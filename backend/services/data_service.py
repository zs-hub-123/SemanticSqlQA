# ============================================================
# 第四层：数据服务层
# 功能：
#   1. 表结构服务（从语义层/本地获取，V5.2优化：移除Milvus）
#   2. SQL生成器（大模型调用②，强制MQL约束）
#   3. SQL白名单校验
#   4. 执行引擎 + 中文表头美化
# V5.2更新：
#   - 移除Milvus向量库依赖（冗余）
#   - 强化MQL控制SQL生成（业务规则强制注入）
#   - 非累加指标跨粒度拦截
# ============================================================

import json
import logging
import re
from typing import Dict, Any, List, Optional, Set

import requests

from backend.core.config import config
from backend.core.exceptions import (
    SQLValidationError,
    APIError
)

logger = logging.getLogger(__name__)


class TableSchemaService:
    """
    表结构服务
    
    V5.2优化：替代MilvusService，直接从语义层或本地预定义获取表结构
    更轻量、更快、无外部依赖
    """

    def __init__(self):
        pass

    def get_table_schemas(self, table_names: List[str]) -> Dict[str, Any]:
        """
        获取表结构
        
        Args:
            table_names: 需要查询的表名列表
            
        Returns:
            {table_name: {fields: [...], description: "..."}}
        """
        result = {}
        
        for table_name in table_names:
            result[table_name] = {
                "table_name": table_name,
                "fields": self._get_table_fields(table_name),
                "description": f"{table_name}表"
            }
        
        logger.info(f"获取 {len(result)} 个表的结构")
        return result

    @staticmethod
    def _get_table_fields(table_name: str) -> List[Dict]:
        """返回15张业务表的完整字段结构"""
        mock_data = {
            "users": [
                {"name": "user_id", "type": "BIGINT", "desc": "用户ID"},
                {"name": "username", "type": "VARCHAR(64)", "desc": "用户名"},
                {"name": "nickname", "type": "VARCHAR(64)", "desc": "用户昵称"},
                {"name": "gender", "type": "ENUM('M','F','U')", "desc": "性别"},
                {"name": "register_time", "type": "DATETIME", "desc": "注册时间"},
                {"name": "user_level", "type": "ENUM('1','2','3','4','5')", "desc": "用户等级"},
                {"name": "balance", "type": "DECIMAL(12,2)", "desc": "账户余额"},
                {"name": "points", "type": "INT", "desc": "积分"},
                {"name": "status", "type": "ENUM('active','inactive','banned')", "desc": "账户状态"}
            ],
            "user_addresses": [
                {"name": "address_id", "type": "BIGINT", "desc": "地址ID"},
                {"name": "user_id", "type": "BIGINT", "desc": "用户ID"},
                {"name": "province", "type": "VARCHAR(32)", "desc": "省份"},
                {"name": "city", "type": "VARCHAR(32)", "desc": "城市"},
                {"name": "detail_address", "type": "VARCHAR(255)", "desc": "详细地址"},
                {"name": "receiver_name", "type": "VARCHAR(64)", "desc": "收货人姓名"},
                {"name": "receiver_phone", "type": "VARCHAR(20)", "desc": "收货人手机号"}
            ],
            "categories": [
                {"name": "category_id", "type": "BIGINT", "desc": "分类ID"},
                {"name": "category_name", "type": "VARCHAR(64)", "desc": "分类名称"},
                {"name": "parent_id", "type": "BIGINT", "desc": "父分类ID"},
                {"name": "level", "type": "TINYINT", "desc": "分类层级"},
                {"name": "is_visible", "type": "TINYINT", "desc": "是否可见"}
            ],
            "products": [
                {"name": "product_id", "type": "BIGINT", "desc": "商品ID"},
                {"name": "product_name", "type": "VARCHAR(128)", "desc": "商品名称"},
                {"name": "category_id", "type": "BIGINT", "desc": "分类ID"},
                {"name": "store_id", "type": "BIGINT", "desc": "店铺ID"},
                {"name": "brand", "type": "VARCHAR(64)", "desc": "品牌"},
                {"name": "price", "type": "DECIMAL(10,2)", "desc": "售价"},
                {"name": "stock", "type": "INT", "desc": "库存数量"},
                {"name": "sales", "type": "INT", "desc": "销量"},
                {"name": "rating_score", "type": "DECIMAL(2,1)", "desc": "商品评分"},
                {"name": "status", "type": "ENUM('on_sale','off_sale','pre_sale')", "desc": "商品状态"}
            ],
            "product_specs": [
                {"name": "spec_id", "type": "BIGINT", "desc": "规格ID"},
                {"name": "product_id", "type": "BIGINT", "desc": "商品ID"},
                {"name": "spec_name", "type": "VARCHAR(64)", "desc": "规格名称"},
                {"name": "spec_value", "type": "VARCHAR(128)", "desc": "规格值"},
                {"name": "sku_code", "type": "VARCHAR(64)", "desc": "SKU编码"},
                {"name": "price", "type": "DECIMAL(10,2)", "desc": "SKU售价"},
                {"name": "stock", "type": "INT", "desc": "SKU库存"}
            ],
            "stores": [
                {"name": "store_id", "type": "BIGINT", "desc": "店铺ID"},
                {"name": "store_name", "type": "VARCHAR(128)", "desc": "店铺名称"},
                {"name": "store_type", "type": "ENUM('flagship','specialty','franchise','personal')", "desc": "店铺类型"},
                {"name": "owner_id", "type": "BIGINT", "desc": "店主用户ID"},
                {"name": "province", "type": "VARCHAR(32)", "desc": "省份"},
                {"name": "city", "type": "VARCHAR(32)", "desc": "城市"},
                {"name": "total_sales", "type": "INT", "desc": "总销量"},
                {"name": "total_followers", "type": "INT", "desc": "总粉丝数"},
                {"name": "status", "type": "ENUM('open','closed','frozen','reviewing')", "desc": "店铺状态"}
            ],
            "store_ratings": [
                {"name": "rating_id", "type": "BIGINT", "desc": "评分ID"},
                {"name": "order_id", "type": "BIGINT", "desc": "订单ID"},
                {"name": "user_id", "type": "BIGINT", "desc": "用户ID"},
                {"name": "store_id", "type": "BIGINT", "desc": "店铺ID"},
                {"name": "description_score", "type": "DECIMAL(2,1)", "desc": "描述相符评分"},
                {"name": "service_score", "type": "DECIMAL(2,1)", "desc": "服务态度评分"},
                {"name": "logistics_score", "type": "DECIMAL(2,1)", "desc": "物流服务评分"}
            ],
            "orders": [
                {"name": "order_id", "type": "BIGINT", "desc": "订单ID"},
                {"name": "order_no", "type": "VARCHAR(32)", "desc": "订单编号"},
                {"name": "user_id", "type": "BIGINT", "desc": "下单用户ID"},
                {"name": "store_id", "type": "BIGINT", "desc": "店铺ID"},
                {"name": "total_amount", "type": "DECIMAL(12,2)", "desc": "订单总金额"},
                {"name": "discount_amount", "type": "DECIMAL(12,2)", "desc": "优惠金额"},
                {"name": "pay_amount", "type": "DECIMAL(12,2)", "desc": "实付金额"},
                {"name": "order_status", "type": "ENUM('pending','paid','shipped','received','cancelled','refunding','refunded')", "desc": "订单状态"},
                {"name": "payment_method", "type": "ENUM('alipay','wechat','bank_card','balance','installment')", "desc": "支付方式"},
                {"name": "shipping_fee", "type": "DECIMAL(10,2)", "desc": "运费"},
                {"name": "create_time", "type": "DATETIME", "desc": "下单时间"},
                {"name": "pay_time", "type": "DATETIME", "desc": "支付时间"},
                {"name": "ship_time", "type": "DATETIME", "desc": "发货时间"},
                {"name": "receive_time", "type": "DATETIME", "desc": "收货时间"}
            ],
            "order_items": [
                {"name": "item_id", "type": "BIGINT", "desc": "明细ID"},
                {"name": "order_id", "type": "BIGINT", "desc": "订单ID"},
                {"name": "product_id", "type": "BIGINT", "desc": "商品ID"},
                {"name": "product_name", "type": "VARCHAR(128)", "desc": "商品名称"},
                {"name": "price", "type": "DECIMAL(10,2)", "desc": "单价"},
                {"name": "quantity", "type": "INT", "desc": "数量"},
                {"name": "subtotal", "type": "DECIMAL(12,2)", "desc": "小计"},
                {"name": "refund_status", "type": "ENUM('none','applied','approved','rejected')", "desc": "退款状态"},
                {"name": "refund_amount", "type": "DECIMAL(10,2)", "desc": "退款金额"}
            ],
            "payments": [
                {"name": "payment_id", "type": "BIGINT", "desc": "支付ID"},
                {"name": "order_id", "type": "BIGINT", "desc": "订单ID"},
                {"name": "payment_no", "type": "VARCHAR(64)", "desc": "支付流水号"},
                {"name": "payment_method", "type": "ENUM('alipay','wechat','bank_card','balance')", "desc": "支付方式"},
                {"name": "amount", "type": "DECIMAL(12,2)", "desc": "支付金额"},
                {"name": "status", "type": "ENUM('pending','success','failed')", "desc": "支付状态"},
                {"name": "pay_time", "type": "DATETIME", "desc": "支付时间"}
            ],
            "coupons": [
                {"name": "coupon_id", "type": "BIGINT", "desc": "优惠券ID"},
                {"name": "coupon_name", "type": "VARCHAR(128)", "desc": "优惠券名称"},
                {"name": "coupon_type", "type": "ENUM('fixed','percent','shipping')", "desc": "券类型"},
                {"name": "coupon_value", "type": "DECIMAL(10,2)", "desc": "优惠券值"},
                {"name": "min_amount", "type": "DECIMAL(10,2)", "desc": "最低消费金额"},
                {"name": "total_count", "type": "INT", "desc": "发放总量"},
                {"name": "received_count", "type": "INT", "desc": "已领取数量"},
                {"name": "used_count", "type": "INT", "desc": "已使用数量"},
                {"name": "status", "type": "ENUM('draft','active','expired','disabled')", "desc": "券状态"}
            ],
            "campaigns": [
                {"name": "campaign_id", "type": "BIGINT", "desc": "活动ID"},
                {"name": "campaign_name", "type": "VARCHAR(128)", "desc": "活动名称"},
                {"name": "campaign_type", "type": "ENUM('flash_sale','group_buy','full_reduction','gift','lottery')", "desc": "活动类型"},
                {"name": "store_id", "type": "BIGINT", "desc": "店铺ID"},
                {"name": "budget", "type": "DECIMAL(12,2)", "desc": "活动预算"},
                {"name": "actual_gmv", "type": "DECIMAL(12,2)", "desc": "活动实际GMV"},
                {"name": "cost", "type": "DECIMAL(12,2)", "desc": "活动成本"},
                {"name": "status", "type": "ENUM('planned','active','ended','cancelled')", "desc": "活动状态"}
            ],
            "user_coupons": [
                {"name": "id", "type": "BIGINT", "desc": "记录ID"},
                {"name": "user_id", "type": "BIGINT", "desc": "用户ID"},
                {"name": "coupon_id", "type": "BIGINT", "desc": "优惠券ID"},
                {"name": "order_id", "type": "BIGINT", "desc": "使用的订单ID"},
                {"name": "status", "type": "ENUM('unused','used','expired')", "desc": "状态"},
                {"name": "receive_time", "type": "DATETIME", "desc": "领取时间"},
                {"name": "use_time", "type": "DATETIME", "desc": "使用时间"}
            ],
            "shipments": [
                {"name": "shipment_id", "type": "BIGINT", "desc": "物流单ID"},
                {"name": "order_id", "type": "BIGINT", "desc": "订单ID"},
                {"name": "store_id", "type": "BIGINT", "desc": "店铺ID"},
                {"name": "shipment_no", "type": "VARCHAR(64)", "desc": "物流单号"},
                {"name": "carrier", "type": "ENUM('sf','yd','zt','sto','yt','ems','jd')", "desc": "快递公司"},
                {"name": "status", "type": "ENUM('pending','picked_up','in_transit','delivered','failed','returned')", "desc": "物流状态"},
                {"name": "ship_time", "type": "DATETIME", "desc": "发货时间"},
                {"name": "deliver_time", "type": "DATETIME", "desc": "签收时间"},
                {"name": "weight", "type": "DECIMAL(8,2)", "desc": "包裹重量"}
            ],
            "shipment_tracks": [
                {"name": "track_id", "type": "BIGINT", "desc": "轨迹ID"},
                {"name": "shipment_id", "type": "BIGINT", "desc": "物流单ID"},
                {"name": "location", "type": "VARCHAR(128)", "desc": "当前位置"},
                {"name": "status", "type": "VARCHAR(64)", "desc": "状态描述"},
                {"name": "track_time", "type": "DATETIME", "desc": "轨迹时间"}
            ]
        }
        return mock_data.get(table_name, [])


