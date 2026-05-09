# ============================================================
# MQL中间层服务
# 功能：定义结构化指标查询语言，实现语义解析和SQL生成的解耦
# V5.3优化：
#   - 支持多指标数组（metrics list），取代单metric字段
#   - 非累加指标跨粒度改为"两步聚合"策略（子查询），不再直接拒绝
# ============================================================

import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class MQLQuery:
    """
    MQL (Metric Query Language) 结构化查询对象

    V5.3升级：支持多指标数组
    {
        "metrics": [
            {"name": "GMV成交总额", "agg": "SUM", "non_additive": false},
            {"name": "订单数", "agg": "COUNT", "non_additive": false}
        ],
        "dimensions": ["下单时间", "店铺类型"],
        "filters": {"订单状态": "已支付"},
        "time_range": {"start": "2024-01-01", "end": "2024-12-31"},
        "granularity": "month"
    }
    """
    metrics: List[Dict[str, Any]]
    dimensions: List[str]
    filters: Dict[str, Any]
    time_range: Optional[Dict[str, str]] = None
    granularity: Optional[str] = None
    limit: int = 1000


@dataclass
class MQLResult:
    """MQL编译结果"""
    sql: str
    explanation: str
    tables_used: List[str]
    lineage: Dict[str, Any]


class MQLService:
    """
    MQL服务：负责将自然语言解析结果转换为结构化MQL

    职责：
    1. 将NLParser输出转换为标准MQL
    2. 校验MQL合法性（指标存在、维度兼容）
    3. 应用默认过滤条件和业务规则
    """

    def __init__(self, semantic_layer_service):
        self.semantic_layer = semantic_layer_service

    def parse_to_mql(
        self,
        parsed_result: Dict[str, Any],
        question: str = None
    ) -> MQLQuery:
        """
        将解析结果转换为MQL

        Args:
            parsed_result: NLParser的输出 {metrics, dimensions, filters, time_range}
            question: 原始问题（用于推断粒度）

        Returns:
            MQLQuery对象
        """
        metric_names = parsed_result.get('metrics', [])
        dimensions = parsed_result.get('dimensions', [])
        filters = parsed_result.get('filters', {})
        time_range = parsed_result.get('time_range')

        granularity = self._infer_granularity(question, dimensions)

        if not metric_names and not dimensions:
            raise ValueError("未识别到有效指标或维度")

        # 构建多指标数组（丰富agg和non_additive信息）
        metrics = []
        for name in metric_names:
            metric_info = self.semantic_layer.get_metric_by_name(name)
            if metric_info:
                metrics.append({
                    "name": name,
                    "agg": metric_info.aggregation_type or 'SUM',
                    "non_additive": metric_info.is_non_additive,
                    "physical_table": metric_info.physical_table,
                    "physical_field": metric_info.physical_field
                })
            else:
                metrics.append({
                    "name": name,
                    "agg": 'SUM',
                    "non_additive": False
                })

        return MQLQuery(
            metrics=metrics,
            dimensions=dimensions,
            filters=filters,
            time_range=time_range,
            granularity=granularity
        )

    def validate_mql(self, mql: MQLQuery) -> Dict[str, Any]:
        """
        校验MQL合法性

        Returns:
            {"valid": bool, "errors": [...], "warnings": [...]}
        """
        errors = []
        warnings = []

        if not mql.metrics and not mql.dimensions:
            errors.append("MQL缺少metrics和dimensions")
            return {"valid": False, "errors": errors, "warnings": warnings}

        # 校验每个指标
        for metric_entry in mql.metrics:
            name = metric_entry['name']
            metric_info = self.semantic_layer.get_metric_by_name(name)
            if not metric_info:
                errors.append(f"指标 '{name}' 不存在")
                continue

            if mql.granularity and metric_info.stat_period:
                allowed_periods = [p.strip() for p in metric_info.stat_period.split(',')]
                if mql.granularity not in allowed_periods:
                    warnings.append(
                        f"⚠️ 指标 '{name}' 推荐粒度: {metric_info.stat_period}，"
                        f"当前请求: {mql.granularity}"
                    )

            # V5.3优化：非累加指标跨粒度->两步聚合策略提示
            if metric_info.is_non_additive and mql.granularity and mql.granularity != 'daily':
                warnings.append(
                    f"ℹ️ '{name}' 是去重类指标，跨粒度({mql.granularity})聚合时"
                    f"请使用两步聚合：内层按天COUNT(DISTINCT)，外层{self._infer_outer_agg(metric_info.aggregation_type)}"
                )

        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}

    def _infer_outer_agg(self, inner_agg: Optional[str]) -> str:
        """推断非累加指标跨粒度时的外层聚合方式"""
        if not inner_agg:
            return 'SUM'
        upper = inner_agg.upper()
        if upper in ('COUNT', 'COUNT(DISTINCT)'):
            return 'SUM'
        return inner_agg

    def apply_business_rules(self, mql: MQLQuery) -> MQLQuery:
        """
        应用业务规则（默认过滤条件）

        Args:
            mql: 原始MQL

        Returns:
            应用规则后的MQL
        """
        metric_names = [m['name'] for m in mql.metrics]

        if metric_names:
            default_filters = self.semantic_layer.apply_default_filters(metric_names)

            for f in default_filters:
                if f and '=' in f:
                    field = f.split('=')[0].strip()
                    value = f.split('=')[1].strip().strip("'\"")
                    if field not in mql.filters:
                        mql.filters[field] = value

            for metric_name in metric_names:
                rules = self.semantic_layer.get_business_rules(
                    rule_type='filter',
                    target_metric=metric_name
                )
                for rule in rules:
                    if rule.rule_content and '=' in rule.rule_content:
                        field = rule.rule_content.split('=')[0].strip()
                        value = rule.rule_content.split('=')[1].strip().strip("'\"")
                        if field not in mql.filters:
                            mql.filters[field] = value

        return mql

    def build_lineage(self, mql: MQLQuery, sql: str) -> Dict[str, Any]:
        """
        构建血缘追溯信息

        Args:
            mql: MQL对象
            sql: 生成的SQL

        Returns:
            血缘信息字典
        """
        lineage = {
            "metrics": [],
            "dimensions": [],
            "filters": [],
            "calculation": "",
            "sql": sql
        }

        for metric_entry in mql.metrics:
            name = metric_entry['name']
            metric_info = self.semantic_layer.get_metric_by_name(name)
            if metric_info:
                entry = {
                    "name": metric_info.name,
                    "business_desc": metric_info.business_desc,
                    "aggregation": metric_info.aggregation_type,
                    "physical_table": metric_info.physical_table,
                    "physical_field": metric_info.physical_field,
                    "is_non_additive": metric_info.is_non_additive,
                    "version": metric_info.metric_version
                }
                if metric_info.default_filter:
                    entry["default_filter"] = metric_info.default_filter
                if metric_info.calculation_formula:
                    lineage["calculation"] = metric_info.calculation_formula
                lineage["metrics"].append(entry)

        for dim in mql.dimensions:
            dim_info = self.semantic_layer.get_metric_by_name(dim)
            if dim_info:
                lineage["dimensions"].append({
                    "name": dim_info.name,
                    "physical_table": dim_info.physical_table,
                    "physical_field": dim_info.physical_field
                })

        for field, value in mql.filters.items():
            lineage["filters"].append({
                "field": field,
                "value": value
            })

        return lineage

    def _infer_granularity(self, question: str, dimensions: List[str]) -> Optional[str]:
        """从问题中推断粒度"""
        if not question:
            return None

        question = question.lower()

        granularity_map = {
            '年': 'year', '按年': 'year', '年度': 'year', '每年': 'year',
            '季': 'quarter', '按季': 'quarter', '季度': 'quarter', '每季度': 'quarter',
            '月': 'month', '按月': 'month', '月度': 'month', '每月': 'month',
            '周': 'week', '按周': 'week', '每周': 'week',
            '日': 'daily', '按日': 'daily', '天': 'daily', '每天': 'daily',
            '实时': 'real_time'
        }

        for keyword, granularity in granularity_map.items():
            if keyword in question:
                return granularity

        for dim in dimensions:
            dim_lower = dim.lower()
            if '时间' in dim or '日期' in dim or dim_lower in ('time', 'date', 'datetime'):
                if '年' in question:
                    return 'year'
                if '季' in question:
                    return 'quarter'
                if '月' in question:
                    return 'month'
                if '周' in question:
                    return 'week'
                if '日' in question or '天' in question:
                    return 'daily'

        return None

    def to_dict(self, mql: MQLQuery) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(mql)