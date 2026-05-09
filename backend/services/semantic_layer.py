# ============================================================
# 第三层：指标语义层服务
# 功能：查询4张配置表，实现口语→标准词→物理表的映射
# V5.0更新：支持增强指标元数据、业务规则、维度层级
# ============================================================

import logging
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
from datetime import date

from backend.core.exceptions import SemanticError

logger = logging.getLogger(__name__)


@dataclass
class MetricDimension:
    """标准指标/维度（增强版）"""
    name: str
    type: str  # metric/dimension
    physical_table: str
    physical_field: str
    field_type: str
    business_desc: str
    aggregation_type: Optional[str]
    domain: str
    # V5.0新增字段
    is_non_additive: bool = False
    stat_period: Optional[str] = None
    data_granularity: Optional[str] = None
    default_filter: Optional[str] = None
    metric_version: str = 'V1.0'
    effective_date: Optional[date] = None
    deprecate_date: Optional[date] = None
    calculation_formula: Optional[str] = None
    related_metrics: Optional[str] = None


@dataclass
class TableRelation:
    """表关联关系"""
    main_table: str
    related_table: str
    join_condition: str
    join_type: str


@dataclass
class TableMeta:
    """表元信息"""
    table_name: str
    table_cn_name: str
    domain: str
    description: str


@dataclass
class BusinessRule:
    """业务规则"""
    id: int
    rule_name: str
    rule_type: str
    target_metric: Optional[str]
    target_dimension: Optional[str]
    rule_content: str
    rule_desc: Optional[str]
    priority: int
    error_message: Optional[str]
    is_active: int = 1
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class DimensionHierarchy:
    """维度层级"""
    dimension_name: str
    level_name: str
    level_order: int
    physical_table: str
    physical_field: str
    field_format: Optional[str]