class SQLValidator:
    """
    SQL白名单校验器
    
    职责：校验SQL中使用的表和字段是否在白名单内
    兜底防止大模型幻觉编造不存在的表/字段
    """

    def __init__(self, allowed_tables: Set[str], allowed_fields: Dict[str, Set[str]]):
        """
        Args:
            allowed_tables: 允许的表名集合
            allowed_fields: {表名: 允许的字段名集合}
        """
        self.allowed_tables = allowed_tables
        self.allowed_fields = allowed_fields

    def validate(self, sql: str) -> Dict[str, Any]:
        """
        校验SQL合法性
        
        Returns:
            {"valid": bool, "errors": [...], "tables_used": [...]}
        """
        errors = []
        tables_in_sql = self._extract_tables(sql)
        fields_in_sql = self._extract_fields(sql)
        
        for table in tables_in_sql:
            if table not in self.allowed_tables:
                errors.append(f"非法表名: {table} (不在白名单中)")
        
        for table, field in fields_in_sql:
            if table in self.allowed_fields:
                if field not in self.allowed_fields[table]:
                    errors.append(f"非法字段: {table}.{field}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "tables_used": list(tables_in_sql),
            "fields_used": fields_in_sql
        }

    @staticmethod
    def _extract_tables(sql: str) -> Set[str]:
        """提取SQL中的表名"""
        patterns = [r'FROM\s+`?(\w+)`?', r'JOIN\s+`?(\w+)`?', r'INTO\s+`?(\w+)`?']
        tables = set()
        for p in patterns:
            matches = re.findall(p, sql, re.IGNORECASE)
            tables.update(matches)
        return tables

    @staticmethod
    def _extract_fields(sql: str) -> List[tuple]:
        """提取SQL中的字段名（带表前缀的优先）"""
        results = []
        matches = re.findall(r'`?(\w+)`?\.`?(\w+)`?', sql)
        results.extend(matches)
        return results


