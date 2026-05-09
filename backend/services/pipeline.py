# ============================================================
# 核心业务流程编排器
# 串联四层架构，实现完整问答闭环
# V5.2优化：
#   - 移除Milvus向量库（使用TableSchemaService替代）
#   - 强化MQL控制SQL生成
#   - 非累加指标跨粒度拦截
#   - 业务规则强制注入SQL生成提示词
# ============================================================

import time
import logging
from typing import Dict, Any, List

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
    
    V5.2优化后完整流程（2次大模型调用）：

    用户问题
      ↓ [第一层：接入层]
    ① 调用NLParser（大模型①）→ 标准指标/维度/筛选条件
      ↓ [第二层：智能解析层完成]
    ② MQL中间层 → 结构化MQL + 强校验（非累加拦截、粒度校验）
      ↓ [新增：MQL层]
    ③ 查语义层 → 候选表集合 + 表关联关系（最大3层深度）
      ↓ [第三层：语义层]
    ④ TableSchemaService → 候选表完整结构（本地获取，无外部依赖）
      ↓ [第四层：数据服务层-结构]
    ⑤ 调用SQLGenerator（大模型②）→ 强约束型SQL（必须遵守MQL）
    ⑥ SQL白名单校验 → 拦截非法表/字段
    ⑦ 血缘追溯 → 构建口径说明
    ⑧ 执行SQL + 中文表头美化
      ↓ [第四层：数据服务层-执行]
    返回结果给用户
    """

    MAX_JOIN_DEPTH = 3

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

            # V5.2强化：非累加指标跨粒度拦截
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

            # V5.2强化：应用业务规则（默认过滤条件）
            mql = self.mql_service.apply_business_rules(mql)

            # ========== 第3步：查语义层 - 候选表筛选 ==========
            logger.info("[步骤3] 查询语义层，筛选候选表...")
            candidate_tables = self.semantic_layer.find_candidate_tables(
                parsed.get('metrics', []),
                parsed.get('dimensions', [])
            )

            if not candidate_tables:
                return {
                    "error": "未找到相关的业务表",
                    "elapsed_time": time.time() - start_time,
                    "parse_result": parsed
                }

            logger.info(f"候选表: {candidate_tables}")

            # ========== 第4步：查表关联关系（限制最大3层深度） ==========
            relations = self.semantic_layer.get_table_relations(candidate_tables)
            logger.info(f"关联关系数: {len(relations)}")

            tables_for_schema = set(candidate_tables)
            for rel in relations:
                tables_for_schema.add(rel.main_table)
                tables_for_schema.add(rel.related_table)

            # ========== 第5步：TableSchemaService获取表结构（替代Milvus） ==========
            logger.info("[步骤4] 获取表结构...")
            table_schemas = self.table_schema.get_table_schemas(list(tables_for_schema))

            # ========== 第6步：准备指标说明 ==========
            involved_metrics = [
                m for m in all_metrics
                if m.name in parsed.get('metrics', []) or
                   m.physical_table in candidate_tables
            ]
            metrics_info = [f"{m.name} ({m.business_desc})" for m in involved_metrics]

            # ========== 第7步：构建MQL约束和业务规则（V5.2强化） ==========
            mql_constraints = self._build_mql_constraints(mql, mql_validation)
            business_rules_text = self._build_business_rules_text(mql.metric)

            # ========== 第8步：调用大模型② - 生成SQL（强约束） ==========
            logger.info("[步骤5] 调用SQLGenerator (大模型②)...")
            result = self.sql_generator.generate(
                question=question,
                parsed_result=parsed,
                table_schemas=table_schemas,
                relations=relations,
                metrics_info=metrics_info,
                mql_constraints=mql_constraints,
                business_rules=business_rules_text
            )

            sql = result.get('sql', '')
            if not sql:
                return {
                    "error": "未能生成有效的SQL",
                    "elapsed_time": time.time() - start_time,
                    "parse_result": parsed
                }

            # ========== 第9步：SQL白名单校验 ==========
            logger.info("[步骤6] SQL白名单校验...")
            
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

            # ========== 第10步：构建血缘追溯 ==========
            logger.info("[步骤7] 构建血缘追溯信息...")
            lineage = self.mql_service.build_lineage(mql, sql)

            # ========== 第11步：执行SQL + 美化结果 ==========
            logger.info("[步骤8] 执行SQL查询...")
            query_result = self.query_executor.execute(sql)

            elapsed = time.time() - start_time

            logger.info(f"✅ 流程完成 | 耗时:{elapsed:.2f}s | 行数:{query_result.get('row_count', 0)}")

            return {
                "success": True,
                "sql": sql,
                "explanation": result.get('explanation', ''),
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

    def _build_mql_constraints(self, mql, validation_result) -> str:
        """构建MQL约束文本，注入到SQL生成提示词"""
        constraints = []

        if mql.metric:
            constraints.append(f"- **目标指标**: {mql.metric}")

        if mql.dimensions:
            constraints.append(f"- **分析维度**: {', '.join(mql.dimensions)}")

        if mql.granularity:
            constraints.append(f"- **时间粒度**: {mql.granularity}（必须按此粒度聚合）")

        if mql.filters:
            filter_strs = [f"{k}={v}" for k, v in mql.filters.items()]
            constraints.append(f"- **强制过滤条件**: {' AND '.join(filter_strs)}（必须在WHERE中应用）")

        # 非累加指标警告
        warnings = validation_result.get('warnings', [])
        if warnings:
            constraints.append("- ⚠️ **重要警告**:")
            for w in warnings:
                constraints.append(f"  - {w}")

        return '\n'.join(constraints) if constraints else "- 无特殊MQL约束"

    def _build_business_rules_text(self, metric_name: str) -> List[str]:
        """构建业务规则文本列表"""
        if not metric_name:
            return None

        rules = []

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
