# ============================================================
# MQL中间层服务
# 功能：定义结构化指标查询语言，实现语义解析和SQL生成的解耦
# V5.0新增
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

    类似于：
    {
        "metric": "GMV成交总额",
        "dimensions": ["下单时间", "店铺类型"],
        "filters": {"订单状态": "已支付"},
        "time_range": {"start": "2024-01-01", "end": "2024-12-31"},
        "granularity": "month"
    }
    """
    metric: str
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
        metrics = parsed_result.get('metrics', [])
        dimensions = parsed_result.get('dimensions', [])
        filters = parsed_result.get('filters', {})
        time_range = parsed_result.get('time_range')

        granularity = self._infer_granularity(question, dimensions)

        if not metrics and not dimensions:
            raise ValueError("未识别到有效指标或维度")

        return MQLQuery(
            metric=metrics[0] if metrics else None,
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

        if not mql.metric and not mql.dimensions:
            errors.append("MQL缺少metric和dimensions")
            return {"valid": False, "errors": errors, "warnings": warnings}

        if mql.metric:
            metric_info = self.semantic_layer.get_metric_by_name(mql.metric)
            if not metric_info:
                errors.append(f"指标 '{mql.metric}' 不存在")
                return {"valid": False, "errors": errors, "warnings": warnings}

            if mql.granularity and metric_info.stat_period:
                if mql.granularity not in metric_info.stat_period:
                    warnings.append(
                        f"⚠️ 指标 '{mql.metric}' 推荐粒度: {metric_info.stat_period}，"
                        f"当前请求: {mql.granularity}"
                    )

            if metric_info.is_non_additive and mql.granularity:
                warnings.append(
                    f"⚠️ '{mql.metric}' 是去重类指标(如UV/支付用户数)，"
                    f"跨粒度聚合可能导致数据失真"
                )

        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}

    def apply_business_rules(self, mql: MQLQuery) -> MQLQuery:
        """
        应用业务规则（默认过滤条件）

        Args:
            mql: 原始MQL

        Returns:
            应用规则后的MQL
        """
        if mql.metric:
            default_filters = self.semantic_layer.apply_default_filters([mql.metric])

            for f in default_filters:
                if f and '=' in f:
                    field = f.split('=')[0].strip()
                    value = f.split('=')[1].strip().strip("'\"")
                    if field not in mql.filters:
                        mql.filters[field] = value

            rules = self.semantic_layer.get_business_rules(
                rule_type='filter',
                target_metric=mql.metric
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
            "metric": None,
            "dimensions": [],
            "filters": [],
            "calculation": "",
            "sql": sql
        }

        if mql.metric:
            metric_info = self.semantic_layer.get_metric_by_name(mql.metric)
            if metric_info:
                lineage["metric"] = {
                    "name": metric_info.name,
                    "business_desc": metric_info.business_desc,
                    "aggregation": metric_info.aggregation_type,
                    "physical_table": metric_info.physical_table,
                    "physical_field": metric_info.physical_field,
                    "is_non_additive": metric_info.is_non_additive,
                    "version": metric_info.metric_version
                }
                if metric_info.default_filter:
                    lineage["default_filter"] = metric_info.default_filter
                if metric_info.calculation_formula:
                    lineage["calculation"] = metric_info.calculation_formula

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
