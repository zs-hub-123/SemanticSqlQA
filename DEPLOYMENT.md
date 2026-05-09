# SemanticSqlQA - 部署与环境配置指南

本文档详细说明如何在新环境中部署和配置 SemanticSqlQA 项目。

---

## 📋 目录

1. [系统要求](#系统要求)
2. [快速开始](#快速开始)
3. [环境变量配置详解](#环境变量配置详解)
4. [数据库初始化](#数据库初始化)
5. [大模型配置](#大模型配置)
6. [常见问题排查](#常见问题排查)
7. [安全注意事项](#安全注意事项)

---

## 系统要求

### 软件依赖

| 组件 | 最低版本 | 推荐版本 | 用途 |
|------|----------|----------|------|
| Python | 3.9+ | 3.11+ | 后端运行时 |
| Node.js | 16+ | 18+ LTS | 前端构建 |
| MySQL | 8.0+ | 8.0+ | 数据存储 |
| pip | 最新 | - | Python包管理 |
| npm | 8+ | 10+ | Node包管理 |

### Python 依赖（requirements.txt）

```
fastapi==0.104.0
uvicorn==0.24.0
mysql-connector-python==8.2.0
python-dotenv==1.0.0
requests==2.31.0
pydantic==2.5.0
```

---

## 快速开始

### 步骤 1：克隆项目

```bash
git clone https://github.com/your-username/SemanticSqlQA.git
cd SemanticSqlQA
```

### 步骤 2：创建环境变量文件

```bash
cp .env.example .env
```

**重要**: 编辑 `.env` 文件，填入你的实际配置（见下方[环境变量配置详解](#环境变量配置详解)）

### 步骤 3：安装后端依赖

```bash
pip install -r requirements.txt
```

### 步骤 4：安装前端依赖

```bash
cd frontend
npm install
cd ..
```

### 步骤 5：初始化语义层数据库

```bash
python init_semantic_db.py
```

### 步骤 6：启动服务

**终端1 - 启动后端：**
```bash
python start.py
```

**终端2 - 启动前端：**
```bash
cd frontend
npm run dev
```

### 步骤 7：访问系统

- 前端界面: http://localhost:5173
- 后端API: http://localhost:8002
- API文档: http://localhost:8002/docs

---

## 环境变量配置详解

### 必需配置项

#### 1. 大模型API（必需）

```env
# 主模型配置（必须提供）
API_KEY=sk-your-api-key-here                    # 你的API密钥
API_BASE_URL=https://api.your-llm-provider.com/v1 # API地址
MODEL_NAME=qwen-plus                              # 模型名称
```

**支持的API提供商示例：**

| 提供商 | API_BASE_URL | MODEL_NAME |
|--------|--------------|------------|
| 通义千问 (scnet) | `https://api.scnet.cn/api/llm/v1` | `Qwen3-235B-A22B` |
| OpenAI | `https://api.openai.com/v1` | `gpt-4-turbo` |
| 本地部署 | `http://localhost:port/v1` | 自定义 |

#### 2. 数据库配置（必需）

```env
# 业务数据库（存储真实业务数据）
DB_HOST=localhost          # 数据库地址
DB_PORT=3306               # 数据库端口
DB_USER=root               # 用户名
DB_PASSWORD=your_password  # 密码
DB_NAME=text02             # 数据库名

# 语义层数据库（存储指标定义、表关系等）
SEMANTIC_DB_HOST=localhost
SEMANTIC_DB_PORT=3306
SEMANTIC_DB_USER=root
SEMANTIC_DB_PASSWORD=your_password
SEMANTIC_DB_NAME=text02_semantic
```

**注意**: 可以使用同一个MySQL实例，但需要创建两个不同的数据库。

### 可选配置项

#### 3. 备选模型（可选）

```env
BACKUP_API_KEY=your_backup_api_key
BACKUP_API_BASE_URL=http://backup-model-server:port/v1
BACKUP_MODEL_NAME=backup-model-name
USE_BACKUP_MODEL=false   # 是否默认使用备选模型
```

#### 4. 服务端口（可选）

```env
SERVICE_HOST=0.0.0.0    # 监听地址（0.0.0.0允许外部访问）
SERVICE_PORT=8002       # 后端服务端口
```

---

## 数据库初始化

### 1. 创建MySQL数据库

确保MySQL服务已运行，然后创建两个数据库：

```sql
-- 创建业务数据库
CREATE DATABASE IF NOT EXISTS text02 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

-- 创建语义层数据库
CREATE DATABASE IF NOT EXISTS text02_semantic 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;
```

### 2. 初始化语义层结构

运行初始化脚本会自动创建以下内容：

**6张核心表：**
- `standard_metrics_dimensions` - 标准指标维度字典表
- `spoken_aliases` - 口语别名映射表
- `table_metadata` - 表元信息表
- `table_relations` - 表关联关系表
- `business_rules` - 业务规则表
- `dimension_hierarchies` - 维度层级表

**初始数据：**
- 50+ 个标准指标定义
- 40+ 个标准维度定义
- 200+ 条口语别名映射
- 15张表的关联关系

### 3. 导入测试数据（可选）

如果需要运行测试套件，需要导入模拟数据：

```bash
mysql -u root -p text02 < sql/mock_data.sql
```

---

## 大模型配置

### 支持的模型类型

SemanticSqlQA 使用 **2次大模型调用** 架构：

| 调用次序 | 用途 | 要求 |
|----------|------|------|
| 第1次 | 自然语言→标准词（NLParser） | 支持中文理解 |
| 第2次 | 结构化SQL生成（SQLGenerator） | 支持SQL生成 |

### 配置建议

#### 方案A：单模型（推荐入门）
```env
API_KEY=sk-your-key
API_BASE_URL=https://api.scnet.cn/api/llm/v1
MODEL_NAME=Qwen3-235B-A22B
```

#### 方案B：双模型（主备切换）
```env
# 主模型
API_KEY=sk-primary-key
API_BASE_URL=https://api.primary.com/v1
MODEL_NAME=gpt-4-turbo

# 备选模型
BACKUP_API_KEY=sk-backup-key
BACKUP_API_BASE_URL=http://local-model:8080/v1
BACKUP_MODEL_NAME=local-qwen
USE_BACKUP_MODEL=false  # 默认使用主模型
```

### 模型切换方式

1. **通过前端界面切换**：统计页面 → 模型选择器组件
2. **通过API切换**：
```bash
curl -X POST http://localhost:8002/api/test/model/switch \
  -H "Content-Type: application/json" \
  -d '{"model_name": "backup-model"}'
```

---

## 常见问题排查

### 问题1：连接数据库失败

**错误信息**：
```
mysql.connector.errors.InterfaceError: 2003: Can't connect to MySQL server
```

**解决方案**：
1. 确认MySQL服务已启动
2. 检查 `.env` 中的 `DB_HOST` 和 `DB_PORT` 是否正确
3. 确认防火墙允许3306端口访问

### 问题2：大模型调用失败

**错误信息**：
```
APIError: SQL生成失败: 401 Unauthorized
```

**解决方案**：
1. 检查 `API_KEY` 是否正确
2. 确认 `API_BASE_URL` 格式正确（通常以 `/v1` 结尾）
3. 确认API额度未耗尽

### 问题3：语义层初始化失败

**错误信息**：
```
Error: 1050 (42S01): Table 'standard_metrics_dimensions' already exists
```

**解决方案**：这是正常警告，表示表已存在，可以忽略。

### 问题4：前端无法连接后端

**检查清单**：
1. 后端是否在运行（访问 http://localhost:8002/docs 测试）
2. 前端代理配置是否正确（查看 `frontend/vite.config.js`）
3. CORS设置是否允许跨域请求

### 问题5：测试套件结果为空

**解决方案**：
```bash
# 初始化空结果文件
python init_test_results.py
```

---

## 安全注意事项

### ⚠️ 必须遵守的安全规则

1. **永远不要提交 .env 文件到版本控制**
   - 已在 `.gitignore` 中配置
   - 提交前检查：`git status` 不应显示 .env

2. **定期轮换API密钥**
   - 如果怀疑密钥泄露，立即更换
   - 在API提供商后台设置IP白名单

3. **生产环境部署建议**
   - 使用HTTPS而非HTTP
   - 设置强密码（至少12位，包含大小写字母、数字、特殊字符）
   - 启用数据库访问日志
   - 定期备份数据库

4. **敏感信息检查清单**

| 检查项 | 位置 | 状态 |
|--------|------|------|
| API密钥已隐藏 | `.gitignore` | ✅ |
| 数据库密码已隐藏 | `.gitignore` | ✅ |
| 内网IP已移除 | `.env.example` | ✅ |
| 无硬编码凭证 | 代码审查 | ⚠️ 需人工检查 |

---

## 生产环境部署建议

### Docker部署（推荐）

创建 `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8002

CMD ["python", "start.py"]
```

### Nginx反向代理配置

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 性能优化建议

1. **数据库优化**
   - 为常用查询字段添加索引
   - 调整 `innodb_buffer_pool_size` 为可用内存的70%

2. **缓存层**
   - Redis缓存语义层数据（减少DB查询）
   - 缓存热门问题的SQL结果（TTL=5分钟）

3. **监控告警**
   - 监控API响应时间
   - 监控错误率（目标<1%）
   - 监控资源使用率

---

## 更新日志

| 版本 | 日期 | 主要变更 |
|------|------|----------|
| V5.2 | 2026-05-09 | 移除Milvus依赖，强化MQL控制 |
| V5.1 | 2026-05-09 | 多模型切换，测试分析脚本 |
| V5.0 | 2026-05-08 | MQL中间层，增强指标元数据 |
| V4.0 | 2026-05-08 | 四层架构重构 |

---

## 技术支持

- **Issue提交**: https://github.com/your-username/SemanticSqlQA/issues
- **Wiki文档**: https://github.com/your-username/SemanticSqlQA/wiki
- **讨论区**: https://github.com/your-username/SemanticSqlQA/discussions

---

*最后更新: 2026-05-09*
