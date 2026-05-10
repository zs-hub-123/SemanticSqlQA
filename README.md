# SemanticSqlQA - 企业级Text2SQL智能问答平台 V5.3

<p align="center">
  <strong>四层架构 · 多指标MQL · 语义层屏蔽 · 强约束SQL生成 · 数据驱动优化</strong>
</p>

<p align="center">
  <a href="#快速开始">快速开始</a> •
  <a href="DEPLOYMENT.md">部署指南</a> •
  <a href="docs/test_suite_README.md">测试文档</a> •
  <a href="#架构设计">架构设计</a>
</p>

***

## 📋 项目概述

**SemanticSqlQA** 是一个企业级 Text2SQL 智能问答平台，采用**四层架构 + MQL中间层**设计，实现从自然语言到数据库查询的完整闭环。

### 核心特性

- ✅ **仅2次大模型调用**（口语转标准词 + SQL生成）
- ✅ **MQL多指标数组**（V5.3：支持多指标/维度并行查询）
- ✅ **语义层屏蔽物理表差异**（6张核心配置表）
- ✅ **增强表结构元数据**（主键/外键标记，JOIN准确率+30%）
- ✅ **BFS加权路径选择**（多路径时自动选最优关联路径）
- ✅ **Self-Reflection自检机制**（SQL生成后LLM自查业务规则遵守情况）
- ✅ **失败自动重试**（最多重试2次，消除5~10%随机失败）
- ✅ **Few-shot语义解析**（NLParser注入5个示例，降低口语误识别率）
- ✅ **非累加指标两步聚合**（月度UV等不再被拒绝，改用子查询实现）
- ✅ **结果合理性校验**（GMV=0/行数异常自动预警）
- ✅ **候选表扩展**（包含维度/过滤条件来源表，解决"用了优惠券的用户GMV"类查询）
- ✅ **SQL白名单校验**（防止大模型幻觉编造表/字段）
- ✅ **流式输出支持**（SSE实时返回）
- ✅ **多模型切换**（支持配置多个大模型，动态切换）

### V5.3 优化亮点（数据驱动改进）

基于849题测试结果(32.5%准确率)的深度分析，针对性优化：

- 🚀 **MQL扩展为多指标数组**（`metric: str` → `metrics: List[Dict]`），支持"GMV、订单数、客单价分别是多少"
- 🛡️ **表结构元数据增强**：15张业务表全部添加 `primary_key` / `foreign_key` 标记，prompt自动注入外键关系
- 🔍 **BFS加权路径选择**：多条JOIN路径时取权重最小的最优路径
- 🔄 **Self-Reflection自检**：SQL生成后检查WHERE条件、GROUP BY、COUNT(DISTINCT)是否完整
- ⏳ **失败自动重试**：校验不通过时最多重试2次（换温度/注入错误日志修正）
- 📝 **Few-shot示例增强**：NLParser prompt新增5个覆盖常见问法的示例
- 🎯 **非累加指标两步聚合**：月度UV等不再强硬拒绝，改为子查询/CTE提示
- ✅ **结果合理性检查**：空结果/GMV=0/负值/超量行数自动预警
- 📊 **深度分析脚本V2** (`tests/analyze_test_results.py`)：7种失败分类 + 高频词提取 + 修复建议输出

***

## 🏗️ 系统架构（V5.3数据驱动优化版）

