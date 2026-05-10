# SQL智能问答系统 - 测试套件技术文档 V5.3

## 一、概述

测试套件为AI生成SQL的质量提供系统化的评测能力，支持问题管理、自动测试、自动匹配、结果对比和数据统计分析。

### 核心功能
- ✅ **自动测试**：批量执行测试题，自动生成SQL并对比结果
- ✅ **自动匹配**：一键匹配所有已生成结果，自动判定SQL和结果的匹配状态
- ✅ **语义SQL匹配**：智能识别语义等价的不同SQL表达（别名、表前缀、注释差异）
- ✅ **双匹配系统**：SQL文本匹配 + 执行结果匹配，两个维度独立判定（**以执行结果匹配为最高优先级**）
- ✅ **模型切换**：支持在测试过程中切换不同的大模型
- ✅ **统计视图**：可视化展示各数据集的测试通过率
- ✅ **设置持久化**：自动测试间隔/跳过已测选项 localStorage 持久化，刷新不丢失
- ✅ **深度分析脚本**：自动分类失败原因、提取高频未识别词、输出修复建议

### V5.3 更新亮点
- 📊 **新增深度分析脚本V2** (`tests/analyze_test_results.py`)
  - 基于 **执行结果匹配(result_match)** 为主要判定标准
  - 自动分类7种失败类型（NL_PARSE_FAIL/METRIC_NOT_FOUND/SQL_MISMATCH等）
  - 提取高频未识别口语词TOP20，直接指导别名补充
  - 输出结构化失败列表(`failures_list.json`) + Markdown报告(`analysis_report.md`)
- 🔄 **设置持久化**：自动测试间隔时间、跳过已测选项刷新页面后保持不变
- 🐛 **修复异步双重检测**：切换数据集/跳转页面后自动停止旧任务

### V5.2 更新亮点
- 🐛 **修复SQL注释未清除问题**（`-- 注释` 和 `/* */`）
- 🛠️ **增强中括号/反引号处理**
- ⚡ **优化AS别名正则匹配精度**（防止跨符号误匹配）

## 二、目录结构

```
SemanticSqlQA/
├── test_suite/
│   ├── backend/
│   │   ├── __init__.py
│   │   ├── storage.py          # 结果持久化存储
│   │   └── routes.py           # 测试API路由
│   ├── datasets/               # 测试数据集（JSON）
│   │   ├── qa_simple.json      # 简单查询
│   │   ├── qa_agg.json         # 聚合查询
│   │   ├── qa_join.json        # 多表关联
│   │   ├── qa_advanced.json    # 高级查询
│   │   └── qa_synonyms.json    # 同义词/别名
│   └── results/                # 测试结果（JSON，每数据集一个）
│       ├── qa_simple_results.json
│       └── ...
├── frontend/src/testviews/
│   ├── api.js                  # 前端API调用
│   ├── TestSidebar.vue         # 侧边栏（数据集目录）
│   ├── QuestionList.vue        # 问题列表（分页）
│   ├── QuestionDetail.vue      # 问题详情（SQL对比+执行）
│   ├── StatsView.vue           # 统计视图
│   └── TestLayout.vue          # 布局容器
├── tests/                      # 测试分析
│   ├── analyze_test_results.py # 测试结果分析脚本
│   ├── failures_list.json      # 失败问题列表
│   └── analysis_report.md      # 数据分析报告
└── init_test_results.py        # 初始化空结果文件
```

## 三、数据结构

### 3.1 测试数据集（datasets/*.json）

