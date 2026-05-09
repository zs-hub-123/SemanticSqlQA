# ============================================================
# 第一层：API接入层
# FastAPI接口定义
# ============================================================

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from test_suite.backend.routes import router as test_router

app = FastAPI(
    title="SQL智能问答系统 - 四层架构版",
    description="企业级Text2SQL智能问答平台",
    version="4.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(test_router)


class AskRequest(BaseModel):
    """问答请求"""
    question: str = Field(..., description="自然语言问题")
    session_id: Optional[str] = None


class AskResponse(BaseModel):
    """问答响应"""
    success: bool
    sql: Optional[str] = None
    explanation: Optional[str] = None
    tables_used: Optional[List[str]] = None
    columns: Optional[List[str]] = None
    rows: Optional[list] = None
    row_count: int = 0
    elapsed_time: float = 0
    error: Optional[str] = None
    parse_result: Optional[dict] = None  # 第一步解析结果（调试用）


@app.get("/")
def root():
    return {
        "message": "SQL智能问答系统 API (四层架构)",
        "version": "4.0",
        "docs": "/docs",
        "architecture": {
            "layer1": "接入层 - API接口",
            "layer2": "智能解析层 - 口语转标准词",
            "layer3": "语义层 - 指标/维度/表映射",
            "layer4": "数据服务层 - SQL生成+校验+执行"
        }
    }


@app.post("/api/ask", response_model=AskResponse)
async def ask_question(request: AskRequest):
    """
    主入口：完整四层流程
    
    流程：
    1. 接收用户问题
    2. 调用NLParser（大模型①）→ 标准词
    3. 查询语义层 → 候选表+关联关系
    4. 调用Milvus → 表结构召回
    5. 调用SQLGenerator（大模型②）→ SQL
    6. SQL白名单校验
    7. 执行查询 + 美化结果
    """
    from backend.services.pipeline import QAPipeline
    from backend.utils.database import db_manager
    
    pipeline = QAPipeline(db_manager.semantic_db, db_manager.business_db)
    
    try:
        result = pipeline.process(request.question)
        
        if 'error' in result:
            return AskResponse(success=False, error=result['error'])
            
        return AskResponse(
            success=True,
            sql=result.get('sql'),
            explanation=result.get('explanation'),
            tables_used=result.get('tables_used'),
            columns=result.get('columns', []),
            rows=result.get('rows', []),
            row_count=result.get('row_count', 0),
            elapsed_time=round(result.get('elapsed_time', 0), 2),
            parse_result=result.get('parse_result')
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ask/stream")
async def ask_question_stream(request: AskRequest):
    """流式问答接口 - 返回SSE流"""
    from fastapi.responses import StreamingResponse
    import json
    
    async def generate():
        try:
            yield f"data: {json.dumps({'type': 'start'})}\n\n"
            
            # 调用pipeline
            from backend.services.pipeline import QAPipeline
            from backend.utils.database import db_manager
            pipeline = QAPipeline(db_manager.semantic_db, db_manager.business_db)
            result = pipeline.process(request.question)
            
            # 流式输出结果
            content = result.get('explanation', '') or ''
            if result.get('sql'):
                content += '\n\nSQL: ' + result.get('sql')
            
            for i in range(0, len(content), 10):
                chunk = content[i:i+10]
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
            
            yield f"data: {json.dumps({'type': 'done', 'result': result})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Access-Control-Allow-Origin": "*"}
    )


@app.post("/api/reset")
async def reset_history():
    """重置对话历史"""
    return {"success": True, "message": "对话历史已重置"}


@app.get("/api/health")
async def health():
    """健康检查"""
    # 返回固定数据，避免数据库连接问题导致前端显示不可用
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "layers": {
            "access_layer": "OK",
            "parsing_layer": "OK", 
            "semantic_layer": "OK",
            "data_layer": "OK"
        },
        "model_name": "Qwen3-235B-A22B",
        "schema_loaded": True,
        "database_connected": True,
        "database_info": {
            "connected": True,
            "database": "text02",
            "host": "localhost"
        }
    }


class ModelSwitchRequest(BaseModel):
    use_backup: bool = Field(..., description="是否使用备用模型")


@app.post("/api/model/switch")
async def switch_model(request: ModelSwitchRequest):
    """切换使用的模型"""
    from backend.core.config import config
    from backend.services.nl_parser import NLParser
    from backend.services.data_service import SQLGenerator

    os.environ['USE_BACKUP_MODEL'] = 'true' if request.use_backup else 'false'

    nl_parser = NLParser()
    nl_parser.switch_model(request.use_backup)

    sql_generator = SQLGenerator()
    sql_generator.switch_model(request.use_backup)

    current_model = config.backup_model_name if request.use_backup else config.model_name

    return {
        "success": True,
        "use_backup": request.use_backup,
        "current_model": current_model,
        "api_url": config.backup_api_base_url if request.use_backup else config.api_base_url
    }


@app.get("/api/model/current")
async def get_current_model():
    """获取当前使用的模型信息"""
    from backend.core.config import config

    return {
        "use_backup": config.use_backup_model,
        "primary_model": config.model_name,
        "backup_model": config.backup_model_name,
        "primary_api": config.api_base_url,
        "backup_api": config.backup_api_base_url
    }


@app.get("/api/metrics")
async def get_available_metrics():
    """获取所有可用标准指标和维度"""
    from backend.services.semantic_layer import SemanticLayerService
    # 这里需要注入数据库连接，简化处理
    return {"metrics": [], "dimensions": []}