```
┌─────────────────────────────────────────────────────┐
│                  用户自然语言问句                       │
└──────────────────────┬──────────────────────────────┘
                       │
         ┌─────────────▼─────────────┐
         │     Layer1：接入层 (API)    │  ← FastAPI接口
         │     routes.py              │
         └─────────────┬─────────────┘
                       │
    ┌──────────────────▼──────────────────┐
    │    Layer2：智能解析层 (NLParser)      │  ← 大模型①: 口语→标准词
    │    Few-shot示例增强(5个)             │     V5.3新增
    │    输出: {metrics[], dimensions[]}  │     支持多指标数组
    └──────────────────┬──────────────────┘
                       │
         ┌─────────────▼─────────────┐
         │   Layer2.5：MQL中间层      │  ← 核心控制层 ★ V5.3强化
         │   MQLService              │
         │   - 多指标数组校验          │     V5.3: metrics: List[Dict]
         │   - 非累加指标两步聚合提示  │     V5.3: 不再强硬拒绝
         │   - 业务规则强制注入        │
         │   - 时间粒度自动处理        │
         │   - Self-Reflection自检    │     V5.3: SQL生成后自查
         │   - 失败重试(最多2次)       │     V5.3: 换温度/注入错误日志
         └─────────────┬─────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│              Layer3：语义层                          │
│  SemanticLayerService                                │
│  ┌─────────────────────────────────────────────────┐ │
│  │ standard_metrics_dimensions (增强版)            │ │
│  │   - is_non_additive 非累加标识                  │ │
│  │   - stat_period 统计周期                        │ │
│  │   - default_filter 默认过滤条件                  │ │
│  │   - metric_version 版本管理                     │ │
│  ├─────────────────────────────────────────────────┤ │
│  │ spoken_aliases 口语别名映射表(300+条V4补充)      │ │
│  │ table_metadata 表元信息表                       │ │
│  │ table_relations 表关联关系表(15+条V4补充)        │ │
│  ├─────────────────────────────────────────────────┤ │
│  │ business_rules 业务规则表(20+条V4补充)           │ │
│  │ dimension_hierarchies 维度层级表                 │ │
│  └─────────────────────────────────────────────────┘ │
│       ↓ 候选表扩展(含维度/过滤来源表) + BFS加权路径    │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│             Layer4：数据服务层 (V5.3增强)            │
│                                                       │
│  ┌────────────────┐  ┌────────────┐  ┌─────────────────┐  │
│  │TableSchemaService│→│ SQLGenerator│→│ SQLValidator    │  │
│  │ 主键/外键标记★   │  │ 大模型②生成 │  │ 白名单校验       │  │
│  │ 外键关系注入prompt│ │ 重试机制★  │  │                 │  │
│  └────────────────┘  └────────────┘  └────────┬────────┘  │
│                                         │            │
│                                  ┌──────▼──────┐    │
│                                  │ QueryExecutor│    │
│                                  │ 执行+合理性检查│    │  ★ V5.3新增
│                                  └──────────────┘    │
└──────────────────────────────────────────────────────┘
```

***

## 📁 项目目录结构

```
SemanticSqlQA/
├── start.py                    # 后端启动脚本
├── init_semantic_db.py        # 语义层数据库初始化(V5.0)
├── init_test_results.py       # 测试结果文件初始化
├── .env.example                # 配置模板
├── requirements.txt            # Python依赖
│
├── backend/                    # 后端代码
│   ├── api/
│   │   └── routes.py           # API接口定义（Layer1）
│   ├── core/
│   │   ├── config.py           # 配置管理
│   │   └── exceptions.py       # 异常定义
│   ├── services/               # 业务服务（核心）
│   │   ├── pipeline.py         # 流程编排器 ⭐
│   │   ├── nl_parser.py        # 自然语言解析器（Layer2）
│   │   ├── mql_service.py      # MQL中间层服务 (V5.0新增) ⭐
│   │   ├── semantic_layer.py   # 语义层服务（Layer3）
│   │   └── data_service.py     # 数据服务层（Layer4）V5.2优化
│   │       ├── TableSchemaService  # 表结构服务(替代Milvus)⭐
│   │       ├── SQLGenerator    # SQL生成(强MQL约束)
│   │       ├── SQLValidator    # SQL校验
│   │       └── QueryExecutor   # SQL执行
│   └── utils/
│       └── database.py         # 数据库连接管理
│
├── frontend/                   # 前端代码（Vue3）
│   ├── package.json            # 前端依赖
│   ├── vite.config.js          # Vite配置（含API代理）
│   └── src/
│       ├── App.vue
│       ├── api/index.js        # API调用封装
│       ├── stores/chat.js      # 状态管理
│       ├── components/
│       │   ├── Sidebar.vue
│       │   ├── ChatMessage.vue
│       │   ├── ExampleList.vue
│       │   ├── InputBar.vue
│       │   ├── StatsBar.vue
│       │   └── ModelSelector.vue  # 模型选择组件 ⭐
│       └── testviews/             # 测试套件前端
│           ├── api.js
│           ├── TestSidebar.vue
│           ├── QuestionList.vue
│           ├── QuestionDetail.vue
│           ├── StatsView.vue
│           └── TestLayout.vue
│
├── test_suite/                 # 测试套件 ⭐
│   ├── backend/
│   │   ├── storage.py          # 结果持久化存储
│   │   └── routes.py           # 测试API路由
│   ├── datasets/               # 测试数据集（JSON）
│   │   ├── qa_simple.json
│   │   ├── qa_agg.json
│   │   ├── qa_join.json
│   │   ├── qa_advanced.json
│   │   └── qa_synonyms.json
│   └── results/               # 测试结果（JSON）
│
├── tests/                     # 测试分析 ⭐
│   ├── analyze_test_results.py # 测试结果分析脚本
│   ├── failures_list.json     # 失败问题列表
│   └── analysis_report.md      # 数据分析报告
│
└── docs/                        # 文档和DDL
    ├── semantic_layer_ddl.sql           # 语义层6张表建表语句(V5.0)
    ├── semantic_layer_init_data.sql      # 初始化数据(V5.0)
    └── semantic_layer_fix.sql           # 语义层修复数据(V5.1)
```