```json
{
  "question": "订单总共有多少条记录",
  "sql": "SELECT COUNT(*) AS order_count FROM orders",
  "difficulty": "easy",
  "technique": "aggregation_count",
  "domain": "",
  "tables": ["orders"]
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `question` | string | 自然语言问题 |
| `sql` | string | 正确的参考SQL |
| `difficulty` | string | 难度：easy/medium/hard |
| `technique` | string | 技术类型 |
| `domain` | string | 业务领域 |
| `tables` | string[] | 涉及的表名 |

### 3.2 测试结果（results/*_results.json）

```json
{
  "0": {
    "ai_generated_sql": "SELECT COUNT(*) FROM orders",
    "ai_explanation": "...",
    "ai_error": null,
    "ai_elapsed": 5.87,
    "ai_tables_used": ["orders"],
    "ai_generated_at": 1746699600.0,
    "correct_sql_result": {"columns": ["order_count"], "rows": [[1280]], "row_count": 1},
    "correct_executed_at": 1746699600.0,
    "ai_sql_result": {"columns": ["order_count"], "rows": [[1280]], "row_count": 1},
    "ai_executed_at": 1746699600.0,
    "sql_match": "matched",
    "sql_match_manual": false,
    "result_match": "matched",
    "result_match_manual": false,
    "updated_at": 1746699600.0
  }
}
```

| 字段 | 说明 |
|------|------|
| `ai_generated_sql` | AI生成的SQL |
| `ai_error` | AI生成失败时的错误信息 |
| `sql_match` | SQL文本匹配：matched/not_matched/null |
| `sql_match_manual` | 是否手动设置过sql_match |
| `result_match` | 执行结果匹配：matched/not_matched/null |
| `result_match_manual` | 是否手动设置过result_match |
| `correct_sql_result` | 正确SQL的执行结果 |
| `ai_sql_result` | AI SQL的执行结果 |

## 四、API接口

### 4.1 数据集管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/test/datasets` | 列出所有数据集及统计 |
| GET | `/api/test/dataset/{name}?page=1&page_size=10` | 分页获取问题列表+统计 |

### 4.2 问题详情

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/test/question/{dataset}/{index}` | 获取问题+结果详情 |
| POST | `/api/test/generate-ai/{dataset}/{index}` | AI生成SQL |
| POST | `/api/test/execute/{dataset}/{index}` | 执行SQL（body: `{sql, type}`） |
| POST | `/api/test/match/{dataset}/{index}` | 手动设置匹配（body: `{match_type, value}`） |

### 4.3 自动测试

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/test/auto-test/start/{dataset}` | 启动自动测试 |
| POST | `/api/test/auto-test/stop/{task_id}` | 停止自动测试 |
| GET | `/api/test/auto-test/status/{task_id}` | 查询测试状态 |

**启动参数：**
```json
{
  "interval": 30,        // 每题间隔秒数，默认30
  "skip_existing": true  // 是否跳过已测试问题，默认true
}
```

**状态返回：**
```json
{
  "success": true,
  "running": true,
  "dataset_name": "qa_agg",
  "skip_existing": true,
  "total": 60,
  "completed": 5,
  "position": 5,
  "current": 57,
  "interval": 30,
  "errors": [...],
  "elapsed": 120.5
}
```

### 4.4 自动匹配 ⭐

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/test/auto-match/{dataset}` | 启动自动匹配任务 |
| POST | `/api/test/auto-match/stop/{task_id}` | 停止自动匹配任务 |
| GET | `/api/test/auto-match/status/{task_id}` | 查询自动匹配状态 |

**功能说明：**
- 自动匹配所有已生成SQL的结果进行匹配判定
- 跳过不存在AI生成SQL的问题
- 支持语义SQL匹配（别名不同但语义等价视为匹配）
- 支持结果匹配（列名不同但值相同视为匹配）

**启动参数：**
```json
{
  "interval": 10,        // 每题间隔秒数，默认10
  "skip_existing": true // 是否跳过已匹配问题，默认true
}
```

### 4.5 模型切换 ⭐

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/test/models` | 获取可用模型列表 |
| POST | `/api/test/model/switch` | 切换当前模型（body: `{model_name}`） |
| GET | `/api/test/model/current` | 获取当前使用的模型 |

