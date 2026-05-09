# ============================================================
# 数据库连接管理
# 支持双数据源：业务库 + 语义层库
# ============================================================

import mysql.connector
from mysql.connector import Error
from typing import Dict, Any, Optional, List
import logging

from backend.core.config import config

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """数据库连接封装"""

    def __init__(self, db_config: Dict):
        self.config = db_config
        self._conn = None

    def connect(self) -> bool:
        try:
            self._conn = mysql.connector.connect(**self.config)
            return True
        except Error as e:
            logger.error(f"数据库连接失败: {e}")
            return False

    def ensure_connected(self) -> bool:
        if not self._conn or not self._conn.is_connected():
            return self.connect()
        return True

    def execute_query(self, sql: str, params=None) -> List[Dict]:
        """执行查询，返回字典列表"""
        if not self.ensure_connected():
            raise Exception("数据库未连接")

        cursor = self._conn.cursor(dictionary=True)
        try:
            cursor.execute(sql, params or ())
            if cursor.description:
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                result = []
                for row in rows:
                    d = dict(zip(columns, row.values()) if hasattr(row, 'values') else dict(row))
                    for k, v in d.items():
                        if hasattr(v, 'isoformat'):
                            d[k] = str(v)
                        elif hasattr(v, '__float__'):
                            d[k] = float(v)
                    result.append(d)
                return result
            return []
        finally:
            cursor.close()

    def execute(self, sql: str, params=None) -> int:
        """执行写操作"""
        if not self.ensure_connected():
            raise Exception("数据库未连接")
        
        cursor = self._conn.cursor()
        try:
            cursor.execute(sql, params or ())
            self._conn.commit()
            return cursor.rowcount
        finally:
            cursor.close()

    def close(self):
        if self._conn and self._conn.is_connected():
            self._conn.close()


class DualDatabaseManager:
    """双数据库管理器"""

    def __init__(self):
        self.business_db = DatabaseConnection(config.business_db_config)
        self.semantic_db = DatabaseConnection(config.semantic_db_config)

    def init(self):
        """初始化两个数据库连接"""
        logger.info("初始化业务数据库...")
        self.business_db.connect()
        logger.info("初始化语义层数据库...")
        self.semantic_db.connect()

    def close(self):
        self.business_db.close()
        self.semantic_db.close()


# 全局实例
db_manager = DualDatabaseManager()