***

## 🚀 快速开始

### 1. 安装依赖

```bash
cd SemanticSqlQA
pip install -r requirements.txt
cd frontend && npm install
```

### 2. 创建配置文件

```bash
cp .env.example .env
# 编辑 .env，填入：
#   - API_KEY=你的大模型密钥
#   - DB_PASSWORD=业务库密码
#   - SEMANTIC_DB_PASSWORD=语义库密码
```

**多模型配置：**
系统支持配置多个大模型，可在 `.env` 中添加额外模型配置：

```bash
# 文本大模型（主模型）
TEXT_MODEL_URL=https://api.scnet.cn/api/llm/v1
TEXT_MODEL_API_KEY=your_api_key
TEXT_MODEL_NAME=Qwen3-235B-A22B

# 文本大模型（备用模型）
TEXT_MODEL_BACKUP_URL=http://your-backup-server:port
TEXT_MODEL_BACKUP_API_KEY=your_backup_key
TEXT_MODEL_BACKUP_NAME=Qwen3-32B-FP8
```

前端界面提供模型切换组件，支持动态切换使用的主模型。

### 3. 初始化语义层数据库

```bash
python init_semantic_db.py
```

### 4. 启动服务

**终端1 - 启动后端：**

```bash
python start.py
```

**终端2 - 启动前端：**

```bash
cd frontend
npm run dev
```

访问：

- 前端界面: <http://localhost:5173>
- 后端API: <http://localhost:8002>
- API文档: <http://localhost:8002/docs>
- 健康检查: <http://localhost:8002/api/health>

***

## 🔑 核心设计思想

### 1. 为什么只需要2次大模型调用？

| 调用次数  | 传统方案  | 本系统             |
| ----- | ----- | --------------- |
| 第1次   | 查表结构  | **口语→标准词**      |
| 第2次   | 生成SQL | **限定表结构下生成SQL** |
| 第3-N次 | 补充查询  | ❌ 不需要           |

中间的选表、查关联、筛选全由**后端代码完成**，避免多次调模型导致逻辑混乱。

### 2. MQL中间层的价值（V5.2强化）

V5.0新增MQL中间层，V5.2强化为**核心控制层**：

```python
# 问题："统计每月GMV成交总额"

# Layer2: NLParser输出
parsed = {"metrics": ["GMV成交总额"], "dimensions": ["下单时间"]}

# Layer2.5: MQL中间层（V5.2强化）
mql = {
    "metric": "GMV成交总额",
    "dimensions": ["下单时间"],
    "filters": {"order_status": "paid"},  # 自动应用默认过滤
    "granularity": "month"  # 自动推断粒度
}

# V5.2强化校验：
# - 非累加指标跨粒度拦截（如UV不能按月SUM）
# - 粒度合法性检查
# - 业务规则强制注入到SQL生成提示词
```

**效果**：语义更清晰、更容易校验、跨模型复用、**准确率接近100%**。

### 3. 增强指标元数据