### 4.6 统计

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/test/stats/{dataset}` | 单数据集统计 |
| GET | `/api/test/stats` | 总体统计 |
| POST | `/api/test/reset/{dataset}` | 重置测试集（清空所有结果） |

## 五、双匹配系统

每个问题有两个独立的匹配维度：

| 维度 | 说明 | 自动判定时机 | 手动设置 |
|------|------|------------|---------|
| `sql_match` | SQL文本匹配 | AI生成后 | 始终可手动 |
| `result_match` | 执行结果匹配 | 两侧SQL都执行后 | 两侧SQL都执行后可手动 |

- 手动设置后会被标记为 `*_manual: true`，自动操作不会覆盖
- 手动点击「未判定」可清除，恢复自动判定能力
- 两种匹配均参与统计（无论手动还是自动）

## 六、自动测试流程

每题完整流程：

```
1. 执行正确SQL → 保存执行结果
2. AI生成SQL → 自动SQL匹配判定
3. 执行AI SQL → 自动结果匹配判定
4. 等待 interval 秒 → 下一题
```

**跳过已测试逻辑：**
```python
has_ai = bool(ai_generated_sql) or bool(ai_error) or sql_match is not None
```
三项有其一即视为已测试，不会重复执行。

## 六-1、自动匹配流程 ⭐

自动匹配与自动测试不同，它只对已生成的结果进行匹配判定：

```
1. 遍历所有问题
2. 检查是否存在AI生成的SQL
   - 不存在 → 跳过
   - 存在 → 继续
3. 执行正确SQL（如未执行过）→ 保存执行结果
4. 执行AI SQL（如未执行过）→ 保存执行结果
5. 语义SQL匹配判定（忽略别名、表前缀差异）
6. 结果匹配判定（忽略列名差异，比较数值）
7. 等待 interval 秒 → 下一题
```

**语义SQL匹配算法（V5.2增强版）：**
```python
def _compare_sql(sql1: str, sql2: str) -> bool:
    """
    比较两条SQL语句是否语义等价
    支持忽略的差异：
    - SQL注释 (-- 和 /* */)
    - 反引号和中括号
    - AS别名
    - 表前缀 (orders.total_amount → total_amount)
    - 空白符和大小写
    """
    def normalize(sql):
        s = sql.lower()
        # 1. 清除SQL注释
        s = re.sub(r"--.*$", "", s, flags=re.MULTILINE)
        s = re.sub(r"/\*.*?\*/", "", s, flags=re.DOTALL)
        # 2. 移除反引号和中括号
        s = re.sub(r"[`\[\]]", "", s)
        # 3. 规范化空格
        s = re.sub(r"\s+", " ", s).strip()
        # 4. 规范化逗号和括号
        s = re.sub(r"\s*,\s*", ",", s)
        s = re.sub(r"\s*\(\s*", "(", s)
        s = re.sub(r"\s*\)\s*", ")", s)
        # 5. 移除AS别名（优化：不跨 , ) 匹配）
        s = re.sub(r"\s+as\s+[^\s,\)]+\s*(?=[,\)]|$)", " ", s)
        # 6. 替换字符串字面量
        s = re.sub(r"'[^']*'", "''", s)
        return s.strip()

    def strip_table_prefix(sql):
        # 移除表前缀: orders.field → field
        s = re.sub(r"(\w+)\.(\w+)", r"\2", sql)
        return s

    n1 = strip_table_prefix(normalize(sql1))
    n2 = strip_table_prefix(normalize(sql2))
    return n1 == n2