class SemanticLayerService:
    """
    语义层核心服务

    职责：
    1. 管理标准指标/维度字典（增强版）
    2. 口语别名映射查询
    3. 候选表筛选
    4. 表关联路径推导（递归）
    5. 业务规则管理
    6. 维度层级管理
    7. 口径校验（防止跨粒度聚合）
    """

    def __init__(self, db_connection):
        self.db = db_connection

    def get_all_metrics(self) -> List[MetricDimension]:
        """获取所有标准指标"""
        sql = "SELECT * FROM standard_metrics_dimensions WHERE type='metric' AND is_active=1"
        rows = self.db.execute_query(sql)
        return [self._row_to_metric(r) for r in rows]

    def get_all_dimensions(self) -> List[MetricDimension]:
        """获取所有标准维度"""
        sql = "SELECT * FROM standard_metrics_dimensions WHERE type='dimension' AND is_active=1"
        rows = self.db.execute_query(sql)
        return [self._row_to_metric(r) for r in rows]

    def get_metric_by_name(self, name: str) -> Optional[MetricDimension]:
        """根据名称获取指标/维度详情"""
        sql = "SELECT * FROM standard_metrics_dimensions WHERE name=%s AND is_active=1"
        rows = self.db.execute_query(sql, (name,))
        return self._row_to_metric(rows[0]) if rows else None

    def get_active_metrics_by_version(self, version: str = None) -> List[MetricDimension]:
        """获取指定版本的生效指标"""
        if version:
            sql = """SELECT * FROM standard_metrics_dimensions
                     WHERE type='metric' AND is_active=1 AND metric_version=%s
                     AND (effective_date IS NULL OR effective_date <= CURDATE())
                     AND (deprecate_date IS NULL OR deprecate_date > CURDATE())"""
            rows = self.db.execute_query(sql, (version,))
        else:
            sql = """SELECT * FROM standard_metrics_dimensions
                     WHERE type='metric' AND is_active=1
                     AND (effective_date IS NULL OR effective_date <= CURDATE())
                     AND (deprecate_date IS NULL OR deprecate_date > CURDATE())"""
            rows = self.db.execute_query(sql)
        return [self._row_to_metric(r) for r in rows]

    def check_non_additive_metric(self, metric_name: str) -> bool:
        """检查指标是否不可二次聚合"""
        sql = """SELECT is_non_additive FROM standard_metrics_dimensions
                 WHERE name=%s AND is_active=1"""
        rows = self.db.execute_query(sql, (metric_name,))
        return rows[0]['is_non_additive'] == 1 if rows else False

    def get_default_filter(self, metric_name: str) -> Optional[str]:
        """获取指标的默认过滤条件"""
        sql = """SELECT default_filter FROM standard_metrics_dimensions
                 WHERE name=%s AND is_active=1"""
        rows = self.db.execute_query(sql, (metric_name,))
        return rows[0]['default_filter'] if rows and rows[0]['default_filter'] else None

    def get_all_aliases(self) -> List[Dict]:
        """获取所有口语别名映射（用于传给大模型）"""
        sql = "SELECT spoken_term, standard_name FROM spoken_aliases WHERE is_active=1"
        rows = self.db.execute_query(sql)
        return [{"spoken": r['spoken_term'], "standard": r['standard_name']} for r in rows]

    def resolve_spoken_term(self, spoken: str) -> Optional[str]:
        """
        解析口语术语 → 标准名称

        Args:
            spoken: 用户输入的口语表达

        Returns:
            标准指标/维度名称，未找到返回None
        """
        sql = """
            SELECT standard_name FROM spoken_aliases
            WHERE spoken_term LIKE %s AND is_active=1
            ORDER BY frequency DESC LIMIT 1
        """
        rows = self.db.execute_query(sql, (f"%{spoken}%",))
        return rows[0]['standard_name'] if rows else None

    def find_candidate_tables(self, metrics: List[str], dimensions: List[str]) -> Set[str]:
        """
        根据指标和维度查找候选表

        Args:
            metrics: 标准指标名列表
            dimensions: 标准维度名列表

        Returns:
            候选表名集合
        """
        all_terms = metrics + dimensions
        if not all_terms:
            return set()

        placeholders = ','.join(['%s'] * len(all_terms))
        sql = f"""
            SELECT DISTINCT physical_table FROM standard_metrics_dimensions
            WHERE name IN ({placeholders}) AND is_active=1
        """
        rows = self.db.execute_query(sql, tuple(all_terms))
        return {r['physical_table'] for r in rows}

    def get_table_relations(self, tables: Set[str]) -> List[TableRelation]:
        """
        获取候选表之间的直接关联关系

        Args:
            tables: 候选表集合

        Returns:
            关系列表
        """
        if not tables:
            return []

        placeholders = ','.join(['%s'] * len(tables))
        
        sql = f"""
            SELECT main_table, related_table, join_condition, join_type
            FROM table_relations
            WHERE is_active=1
            AND (main_table IN ({placeholders}) OR related_table IN ({placeholders}))
        """
        params = tuple(list(tables) * 2)
        rows = self.db.execute_query(sql, params)

        return [TableRelation(**r) for r in rows]

    def find_join_path(self, table1: str, table2: str, max_depth: int = 3) -> Optional[List[TableRelation]]:
        """
        递归查找两张表之间的JOIN路径（V5.2强化：限制最大深度）
        
        只使用直接相邻关系，自动推导多层关联
        默认最大深度为3层（防止性能爆炸和无效JOIN）

        Args:
            table1: 起始表
            table2: 目标表
            max_depth: 最大递归深度（默认3层）

        Returns:
            JOIN路径（有序的关系列表），超深则返回None
        """
        if table1 == table2:
            return []

        visited = {table1}
        path = []

        def _dfs(current: str, target: str, depth: int) -> bool:
            if depth > max_depth:
                return False

            relations = self.get_table_relations({current})

            for rel in relations:
                next_table = rel.related_table if rel.main_table == current else rel.main_table

                if next_table == target:
                    path.append(rel)
                    return True

                if next_table not in visited:
                    visited.add(next_table)
                    if _dfs(next_table, target, depth + 1):
                        path.append(rel)
                        return True

            return False

        if _dfs(table1, table2, 0):
            path.reverse()
            return path
        return None

    def get_table_metadata(self, table_name: str) -> Optional[TableMeta]:
        """获取表的元信息"""
        sql = "SELECT * FROM table_metadata WHERE table_name=%s AND is_active=1"
        rows = self.db.execute_query(sql, (table_name,))
        return TableMeta(**rows[0]) if rows else None

    def get_all_aliases_for_standard(self, standard_name: str) -> List[str]:
        """获取某个标准词的所有别名"""
        sql = "SELECT spoken_term FROM spoken_aliases WHERE standard_name=%s AND is_active=1"
        rows = self.db.execute_query(sql, (standard_name,))
        return [r['spoken_term'] for r in rows]

    def get_business_rules(self, rule_type: str = None, target_metric: str = None) -> List[BusinessRule]:
        """
        获取业务规则

        Args:
            rule_type: 规则类型 filter/calc/conflict/validation
            target_metric: 目标指标名

        Returns:
            规则列表
        """
        sql = "SELECT * FROM business_rules WHERE is_active=1"
        params = []

        if rule_type:
            sql += " AND rule_type=%s"
            params.append(rule_type)
        if target_metric:
            sql += " AND target_metric=%s"
            params.append(target_metric)

        sql += " ORDER BY priority DESC"
        rows = self.db.execute_query(sql, tuple(params) if params else None)
        return [BusinessRule(**r) for r in rows]

    def validate_metric_calculation(self, metric_name: str, granularity: str = None) -> Dict[str, Any]:
        """
        校验指标计算是否合法（V5.2强化版）
        
        新增：
        - 非累加指标跨粒度强拦截（不仅是警告）
        - 粒度合法性校验

        Args:
            metric_name: 指标名
            granularity: 请求的粒度（如"按月"）

        Returns:
            {"valid": bool, "error": str, "errors": [...], "warnings": [...]}
        """
        metric = self.get_metric_by_name(metric_name)
        if not metric:
            return {"valid": False, "error": f"指标 {metric_name} 不存在", "errors": [f"指标 {metric_name} 不存在"], "warnings": []}

        errors = []
        warnings = []

        # V5.2强化：非累加指标跨粒度拦截
        if metric.is_non_additive and granularity:
            if granularity != 'daily':
                errors.append(
                    f"❌ '{metric_name}' 是去重类指标(如UV/支付用户数)，"
                    f"仅支持按天(daily)统计，不支持{granularity}粒度聚合"
                )
        
        # 粒度合法性校验
        if granularity and metric.stat_period:
            allowed_periods = [p.strip() for p in metric.stat_period.split(',')]
            if granularity not in allowed_periods:
                errors.append(
                    f"❌ 指标 '{metric_name}' 仅支持 {metric.stat_period} 粒度，"
                    f"不支持 {granularity}"
                )

        # 非警告信息（用于提示词注入）
        if metric.is_non_additive and (not granularity or granularity == 'daily'):
            warnings.append(
                f"⚠️ '{metric_name}' 是去重类指标(如UV/支付用户数)，"
                f"请使用 COUNT(DISTINCT) 而非 SUM"
            )

        return {
            "valid": len(errors) == 0,
            "error": errors[0] if errors else None,
            "errors": errors,
            "warnings": warnings
        }

    def apply_default_filters(self, metric_names: List[str]) -> List[str]:
        """
        为指标列表应用默认过滤条件

        Args:
            metric_names: 指标名列表

        Returns:
            带WHERE子句的过滤条件列表
        """
        filters = []
        for name in metric_names:
            default_filter = self.get_default_filter(name)
            if default_filter:
                filters.append(default_filter)
        return filters

    def get_dimension_hierarchies(self, dimension_name: str = None) -> List[DimensionHierarchy]:
        """
        获取维度层级信息

        Args:
            dimension_name: 维度名，为空则返回所有

        Returns:
            层级列表
        """
        if dimension_name:
            sql = """SELECT * FROM dimension_hierarchies
                     WHERE dimension_name=%s AND is_active=1
                     ORDER BY level_order"""
            rows = self.db.execute_query(sql, (dimension_name,))
        else:
            sql = """SELECT * FROM dimension_hierarchies
                     WHERE is_active=1
                     ORDER BY dimension_name, level_order"""
            rows = self.db.execute_query(sql)

        return [DimensionHierarchy(
            dimension_name=r['dimension_name'],
            level_name=r['level_name'],
            level_order=r['level_order'],
            physical_table=r['physical_table'],
            physical_field=r['physical_field'],
            field_format=r['field_format']
        ) for r in rows]

    @staticmethod
    def _row_to_metric(row: Dict) -> MetricDimension:
        return MetricDimension(
            name=row['name'],
            type=row['type'],
            physical_table=row['physical_table'],
            physical_field=row['physical_field'],
            field_type=row['field_type'],
            business_desc=row['business_desc'],
            aggregation_type=row.get('aggregation_type'),
            domain=row['domain'],
            is_non_additive=bool(row.get('is_non_additive', 0)),
            stat_period=row.get('stat_period'),
            data_granularity=row.get('data_granularity'),
            default_filter=row.get('default_filter'),
            metric_version=row.get('metric_version', 'V1.0'),
            effective_date=row.get('effective_date'),
            deprecate_date=row.get('deprecate_date'),
            calculation_formula=row.get('calculation_formula'),
            related_metrics=row.get('related_metrics')
        )