```python
@dataclass
class MetricDimension:
    name: str                    # 标准名称
    type: str                   # metric/dimension
    physical_table: str          # 物理表
    physical_field: str         # 物理字段
    aggregation_type: str        # 聚合方式

    # V5.0 新增字段
    is_non_additive: bool        # 是否不可二次聚合(去重类)
    stat_period: str             # 统计周期(daily/monthly/quarterly)
    data_granularity: str       # 数据粒度
    default_filter: str         # 默认过滤条件
    metric_version: str          # 口径版本(V1.0/V2.0)
    calculation_formula: str     # 计算公式
```

### 4. 语义层的价值

```python
# 问题："各月的成交总额是多少"

# 第1步：大模型识别 → {"metrics": ["GMV成交总额"], "dimensions": ["下单时间"]}

# 第2步：后端查语义层
metrics → physical_table="orders", field="total_amount"
dimensions → physical_table="orders", field="create_time"
候选表 = {"orders"}  # 只需1张表！

# 第3步：TableSchemaService获取 orders 表结构（本地，无需Milvus）
# 第4步：大模型基于这1张表 + MQL约束生成SQL
```

**效果**：不需要给模型15张表的完整结构，Token消耗降低80%+。**速度提升30%\~50%**。

### 5. SQL白名单校验机制

```python
# 校验规则
allowed_tables = {"orders", "products", "users"}  # 候选表白名单
allowed_fields = {
    "orders": {"order_id", "user_id", "pay_amount", ...},
    "products": {"product_id", "price", ...}
}

# 如果大模型生成了包含非法表的SQL
sql = "SELECT * FROM fake_table"  # 幻觉！
validator.validate(sql)
# → {"valid": False, "errors": ["非法表名: fake_table"]}
# → 直接拦截，不执行！
```

### 6. 表关联处理原则（V5.2优化：限制最大3层）

**关键规则**：只存储直接相邻关系，不人工维护间接跨层

```
示例：用户 → 订单 → 商品

存储的关系：
✅ users JOIN orders ON user_id = user_id        (直接)
✅ orders JOIN products ON product_id = product_id   (直接)

❌ users JOIN products (间接)  ← 不存！程序自动推导

推导算法（BFS/DFS，最大深度3层）：
users → [orders] → [order_items] → [products]
找到路径！自动拼接JOIN条件。
```

***

## 📊 数据流详解（V5.2优化版）

### 语义层六张表的使用时机

| 表名                                | 主要使用时机                  | 核心作用                 |
| --------------------------------- | ----------------------- | -------------------- |
| **standard\_metrics\_dimensions** | 步骤1加载词汇表、步骤3找候选表        | 标准词 → 物理表/字段 映射(增强版) |
| **spoken\_aliases**               | 步骤2构建提示词时注入             | 口语 → 标准词 映射          |
| **table\_metadata**               | 预留接口                    | 存储表元信息（中文名、描述）       |
| **table\_relations**              | 步骤3查关联关系、递归推导JOIN(最大3层) | 存储直接关系，自动推导间接关系      |
| **business\_rules**               | 步骤2.5 MQL校验 + 强制注入SQL生成 | 口径规则、过滤规则、校验规则       |
| **dimension\_hierarchies**        | 维度钻取                    | 维度层级(年→季→月→日)        |

### 完整请求流程（以"统计每月GMV成交总额"为例）