class SQLGenerator:
    """
    SQL生成器（大模型调用②）
    
    V5.2优化：强化MQL控制，业务规则强制注入提示词
    大模型必须遵守MQL规则生成SQL
    """

    SYSTEM_PROMPT = """你是专业的MySQL SQL生成专家。

## 可用的表结构和字段
{table_schemas}

## 表之间的JOIN关系
{join_relations}

## 标准指标说明
{metrics_info}

## MQL约束条件（必须严格遵守）⭐
{mql_constraints}

## 业务规则（必须应用）⭐
{business_rules}

## 严格规则
1. **只能使用上面列出的表和字段**，禁止编造任何不存在的表名或字段名
2. 多表查询必须使用提供的JOIN条件，禁止自己猜测关联方式
3. 只生成SELECT语句，禁止INSERT/UPDATE/DELETE
4. 字段名使用反引号包裹，如 `users`.`user_id`
5. 结果集使用中文别名，便于展示
6. WHERE条件的枚举值必须使用英文值（如 'active' 而非 '正常'）
7. **必须应用所有MQL约束条件和业务规则**，这是强制的


## 输出格式
严格返回JSON：
```json
{{
    "sql": "SELECT ...",
    "explanation": "中文说明",
    "tables_used": ["表1", "表2"]
}}
<!-- JSON_END -->
"""

    def __init__(self):
        self.use_backup = config.use_backup_model
        if self.use_backup:
            self.api_key = config.backup_api_key
            self.api_url = config.backup_api_base_url
            self.model = config.backup_model_name
        else:
            self.api_key = config.api_key
            self.api_url = config.api_base_url
            self.model = config.model_name

    def switch_model(self, use_backup: bool = None):
        """切换使用的模型"""
        if use_backup is not None:
            self.use_backup = use_backup
        else:
            self.use_backup = not self.use_backup

        if self.use_backup:
            self.api_key = config.backup_api_key
            self.api_url = config.backup_api_base_url
            self.model = config.backup_model_name
        else:
            self.api_key = config.api_key
            self.api_url = config.api_base_url
            self.model = config.model_name

    def generate(
        self,
        question: str,
        parsed_result: Dict[str, Any],
        table_schemas: Dict[str, Any],
        relations: List[Any],
        metrics_info: List[str],
        mql_constraints: str = "",
        business_rules: List[str] = None
    ) -> Dict[str, Any]:
        """
        生成SQL（V5.2强化版）
        
        Args:
            question: 原始问题
            parsed_result: 第一步解析的结构化结果
            table_schemas: 候选表的完整结构
            relations: 表关联关系
            metrics_info: 涉及的指标说明
            mql_constraints: MQL约束条件文本
            business_rules: 业务规则列表
            
        Returns:
            {"sql": "...", "explanation": "...", "tables_used": [...]}
        """
        schemas_text = self._format_schemas(table_schemas)
        relations_text = self._format_relations(relations)
        metrics_text = '\n'.join([f"- {m}" for m in metrics_info])
        
        rules_text = ""
        if business_rules:
            rules_text = "\n".join([f"- ⚠️ {r}" for r in business_rules])
        else:
            rules_text = "- 无特殊业务规则"

        user_prompt = f"""请为以下问题生成SQL:

**原始问题**: {question}

**识别到的指标**: {parsed_result.get('metrics', [])}
**识别到的维度**: {parsed_result.get('dimensions', [])}
**筛选条件**: {parsed_result.get('filters', {})}"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT.format(
                table_schemas=schemas_text,
                join_relations=relations_text,
                metrics_info=metrics_text,
                mql_constraints=mql_constraints or "- 无特殊MQL约束",
                business_rules=rules_text
            )},
            {"role": "user", "content": user_prompt}
        ]
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0,
            "max_tokens": 2048,
            "enable_thinking": False
        }
        
        try:
            response = requests.post(
                f"{self.api_url}/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                },
                json=payload,
                timeout=config.api_timeout
            )
            response.raise_for_status()
            
            content = response.json()['choices'][0]['message']['content']
            result = self._parse_response(content)
            
            logger.info(f"SQL生成完成 | 表:{result.get('tables_used', [])}")
            return result
            
        except Exception as e:
            logger.error(f"SQL生成失败: {str(e)}")
            raise APIError(f"SQL生成失败: {str(e)}")

    @staticmethod
    def _format_schemas(schemas: Dict) -> str:
        """格式化表结构"""
        lines = []
        for table_name, info in schemas.items():
            lines.append(f"\n### 表: {table_name}")
            lines.append(f"说明: {info.get('description', '')}")
            lines.append("字段:")
            for field in info.get('fields', []):
                lines.append(f"  - `{field['name']}` ({field['type']}): {field['desc']}")
        return '\n'.join(lines)

    @staticmethod
    def _format_relations(relations: List) -> str:
        """格式化关联关系"""
        if not relations:
            return "无直接关联"
        lines = []
        for rel in relations:
            lines.append(f"- {rel.main_table} {rel.join_type} JOIN {rel.related_table} ON {rel.join_condition}")
        return '\n'.join(lines)

    @staticmethod
    def _parse_response(content: str) -> Dict:
        """解析响应"""
        match = re.search(r'\{[\s\S]*\}', content)
        if match:
            try:
                return json.loads(match.group())
            except:
                pass
        return {"sql": "", "explanation": content[:200], "tables_used": []}


class QueryExecutor:
    """
    查询执行器 + 中文表头美化
    """

    def __init__(self, db_connection):
        self.db = db_connection
        self.field_aliases = {}

    def execute(self, sql: str) -> Dict[str, Any]:
        """
        执行SQL并美化结果

        Returns:
            {"success": bool, "columns": [], "rows": [], "error": str}
        """
        try:
            rows = self.db.execute_query(sql)
            if isinstance(rows, list):
                if rows:
                    columns = list(rows[0].keys()) if rows else []
                    beautified = self._beautify_columns({"columns": columns, "rows": rows})
                    return beautified
                else:
                    return {"success": True, "columns": [], "rows": [], "row_count": 0}
            return {"success": True, "columns": [], "rows": rows}
        except Exception as e:
            logger.error(f"SQL执行失败: {str(e)}")
            return {"success": False, "error": str(e), "columns": [], "rows": []}

    def _beautify_columns(self, result: Dict) -> Dict:
        """将英文列名替换为中文"""
        columns = result.get('columns', [])
        rows = result.get('rows', [])
        
        new_columns = []
        alias_map = {}
        
        for col in columns:
            if col.startswith("'") or ' AS ' in col.upper():
                clean_col = col.split(' AS ')[-1].strip().strip("'`")
                new_columns.append(clean_col)
            else:
                new_columns.append(col)
            alias_map[col] = new_columns[-1]
        
        return {
            "success": True,
            "columns": new_columns,
            "rows": rows,
            "row_count": len(rows),
            "alias_map": alias_map
        }
