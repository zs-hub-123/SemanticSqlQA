# ============================================================
# SQL智能问答系统 - 启动脚本
# 四层架构：接入层 → 智能解析层 → MQL中间层 → 语义层 → 数据服务层
# V5.2优化：移除Milvus，强化MQL控制
# ============================================================

import sys
import os

# 设置工作目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)

# 强制加载.env文件（最优先）
from dotenv import load_dotenv
load_dotenv(os.path.join(SCRIPT_DIR, '.env'), override=True)

# 打印关键配置
print("=" * 70)
print("  🚀 SQL智能问答系统 (四层架构版 V5.2)")
print("=" * 70)
print()
print("  📍 访问地址:")
print(f"     🌐 前端页面: http://localhost:5173")
print(f"     🔌 后端API:  http://localhost:8002")
print(f"     📚 API文档:  http://localhost:8002/docs")
print()
print("  架构层次:")
print("    Layer1: 接入层     → API接口")
print("    Layer2: 智能解析层 → 口语转标准词 (大模型①)")
print("    Layer2.5: MQL中间层 → 结构化查询+强校验 ★")
print("    Layer3: 语义层     → 指标/维度/表映射")
print("    Layer4: 数据服务层 → SQL生成(强约束)+校验+执行 (大模型②)")
print()

# 导入配置
from backend.core.config import config
from backend.utils.database import db_manager
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s'
)

print(f"  大模型: {config.model_name}")
if config.use_backup_model:
    print(f"  ⚠️ 使用备用模型: {config.backup_model_name}")
else:
    print(f"  备用模型: {config.backup_model_name} (未启用)")
print(f"  业务库: {config.business_db_config['database']}@{config.business_db_config['host']}")
print(f"  语义库: {config.semantic_db_config['database']}@{config.semantic_db_config['host']}")
print("=" * 70)

logger = logging.getLogger(__name__)

# 初始化数据库连接
try:
    db_manager.init()
    logger.info("✅ 数据库连接成功")
except Exception as e:
    logger.warning(f"⚠️ 数据库连接失败: {e}")
    logger.warning("   服务仍可启动，但问答功能需要数据库支持")

# 启动服务
import uvicorn
uvicorn.run(
    "backend.api.routes:app",
    host=config.service_host,
    port=config.service_port,
    reload=False,  # 禁用热重载，避免环境变量丢失
    log_level="info"
)