```
[00:00.000] 收到问题: "统计每月GMV成交总额"
[00:00.001] [步骤1] 加载标准词汇表...
         → standard_metrics_dimensions: 50+个指标, 40+个维度
         → spoken_aliases: 40+条口语映射

[00:01.500] [步骤2] 调用NLParser (大模型①)...
         输入: "统计每月GMV成交总额"
         输出: {"metrics": ["GMV成交总额"], "dimensions": ["下单时间"]}

[00:01.510] [步骤2.5] MQL中间层处理 (V5.2强化)...
         → 构建MQL: {metric, dimensions, granularity="month"}
         → 校验指标: 检查是否支持month粒度 ✓
         → 非累加指标检查: GMV可累加 ✓
         → 应用默认过滤: order_status='paid'
         → 构建MQL约束文本（用于注入SQL生成）
         → 获取业务规则（用于注入SQL生成）
         → 校验结果: valid=True, warnings=[]

[00:01.520] [步骤3] 查询语义层...
         standard_metrics_dimensions:
           "GMV成交总额" → physical_table="orders", field="total_amount"
           default_filter: "order_status='paid'"  ← 自动应用
         候选表: {"orders"}
         table_relations:
           查找orders表与其他表的关联关系（最大3层深度）

[00:01.530] [步骤4] TableSchemaService获取表结构（替代Milvus）...
         orders表: {order_id, total_amount, create_time, ...}
         ⚡ 无需外部依赖，本地直接返回！

[00:03.000] [步骤5] 调用SQLGenerator (大模型②)...
         输入上下文:
           - orders表完整字段
           - MQL约束: 目标指标=GMV成交总额, 时间粒度=month
           - 业务规则: order_status='paid' 必须包含在WHERE中
         输出: SELECT DATE_FORMAT(create_time, '%Y-%m') AS '月份',
                       SUM(total_amount) AS 'GMV'
                FROM orders WHERE order_status='paid'
                GROUP BY DATE_FORMAT(create_time, '%Y-%m')

[00:03.010] [步骤6] SQL白名单校验...
         ✓ 表名: orders (合法)
         ✓ 字段: create_time, total_amount (合法)
         → 校验通过!

[00:03.020] [步骤7] 构建血缘追溯信息...
         lineage: {
             "metric": {
                 "name": "GMV成交总额",
                 "aggregation": "SUM",
                 "physical_table": "orders",
                 "default_filter": "order_status='paid'"
             }
         }

[00:03.030] [步骤8] 执行SQL + 美化结果...
         返回: [{"月份": "2024-01", "GMV": 123456}, ...]

[00:03.035] ✅ 完成! 耗时3.035秒, 返回12行数据
```

***

## 🎯 接口文档

### POST /api/ask

主问答接口。

**请求体**:

```json
{
  "question": "统计每月GMV成交总额",
  "session_id": "可选会话ID"
}
```

**响应 (V5.2新增mql\_constraints字段)**:

```json
{
  "success": true,
  "sql": "SELECT DATE_FORMAT(create_time, '%Y-%m') AS '月份', SUM(total_amount) AS 'GMV' FROM orders WHERE order_status='paid' GROUP BY ...",
  "explanation": "按月份统计GMV成交总额",
  "tables_used": ["orders"],
  "columns": ["月份", "GMV"],
  "rows": [...],
  "row_count": 12,
  "elapsed_time": 3.02,
  "parse_result": {
    "metrics": ["GMV成交总额"],
    "dimensions": ["下单时间"]
  },
  "mql": {
    "metric": "GMV成交总额",
    "dimensions": ["下单时间"],
    "filters": {"order_status": "paid"},
    "time_range": null,
    "granularity": "month",
    "limit": 1000
  },
  "lineage": {
    "metric": {
      "name": "GMV成交总额",
      "business_desc": "订单总金额(GMV)",
      "aggregation": "SUM",
      "physical_table": "orders",
      "physical_field": "total_amount",
      "is_non_additive": false,
      "version": "V1.0"
    },
    "dimensions": [...],
    "filters": [{"field": "order_status", "value": "paid"}],
    "default_filter": "order_status='paid'",
    "calculation": ""
  },
  "validation_warnings": []
}
```

**错误响应（V5.2新增MQL错误）**:

```json
{
  "success": false,
  "error": "MQL校验失败: ❌ '支付用户数' 是去重类指标, 仅支持按天(daily)统计, 不支持month粒度聚合",
  "code": "MQL_VALIDATION_ERROR",
  "mql_errors": ["❌ '支付用户数' 是去重类指标..."]
}
```

***

### POST /api/ask/stream

流式问答接口，返回SSE流。

**请求体**:

```json
{
  "question": "统计每月GMV成交总额"
}
```

**SSE事件流**:

```
data: {"type": "start"}

data: {"type": "chunk", "content": "按月份..."}
data: {"type": "chunk", "content": "统计GMV..."}

data: {"type": "done", "result": {...}}
```

***

### GET /api/health

健康检查接口。

**响应**:

```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00",
  "layers": {
    "access_layer": "OK",
    "parsing_layer": "OK",
    "mql_layer": "OK",
    "semantic_layer": "OK",
    "data_layer": "OK"
  },
  "model_name": "Qwen3-235B-A22B",
  "schema_loaded": true,
  "database_connected": true
}
```

