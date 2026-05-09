# ============================================================
# SQL智能问答系统 - 核心配置模块
# V5.2更新：移除Milvus向量库配置（已下线）
# 支持多数据源：业务库 + 语义层库
# ============================================================

import os
from pathlib import Path
from typing import Optional, Dict
from dotenv import load_dotenv


class Config:
    """统一配置管理器（单例）"""
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._load_env()
            self._initialized = True

    def _load_env(self):
        env_path = Path(__file__).parent.parent.parent / '.env'
        if env_path.exists():
            load_dotenv(env_path, override=True)

    @property
    def api_key(self) -> str:
        key = os.getenv('API_KEY', '')
        if not key:
            raise ValueError("API_KEY未配置")
        return key

    @property
    def api_base_url(self) -> str:
        return os.getenv('API_BASE_URL', '').rstrip('/')

    @property
    def model_name(self) -> str:
        return os.getenv('MODEL_NAME', 'Qwen3-235B-A22B')

    @property
    def api_timeout(self) -> int:
        return int(os.getenv('API_TIMEOUT', '180'))

    # ========== 多模型支持 ==========
    @property
    def backup_api_key(self) -> str:
        return os.getenv('BACKUP_API_KEY', '')

    @property
    def backup_api_base_url(self) -> str:
        return os.getenv('BACKUP_API_BASE_URL', '').rstrip('/')

    @property
    def backup_model_name(self) -> str:
        return os.getenv('BACKUP_MODEL_NAME', 'Qwen3-32B-FP8')

    @property
    def use_backup_model(self) -> bool:
        return os.getenv('USE_BACKUP_MODEL', 'false').lower() == 'true'

    # ========== 业务数据库 ==========
    @property
    def business_db_config(self) -> Dict:
        return {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', '3306')),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'text02'),
            'charset': 'utf8mb4'
        }

    # ========== 语义层数据库 ==========
    @property
    def semantic_db_config(self) -> Dict:
        return {
            'host': os.getenv('SEMANTIC_DB_HOST', 'localhost'),
            'port': int(os.getenv('SEMANTIC_DB_PORT', '3306')),
            'user': os.getenv('SEMANTIC_DB_USER', 'root'),
            'password': os.getenv('SEMANTIC_DB_PASSWORD', ''),
            'database': os.getenv('SEMANTIC_DB_NAME', 'text02_semantic'),
            'charset': 'utf8mb4'
        }

    # ========== 服务配置 ==========
    @property
    def service_host(self) -> str:
        return os.getenv('SERVICE_HOST', '0.0.0.0')

    @property
    def service_port(self) -> int:
        return int(os.getenv('SERVICE_PORT', '8002'))


config = Config()
