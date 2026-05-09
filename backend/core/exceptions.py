# ============================================================
# 异常定义 - 统一错误处理
# V5.2更新：移除MilvusError（已下线Milvus）
# ============================================================

class Text2SQLError(Exception):
    def __init__(self, message, code="ERROR", details=None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)

    def to_dict(self):
        return {"error": self.message, "code": self.code, "details": self.details}

class ValidationError(Text2SQLError):
    def __init__(self, message): super().__init__(message, "VALIDATION_ERROR")

class SemanticError(Text2SQLError):
    def __init__(self, message): super().__init__(message, "SEMANTIC_ERROR")

class SQLValidationError(Text2SQLError):
    def __init__(self, message, sql=None):
        super().__init__(message, "SQL_VALIDATION_ERROR", {"sql": sql})

class APIError(Text2SQLError):
    def __init__(self, message): super().__init__(message, "API_ERROR")