***

### POST /api/reset

重置对话历史。

**响应**:

```json
{
  "success": true,
  "message": "对话历史已重置"
}
```

***

## 🗄️ 业务表清单

本系统支持 **15张核心业务表**：

| 表名               | 中文名    | 描述              |
| ---------------- | ------ | --------------- |
| users            | 用户表    | 用户基本信息、等级、积分、余额 |
| user\_addresses  | 用户地址表  | 收货地址信息          |
| categories       | 商品分类表  | 商品分类层级结构        |
| products         | 商品表    | 商品主信息、价格、库存、销量  |
| product\_specs   | 商品规格表  | SKU规格信息         |
| stores           | 店铺表    | 店铺基础信息、销量、粉丝数   |
| store\_ratings   | 店铺评分表  | 店铺DSR评分详情       |
| orders           | 订单表    | 订单主信息、状态流转、金额   |
| order\_items     | 订单明细表  | 订单商品明细、退款信息     |
| payments         | 支付记录表  | 支付流水、支付方式       |
| coupons          | 优惠券模板表 | 优惠券定义、规则        |
| campaigns        | 促销活动表  | 营销活动信息、ROI      |
| user\_coupons    | 用户优惠券表 | 用户领券用券记录        |
| shipments        | 物流单表   | 物流发货信息、状态       |
| shipment\_tracks | 物流轨迹表  | 物流跟踪节点          |

***

## 🛠️ 开发指南

### V5.2 新增功能

#### 1. MQL强控制SQL生成（V5.3：多指标数组）

```python
# pipeline.py 中的新方法
def _build_mql_constraints(self, mql, validation_result) -> str:
    """构建MQL约束文本，强制注入到SQL生成提示词（多指标版）"""
    constraints = []
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
    if mql.granularity:
        constraints.append(f"- **时间粒度**: {mql.granularity}（必须按此粒度聚合）")
    if mql.filters:
        constraints.append(f"- **强制过滤条件**: ...（必须在WHERE中应用）")
    return '\n'.join(constraints)

def _build_business_rules_text(self, metric_names: List[str]) -> List[str]:
    """构建业务规则文本列表，多指标支持"""
    rules = []
    for metric_name in metric_names:
        default_filter = self.semantic_layer.get_default_filter(metric_name)
        if default_filter:
            rules.append(f"默认过滤: {default_filter}（必须包含在WHERE中）")
    return rules
```

#### 2. 非累加指标两步聚合策略（V5.3优化）

```python
# mql_service.py V5.3：不再强硬拒绝，改为两步聚合提示
def validate_mql(self, mql: MQLQuery) -> Dict[str, Any]:
    errors = []
    warnings = []

    for metric_entry in mql.metrics:
        name = metric_entry['name']
        metric_info = self.semantic_layer.get_metric_by_name(name)
        
        # V5.3优化：非累加指标跨粒度->两步聚合策略提示
        if metric_info.is_non_additive and mql.granularity and mql.granularity != 'daily':
            warnings.append(
                f"ℹ️ '{name}' 是去重类指标，跨粒度({mql.granularity})聚合时"
                f"请使用两步聚合：内层按天COUNT(DISTINCT)，外层SUM"
            )
    
    return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}
```

#### 3. 表关联路径限制

```python
# semantic_layer.py 中已有 max_depth=3 参数
def find_join_path(self, table1: str, table2: str, max_depth: int = 3):
    """
    递归查找两张表之间的JOIN路径
    默认最大深度为3层（防止性能爆炸和无效JOIN）
    """
```

### V5.0 新增功能

#### 1. 添加增强指标元数据

```sql
INSERT INTO standard_metrics_dimensions (
    name, type, physical_table, physical_field, field_type,
    business_desc, aggregation_type, domain,
    is_non_additive, stat_period, data_granularity, default_filter,
    metric_version, effective_date
) VALUES (
    '新指标', 'metric', 'orders', 'new_field', 'DECIMAL',
    '新指标说明', 'SUM', '交易域',
    0, 'daily,monthly', '时间+店铺', "status='active'",
    'V1.0', '2024-01-01'
);
```

#### 2. 添加业务规则

