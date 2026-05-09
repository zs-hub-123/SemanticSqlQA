# ============================================================
# 核心业务流程编排器
# 串联四层架构，实现完整问答闭环
# V5.3优化：
#   - 支持多指标MQL（metrics数组）
#   - 候选表扩展：包含维度/过滤条件来源表
#   - BFS加权路径选择
#   - SQL生成后Self-Reflection自检
#   - 失败自动重试机制
# ============================================================

import time
import logging
from typing import Dict, Any, List, Set

from backend.services.nl_parser import NLParser
from backend.services.semantic_layer import SemanticLayerService
from backend.services.mql_service import MQLService
from backend.services.data_service import (
    TableSchemaService,
    SQLGenerator,
    SQLValidator,
    QueryExecutor
)
from backend.core.exceptions import Text2SQLError

logger = logging.getLogger(__name__)


class QAPipeline:
    """
    问答主流程编排器

    V5.3优化后完整流程（2次大模型调用 + 自检）：

    用户问题
      ↓ [第一层：接入层]
    ① 调用NLParser（大模型①）→ 标准指标/维度/筛选条件
      ↓ [第二层：智能解析层完成]
    ② MQL中间层 → 结构化MQL（多指标数组）+ 校验（非累加指标两步聚合提示）
      ↓ [新增：MQL层]
    ③ 查语义层 → 候选表集合（含维度/过滤条件来源表）+ 表关联关系（BFS加权）
      ↓ [第三层：语义层]
    ④ TableSchemaService → 候选表完整结构（含主键/外键标记）
      ↓ [第四层：数据服务层-结构]
    ⑤ 调用SQLGenerator（大模型②）→ 强约束型SQL（多指标+外键+业务规则）
    ⑥ Self-Reflection自检 → 确保业务规则和MQL约束被遵守
    ⑦ SQL白名单校验 → 拦截非法表/字段
    ⑧ 失败重试 → 最多重试2次
    ⑨ 血缘追溯 → 构建口径说明
    ⑩ 执行SQL + 中文表头美化
      ↓ [第四层：数据服务层-执行]
    返回结果给用户
    """

    MAX_JOIN_DEPTH = 3
    MAX_RETRY_COUNT = 2

    def __init__(self, semantic_db, business_db):
        """
        Args:
            semantic_db: 语义层数据库连接
            business_db: 业务数据库连接
        """
        self.semantic_layer = SemanticLayerService(semantic_db)
        self.nl_parser = NLParser()
        self.mql_service = MQLService(self.semantic_layer)
        self.table_schema = TableSchemaService()
        self.sql_generator = SQLGenerator()
        self.query_executor = QueryExecutor(business_db)

    def process(self, question: str) -> Dict[str, Any]:
        """
        处理用户问题的完整流程

        Args:
            question: 自然语言问句

        Returns:
            结果字典
        """
        start_time = time.time()

        try:
            # ========== 第1步：获取标准词汇表 ==========
            logger.info(f"[步骤1] 开始处理问题: {question[:50]}...")
            all_metrics = self.semantic_layer.get_all_metrics()
            all_dimensions = self.semantic_layer.get_all_dimensions()

            metrics_names = [m.name for m in all_metrics]
            dimensions_names = [d.name for d in all_dimensions]
            aliases = self.semantic_layer.get_all_aliases()

            # ========== 第2步：调用大模型① - 口语转标准词 ==========
            logger.info("[步骤2] 调用NLParser (大模型①)...")
            parsed = self.nl_parser.parse(question, metrics_names, dimensions_names, aliases)

            if not parsed.get('metrics') and not parsed.get('dimensions'):
                return {
                    "error": "无法理解您的问题，请尝试使用更标准的业务术语",
                    "elapsed_time": time.time() - start_time,
                    "parse_result": parsed
                }

            # ========== 第2.5步：MQL中间层（强校验） ==========
            logger.info("[步骤2.5] MQL中间层处理...")
            mql = self.mql_service.parse_to_mql(parsed, question)

            # V5.3优化：非累加指标跨粒度预警（不再强硬拒绝）
            mql_validation = self.mql_service.validate_mql(mql)

            # 检查是否有严重错误（非警告）
            if not mql_validation['valid']:
                error_msg = f"MQL校验失败: {'; '.join(mql_validation['errors'])}"
                logger.error(error_msg)
                return {
                    "error": error_msg,
                    "elapsed_time": time.time() - start_time,
                    "parse_result": parsed,
                    "mql_errors": mql_validation['errors']
                }

            # V5.3优化：应用业务规则（多指标支持）
            mql = self.mql_service.apply_business_rules(mql)

            # ========== 第3步：查语义层 - 候选表筛选（含维度表） ==========
            logger.info("[步骤3] 查询语义层，筛选候选表...")
            metric_names = [m['name'] for m in mql.metrics]
            # V5.3优化：候选表不仅包含指标表，还包含维度和过滤条件来源表
            parsed_dimensions = parsed.get('dimensions', [])
            parsed_filters = list(parsed.get('filters', {}).keys())
            all_terms = metric_names + parsed_dimensions + parsed_filters

            candidate_tables = self.semantic_layer.find_candidate_tables(
                metric_names,
                parsed_dimensions
            )

            if not candidate_tables:
                return {
                    "error": "未找到相关的业务表",
                    "elapsed_time": time.time() - start_time,
                    "parse_result": parsed
                }

            logger.info(f"候选表: {candidate_tables}")

            # ========== 第4步：查表关联关系（BFS加权路径） ==========
            relations = self.semantic_layer.get_table_relations(candidate_tables)
            logger.info(f"关联关系数: {len(relations)}")

            tables_for_schema = set(candidate_tables)
            for rel in relations:
                tables_for_schema.add(rel.main_table)
                tables_for_schema.add(rel.related_table)

            # ========== 第5步：TableSchemaService获取表结构（含主键/外键） ==========
            logger.info("[步骤4] 获取表结构...")
            table_schemas = self.table_schema.get_table_schemas(list(tables_for_schema))

            # ========== 第6步：准备多指标说明 ==========
            metrics_info = []
            for m_name in metric_names:
                matched = [m for m in all_metrics if m.name == m_name]
                if matched:
                    m = matched[0]
                    metrics_info.append(f"{m.name} ({m.business_desc}, 聚合:{m.aggregation_type})")

            # ========== 第7步：构建MQL约束和业务规则（多指标） ==========
            mql_constraints = self._build_mql_constraints(mql, mql_validation)
            business_rules_text = self._build_business_rules_text(metric_names)

            # ========== 第8步：调用大模型② - 生成SQL（带重试） ==========
            logger.info("[步骤5] 调用SQLGenerator (大模型②)...")
            sql_result = self._generate_sql_with_retry(
                question=question,
                parsed_result=parsed,
                table_schemas=table_schemas,
                relations=relations,
                metrics_info=metrics_info,
                mql_constraints=mql_constraints,
                business_rules=business_rules_text
            )

            if not sql_result:
                return {
                    "error": "多次尝试后未能生成有效的SQL",
                    "elapsed_time": time.time() - start_time,
                    "parse_result": parsed
                }

            sql = sql_result.get('sql', '')
            if not sql:
                return {
                    "error": "未能生成有效的SQL",
                    "elapsed_time": time.time() - start_time,
                    "parse_result": parsed
                }

            # ========== 第9步：Self-Reflection自检 ==========
            logger.info("[步骤6] Self-Reflection自检...")
            self_reflection_passed, reflection_notes = self._self_reflection_check(
                sql, mql, mql_validation
            )
            if not self_reflection_passed and self.MAX_RETRY_COUNT > 0:
                logger.warning(f"Self-Reflection未通过，重新生成SQL...")
                sql_result = self._generate_sql_with_retry(
                    question=question,
                    parsed_result=parsed,
                    table_schemas=table_schemas,
                    relations=relations,
                    metrics_info=metrics_info,
                    mql_constraints=mql_constraints,
                    business_rules=business_rules_text,
                    reflection_notes=reflection_notes
                )
                if sql_result:
                    sql = sql_result.get('sql', '')

            if not sql:
                return {
                    "error": "未能生成有效的SQL",
                    "elapsed_time": time.time() - start_time,
                    "parse_result": parsed
                }

            # ========== 第10步：SQL白名单校验 ==========
            logger.info("[步骤7] SQL白名单校验...")

            allowed_tables = set(candidate_tables)
            for rel in relations:
                allowed_tables.add(rel.main_table)
                allowed_tables.add(rel.related_table)

            allowed_fields = {}
            all_tables = allowed_tables | set(table_schemas.keys())
            for table_name in all_tables:
                if table_name in table_schemas:
                    allowed_fields[table_name] = {f['name'] for f in table_schemas.get(table_name, {}).get('fields', [])}

            validator = SQLValidator(allowed_tables, allowed_fields)
            validation = validator.validate(sql)

            if not validation['valid']:
                error_msg = f"SQL校验失败: {'; '.join(validation['errors'])}"
                logger.error(error_msg)
                return {
                    "error": error_msg,
                    "sql": sql,
                    "elapsed_time": time.time() - start_time,
                    "parse_result": parsed
                }

            # ========== 第11步：构建血缘追溯（多指标） ==========
            logger.info("[步骤8] 构建血缘追溯信息...")
            lineage = self.mql_service.build_lineage(mql, sql)

            # ========== 第12步：执行SQL + 美化结果 ==========
            logger.info("[步骤9] 执行SQL查询...")
            query_result = self.query_executor.execute(sql)

            elapsed = time.time() - start_time

            logger.info(f"✅ 流程完成 | 耗时:{elapsed:.2f}s | 行数:{query_result.get('row_count', 0)}")

            return {
                "success": True,
                "sql": sql,
                "explanation": sql_result.get('explanation', ''),
                "tables_used": list(candidate_tables),
                "query_result": {
                    "columns": query_result.get('columns', []),
                    "rows": query_result.get('rows', []),
                    "row_count": query_result.get('row_count', 0)
                },
                "elapsed_time": elapsed,
                "parse_result": parsed,
                "mql": self.mql_service.to_dict(mql),
                "lineage": lineage,
                "validation_warnings": mql_validation.get('warnings', [])
            }

        except Text2SQLError as e:
            logger.error(f"流程异常: {e.message}")
            return {"error": e.message, "code": e.code, "elapsed_time": time.time() - start_time}
        except Exception as e:
            logger.exception("未知错误")
            return {"error": str(e), "elapsed_time": time.time() - start_time}

    def _generate_sql_with_retry(
        self,
        question: str,
        parsed_result: Dict[str, Any],
        table_schemas: Dict[str, Any],
        relations: List[Any],
        metrics_info: List[str],
        mql_constraints: str = "",
        business_rules: List[str] = None,
        reflection_notes: List[str] = None,
    ) -> Dict[str, Any]:
        """带重试的SQL生成"""
        last_error = None

        for attempt in range(1, self.MAX_RETRY_COUNT + 1):
            try:
                result = self.sql_generator.generate(
                    question=question,
                    parsed_result=parsed_result,
                    table_schemas=table_schemas,
                    relations=relations,
                    metrics_info=metrics_info,
                    mql_constraints=mql_constraints,
                    business_rules=business_rules,
                    reflection_notes=reflection_notes
                )

                if result and result.get('sql'):
                    logger.info(f"SQL生成成功 (尝试{attempt})")
                    return result

                last_error = "生成的SQL为空"
            except Exception as e:
                last_error = str(e)
                logger.warning(f"SQL生成失败 (尝试{attempt}/{self.MAX_RETRY_COUNT}): {last_error}")

        logger.error(f"SQL生成已耗尽所有重试次数，最终错误: {last_error}")
        return None

    def _self_reflection_check(
        self,
        sql: str,
        mql,
        mql_validation: Dict[str, Any]
    ) -> tuple:
        """
        Self-Reflection自检：检查MQL约束是否被SQL遵守

        Returns:
            (passed: bool, notes: List[str])
        """
        notes = []
        passed = True
        sql_upper = sql.upper()

        # 检查过滤条件是否都在WHERE中
        for field, value in mql.filters.items():
            if field.lower() not in sql.lower():
                notes.append(f"缺少过滤条件: {field}={value}")
                passed = False

        # 检查维度是否都在GROUP BY中
        if mql.dimensions and 'GROUP BY' in sql_upper:
            for dim in mql.dimensions:
                dim_info = self.semantic_layer.get_metric_by_name(dim)
                if dim_info:
                    physical_field = dim_info.physical_field
                    if physical_field.lower() not in sql.lower():
                        notes.append(f"维度字段未使用: {dim} ({physical_field})")
                        passed = False

        # 检查非累加指标是否使用了COUNT(DISTINCT)
        for metric_entry in mql.metrics:
            if metric_entry.get('non_additive'):
                if 'COUNT(DISTINCT' not in sql_upper:
                    notes.append(f"去重指标 '{metric_entry['name']}' 应使用 COUNT(DISTINCT)")
                    passed = False

        return passed, notes

    def _build_mql_constraints(self, mql, validation_result) -> str:
        """构建MQL约束文本，注入到SQL生成提示词（多指标版）"""
        constraints = []

        # V5.3：多指标数组
        if mql.metrics:
            metric_names = [m['name'] for m in mql.metrics]
            constraints.append(f"- **目标指标**: {', '.join(metric_names)}")
            for m in mql.metrics:
                extra = []
                if m.get('agg'):
                    extra.append(f"聚合方式:{m['agg']}")
                if m.get('non_additive'):
                    extra.append("去重类指标(使用COUNT(DISTINCT))")
                if extra:
                    constraints.append(f"  - {m['name']} ({'; '.join(extra)})")

        if mql.dimensions:
            constraints.append(f"- **分析维度**: {', '.join(mql.dimensions)}")

        if mql.granularity:
            constraints.append(f"- **时间粒度**: {mql.granularity}（必须按此粒度聚合）")

        if mql.filters:
            filter_strs = [f"{k}={v}" for k, v in mql.filters.items()]
            constraints.append(f"- **强制过滤条件**: {' AND '.join(filter_strs)}（必须在WHERE中应用）")

        # 非累加指标警告（V5.3：两步聚合策略）
        warnings = validation_result.get('warnings', [])
        if warnings:
            constraints.append("- ⚠️ **重要警告**:")
            for w in warnings:
                constraints.append(f"  - {w}")

        return '\n'.join(constraints) if constraints else "- 无特殊MQL约束"

    def _build_business_rules_text(self, metric_names: List[str]) -> List[str]:
        """构建业务规则文本列表（多指标版）"""
        if not metric_names:
            return None

        rules = []

        for metric_name in metric_names:
            # 获取默认过滤条件
            default_filter = self.semantic_layer.get_default_filter(metric_name)
            if default_filter:
                rules.append(f"指标'{metric_name}'默认过滤: {default_filter}（必须包含在WHERE中）")

            # 获取业务规则
            biz_rules = self.semantic_layer.get_business_rules(
                rule_type='filter',
                target_metric=metric_name
            )

            for rule in biz_rules:
                if rule.rule_content:
                    rules.append(f"[{rule.rule_name}] {rule.rule_desc or ''}: {rule.rule_content}")

        return rules if rules else None