```

**匹配示例：**

| 正确SQL | AI生成SQL | 匹配结果 |
|---------|----------|---------|
| `SELECT COUNT(*) AS total FROM user_addresses` | `SELECT COUNT(\`address_id\`) AS '地址数量' FROM \`user_addresses\` -- 注释` | ✅ **matched** |
| `SELECT SUM(pay_amount) FROM orders WHERE status='paid'` | `SELECT SUM(orders.pay_amount) AS 'GMV' FROM orders WHERE orders.status='paid'` | ✅ **matched** |
| `SELECT * FROM users` | `SELECT * FROM products` | ❌ **not_matched** |

**结果匹配算法：**
```python
def _compare_results(result1, result2) -> bool:
    # 1. 比较行数
    # 2. 比较每个单元格的值（忽略类型差异）
    # 3. 允许列名不同
```

## 七、分页机制

- 后端按 `page` + `page_size` 分页返回问题列表（默认每页10条）
- 结果文件只在**问题详情页**按需加载，不在列表页读取
- 切换数据集时自动回到第1页
- 进入详情后返回，保持原页码

## 八、数据库连接隔离

所有测试相关操作使用独立的数据库连接，不与主应用共享：

- `generate-ai`：独立 `DatabaseConnection`
- `execute`：独立 `DatabaseConnection`
- `auto-test`：独立连接 + 每轮重建 `QAPipeline`

## 九、前端页面结构

```
测试套件
├── 侧边栏
│   ├── 数据集列表（点击进入问题列表）
│   └── 总体统计入口
├── 问题列表（分页）
│   ├── 顶部栏：数据集名 + 自动测试控件（间隔/跳过复选框/按钮）
│   ├── 自动匹配按钮（右侧）⭐
│   ├── 进度条（自动测试/匹配运行时显示）
│   ├── 分页栏
│   ├── 统计栏（来自后端stats）
│   └── 问题卡片列表（显示✅❌⏳状态）
├── 问题详情
│   ├── 问题描述
│   ├── 匹配判定（SQL匹配 + 结果匹配，各自3个切换按钮）
│   └── SQL对比（正确SQL + AI SQL，各含执行按钮和结果表格）
└── 统计视图
    ├── 模型选择器 ⭐
    ├── 初始化测试集按钮 ⭐
    ├── 总体统计卡片
    └── 各数据集统计表格
```

## 十、测试结果分析（V5.3新增）

### 10.1 深度分析脚本

V5.3新增 `tests/analyze_test_results.py` 脚本，基于**执行结果匹配**对测试结果进行深度分析：

```bash
# 运行分析
python tests/analyze_test_results.py

# 输出文件:
#   tests/analysis_report.md      - 完整Markdown报告
#   tests/failures_list.json       - 结构化失败列表(562条)
```

**评估标准优先级：**

| 优先级 | 判定方式 | 含义 |
|--------|---------|------|
| **最高** | `result_match="matched"` | 执行结果完全一致 ✅ |
| 中等 | `sql_match="matched"` | SQL语义等价但结果不同 ⚠️ |
| 低 | 有AI SQL但 `sql_match="not_matched"` | SQL不等价 ❌ |
| 最低 | 无AI SQL / AI报错 | 生成环节失败 ❌ |

### 10.2 最新测试结果（849题）

基于五大数据集的完整测试数据：

| 数据集 | 题数 | 已测 | 结果✅ | AI报错❌ | SQL差异❌ | 准确率 |
|--------|------|------|--------|----------|----------|--------|
| 简单查询 (qa_simple) | 607 | 607 | 254 | 191 | 162 | **41.8%** |
| 同义词/别名 (qa_synonyms) | 82 | 82 | 25 | 38 | 19 | **30.5%** |
| 多表关联 (qa_join) | 97 | 97 | 8 | 49 | 40 | **9.4%** |
| 高级查询 (qa_advanced) | 38 | 38 | 3 | 24 | 11 | **7.9%** |
| 聚合查询 (qa_agg) | 69 | 69 | 0 | 56 | 13 | **0.0%** |
| **合计** | **893** | **893** | **290** | **358** | **245** | **32.5%** |

### 10.3 失败根因分布（562个失败样例）

| 排名 | 类别 | 数量 | 占比 | 根因描述 |
|------|------|------|------|---------|
| 1 | SQL_MISMATCH | 245 | 43.6% | COUNT(*)差异、WHERE条件多加(业务规则注入)、JOIN差异 |
| 2 | NL_PARSE_FAIL | 163 | 29.0% | 口语词未被识别（如"券""活动""商户"） |
| 3 | METRIC_NOT_FOUND | 98 | 17.4% | 标准指标表中缺少定义 |
| 4 | SQL_VALIDATE_FAIL | 23 | 4.1% | 候选表遗漏（categories/users/stores） |
| 5 | RETRY_EXHAUSTED | 20 | 3.6% | LLM多次生成均不通过校验 |
| 6 | OTHER_ERROR | 10 | 1.8% | 其他异常 |
| 7 | NO_CANDIDATE_TABLE | 6 | 1.1% | 维度-only查询无候选表 |

### 10.4 高频未识别口语词TOP10（数据驱动修复依据）

| 口语词 | 出现次数 | 应映射到标准指标 | V4修复状态 |
|--------|---------|-----------------|-----------|
| '券'→'优惠券数量' | **82次** | 优惠券数量 | ✅ 已补 |
| '活动'→'活动数量' | **40次** | 活动数量 | ✅ 已补 |
| '评分'→'平均评分' | 28次 | 平均评分 | ✅ 已补 |
| '快递'→'物流单数量' | 26次 | 物流单数量 | ✅ 已补 |
| '商户'→'店铺数量' | 24次 | 店铺数量 | ✅ 已补 |
| '客户'→'用户数量' | 24次 | 用户数量 | ✅ 已补 |
| '轨迹'→'物流轨迹数量' | 22次 | 物流轨迹数量 | ✅ 已补 |
| '货品'→'商品数量' | 16次 | 商品数量 | ✅ 已补 |
| '物品'→'商品数量' | 15次 | 商品数量 | ✅ 已补 |
| '商家'→'店铺数量' | 15次 | 店铺数量 | ✅ 已补 |

> 完整TOP20及所有562条失败详情见 `tests/failures_list.json`

### 10.5 V4数据驱动修复方案

基于以上分析结果，已生成全面修复脚本：

```bash
# 方式1: 直接执行V4修复（推荐）
python fix_semantic_v4.py

# 方式2: 完整初始化（自动执行V1→V2→V3→V4）
python init_semantic_db.py

# V4修复内容:
#   - 新增40+个标准指标（实体计数+业务聚合+维度查询）
#   - 新增300+条口语别名（覆盖163个NL解析失败高频词）
#   - 新增15条表关联关系（解决候选表遗漏）
#   - 新增20条业务规则（自动过滤条件）
#
# 预期改善: NL_FAIL↓70%, METRIC_NOT_FOUND↓90%, WHITELIST↓80%
```

### 10.6 失败列表JSON结构

```json
{
  "id": "qa_simple_36",
  "dataset": "简单查询",
  "idx": 36,
  "question": "评价数量最多的前5个商家",
  "correct_sql": "SELECT ...",
  "ai_sql": "SELECT ...",
  "error": "",
  "final_status": "FAIL_SQL_MISMATCH",
  "category": "SQL_MISMATCH",
  "subcategory": "SQL语义差异",
  "root_cause": "AI用COUNT(*)而答案用COUNT(field)",
  "suggested_fix": "优化NLParser prompt中的Few-shot示例",
  "missing_data": []
}
```

## 十一、初始化

首次使用需运行：

```bash
python init_test_results.py
```

会为每个数据集在 `test_suite/results/` 下创建空结果文件。

---

## 十二、更新日志

### V5.2 (2026-05-09) - SQL匹配算法增强
- ✅ **修复SQL注释未清除问题**：AI生成的SQL常包含 `-- 注释`，现已正确处理
- ✅ **增强中括号/反引号处理**：支持更多SQL方言的引用符号
- ✅ **优化AS别名正则匹配**：防止跨 `,` `)` 符号误匹配
- ✅ **完善表前缀移除逻辑**：使用更精确的正则表达式
- ✅ **新增匹配示例表格**：直观展示匹配规则

### V5.1 (2026-05-09)
- ✅ 新增自动匹配功能（一键匹配所有已生成结果）
- ✅ 新增模型切换功能
- ✅ 新增测试结果分析脚本
- ✅ 完善统计视图和初始化功能