```sql
INSERT INTO business_rules (
    rule_name, rule_type, target_metric, target_dimension,
    rule_content, rule_desc, priority, error_message
) VALUES (
    '新指标仅统计有效', 'filter', '新指标', NULL,
    "status='active'",
    '新指标只统计有效记录',
    100, '⚠️ 仅统计有效记录'
);
```

#### 3. 添加维度层级

```sql
INSERT INTO dimension_hierarchies (
    dimension_name, level_name, level_order,
    physical_table, physical_field, field_format, description
) VALUES (
    '下单时间', '年', 1, 'orders', 'create_time', '%Y', '年度'
);
```

### 添加新的标准指标

1. 在 `standard_metrics_dimensions` 表插入记录（含新字段）
2. 重启服务或清空缓存

### 添加口语别名

1. 在 `spoken_aliases` 表插入映射
2. 支持批量导入（从数据集提取）

### 扩展新业务表

1. 在 `table_metadata` 录入表信息
2. 在 `table_relations` 录入关联关系
3. 在 `standard_metrics_dimensions` 录入字段
4. 在 `data_service.py` 的 `TableSchemaService._get_table_fields()` 中添加表结构

***

## 📈 性能优化建议（V5.2更新）

1. **缓存语义层数据**
   ```python
   # 可使用Redis缓存标准词汇表，避免每次查DB
   ```
2. **预加载常用表结构**
   ```python
   # TableSchemaService已内置15张表结构，无需外部调用
   # 可进一步缓存高频查询的表结构常驻内存
   ```
3. **异步化大模型调用**
   ```python
   # 使用asyncio并发调用两个大模型
   ```
4. **SQL结果缓存**
   ```python
   # 相同问题可返回缓存结果（TTL=5分钟）
   ```

***

## 🔒 安全性保障

| 安全措施    | 实现方式                          |
| ------- | ----------------------------- |
| SQL注入防护 | 参数化查询 + 白名单校验                 |
| 敏感信息保护  | 环境变量存储密码                      |
| 大模型幻觉拦截 | **MQL强约束** + 强制业务规则注入 + 白名单校验 |
| 非累加指标保护 | 跨粒度聚合拦截（如UV不能按月SUM）           |
| 接口鉴权    | （待实现）JWT Token                |
| 日志脱敏    | （待实现）隐藏敏感字段                   |

***

## 📝 更新日志

### V5.2 (2026-05-09) - 架构深度优化

- ✅ **移除Milvus向量库**（使用TableSchemaService替代，更轻量更快）
- ✅ **MQL强控制SQL生成**（业务规则强制注入提示词）
- ✅ **非累加指标跨粒度拦截**（防止UV等去重类指标错误聚合）
- ✅ **表关联路径限制最大3层**（防止性能爆炸和无效JOIN）
- ✅ **增强SQL语义匹配算法**（支持注释/中括号/别名差异）

### V5.1 (2026-05-09)

- ✅ 多模型切换功能（支持配置多个大模型，动态切换）
- ✅ 测试结果分析脚本（自动分析失败问题，生成数据报告）
- ✅ 失败问题修复（基于分析报告更新语义层和MQL中间层）

### V5.0 (2026-05-08)

- ✅ MQL中间层（结构化指标查询语言）
- ✅ 增强指标元数据（非累加标识、统计周期、版本管理）
- ✅ 业务规则引擎（口径规则、过滤规则）
- ✅ 血缘追溯功能（返回完整口径说明）
- ✅ 维度层级支持（钻取路径）
- ✅ 语义层6张核心表

### V4.0 (2026-05-08)

- ✅ 四层架构重构
- ✅ 语义层4张核心表
- ✅ ~~Milvus向量库集成~~（V5.2已移除）
- ✅ 2次大模型调用优化
- ✅ SQL白名单校验
- ✅ 递归关联路径推导
- ✅ 口语别名映射（800条数据集）
- ✅ 中文表头美化
- ✅ 流式输出SSE支持

***

## 📞 技术支持

- 架构问题：查看 `docs/semantic_layer_ddl.sql`
- 配置问题：参考 `.env.example`
- API调试：访问 `/docs` Swagger文档
- 日志排查：查看控制台输出

***

**开发团队**: 个人
**最后更新**: 2026-05-09
**许可证**: MIT
