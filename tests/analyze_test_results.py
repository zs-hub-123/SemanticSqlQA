# -*- coding: utf-8 -*-
"""
测试结果分析脚本
功能：
1. 加载所有测试结果和数据集
2. 分析失败问题及原因
3. 生成失败列表(JSON)和分析报告(Markdown)
"""

import json
import os
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime

SCRIPT_DIR = Path(__file__).parent.parent / "test_suite"
RESULTS_DIR = SCRIPT_DIR / "results"
DATASETS_DIR = SCRIPT_DIR / "datasets"
OUTPUT_DIR = SCRIPT_DIR.parent / "tests"
OUTPUT_DIR.mkdir(exist_ok=True)

DATASET_FILES = {
    "qa_simple": "简单查询",
    "qa_agg": "聚合查询",
    "qa_join": "多表关联",
    "qa_advanced": "高级查询",
    "qa_synonyms": "同义词/别名"
}


def load_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(data, filepath):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def analyze_error_message(error_msg):
    """分析错误消息，提取失败原因"""
    if not error_msg:
        return "未知错误"

    error_lower = error_msg.lower()

    if "mql校验失败" in error_lower or "指标" in error_msg and "不存在" in error_msg:
        if "用户数量" in error_msg:
            return "MQL校验失败: 缺少'用户数量'指标定义"
        if "账户余额" in error_msg:
            return "MQL校验失败: 缺少'账户余额'指标定义"
        if "gmv" in error_lower or "成交总额" in error_msg:
            return "MQL校验失败: 缺少'GMV成交总额'指标定义"
        if "商品数量" in error_msg:
            return "MQL校验失败: 缺少'商品数量'指标定义"
        if "订单数量" in error_msg:
            return "MQL校验失败: 缺少'订单数量'指标定义"
        return f"MQL校验失败: 指标不存在"

    if "sql校验失败" in error_lower:
        if "非法字段" in error_msg:
            if "users.province" in error_lower or "user_province" in error_lower:
                return "SQL校验失败: users表无province字段(需通过user_addresses关联)"
            if "shipment_tracks.status" in error_lower:
                return "SQL校验失败: shipment_tracks表无status字段"
            return "SQL校验失败: 使用了不存在或未授权的字段"
        if "不支持的表" in error_msg:
            return "SQL校验失败: 使用了不支持的表"
        return "SQL校验失败: SQL语法或语义错误"

    if "execute error" in error_lower or "sql执行错误" in error_lower:
        if "unknown column" in error_lower:
            return "SQL执行错误: 列不存在"
        if "table" in error_lower and "doesn't exist" in error_lower:
            return "SQL执行错误: 表不存在"
        if "syntax" in error_lower:
            return "SQL执行错误: SQL语法错误"
        return "SQL执行错误: 执行失败"

    if "api" in error_lower and ("error" in error_lower or "failed" in error_lower):
        return "API调用失败"

    if "timeout" in error_lower:
        return "请求超时"

    return f"其他错误: {error_msg[:50]}"


def analyze_sql_mismatch(correct_sql, ai_sql, result):
    """分析SQL不匹配的原因"""
    if not ai_sql:
        return "AI未生成SQL"

    ai_lower = ai_sql.lower()
    correct_lower = correct_sql.lower()

    if "join" in ai_lower and "join" not in correct_lower:
        return "错误使用JOIN关联"

    if "join" not in ai_lower and "join" in correct_lower:
        return "缺少必要的JOIN关联"

    if "where" in ai_lower and "where" not in correct_lower:
        return "错误添加了WHERE条件"

    if "where" not in ai_lower and "where" in correct_lower:
        return "缺少必要的WHERE条件"

    if "group by" in ai_lower and "group by" not in correct_lower:
        return "错误添加了GROUP BY"

    if "group by" not in ai_lower and "group by" in correct_lower:
        return "缺少必要的GROUP BY"

    if "order by" in ai_lower and "order by" not in correct_lower:
        return "错误添加了ORDER BY"

    if "count" in ai_lower and "count" not in correct_lower:
        return "错误使用COUNT聚合"

    if "sum" in ai_lower and "sum" not in correct_lower:
        return "错误使用SUM聚合"

    if "avg" in ai_lower and "avg" not in correct_lower:
        return "错误使用AVG聚合"

    if ai_lower.count("from") > correct_lower.count("from"):
        return "使用了多余的FROM子句"

    if ai_lower.count("select") > correct_lower.count("select"):
        return "使用了多余的SELECT"

    return "SQL语义差异"


def analyze_result_mismatch(correct_result, ai_result):
    """分析结果不匹配的原因"""
    if not ai_result:
        return "AI未执行SQL"

    correct_rows = correct_result.get("rows", [])
    ai_rows = ai_result.get("rows", [])

    if len(ai_rows) != len(correct_rows):
        return f"结果行数不一致: 期望{len(correct_rows)}行, 实际{len(ai_rows)}行"

    for i, (c, a) in enumerate(zip(correct_rows, ai_rows)):
        if c != a:
            return f"结果数据不一致: 第{i+1}行数据不同"

    return "结果数值略有差异"


def classify_failure(failure_type, result_item, dataset_item, question_idx, dataset_name):
    """分类失败问题"""
    issue = {
        "id": f"{dataset_name}_{question_idx}",
        "dataset": DATASET_FILES.get(dataset_name, dataset_name),
        "dataset_key": dataset_name,
        "question_index": question_idx,
        "question": dataset_item.get("question", ""),
        "difficulty": dataset_item.get("difficulty", ""),
        "technique": dataset_item.get("technique", ""),
        "domain": dataset_item.get("domain", ""),
        "tables": dataset_item.get("tables", []),
        "correct_sql": dataset_item.get("sql", ""),
        "ai_sql": result_item.get("ai_generated_sql", ""),
        "error_message": result_item.get("ai_error", ""),
        "failure_type": failure_type,
        "failure_reason": ""
    }

    if failure_type == "sql生成失败":
        issue["failure_reason"] = analyze_error_message(result_item.get("ai_error", ""))
    elif failure_type == "sql不匹配":
        issue["failure_reason"] = analyze_sql_mismatch(
            dataset_item.get("sql", ""),
            result_item.get("ai_generated_sql", ""),
            result_item
        )
    elif failure_type == "结果不匹配":
        issue["failure_reason"] = analyze_result_mismatch(
            result_item.get("correct_sql_result"),
            result_item.get("ai_sql_result")
        )

    return issue


def generate_report(all_failures, stats, by_dataset, by_type, by_reason):
    """生成Markdown分析报告"""

    report = f"""# SQL智能问答系统 测试结果分析报告

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 📊 总体概览

| 指标 | 数值 |
|------|------|
| 总测试题数 | {stats['total_questions']} |
| 成功题数 | {stats['success_count']} |
| 失败题数 | {stats['failure_count']} |
| 成功率 | {stats['success_rate']:.1f}% |
| SQL匹配率 | {stats['sql_match_rate']:.1f}% |
| 结果匹配率 | {stats['result_match_rate']:.1f}% |

---

## 📈 数据集维度分析

| 数据集 | 总题数 | 成功 | 失败 | 成功率 | SQL匹配率 | 结果匹配率 |
|--------|--------|------|------|--------|-----------|------------|
"""

    for ds_key, ds_name in DATASET_FILES.items():
        if ds_key in by_dataset:
            d = by_dataset[ds_key]
            report += f"| {ds_name} | {d['total']} | {d['success']} | {d['failure']} | {d['success_rate']:.1f}% | {d['sql_match_rate']:.1f}% | {d['result_match_rate']:.1f}% |\n"

    report += f"""

---

## 🔍 失败类型分布

| 失败类型 | 数量 | 占比 |
|----------|------|------|
| SQL生成失败 | {by_type.get('sql生成失败', 0)} | {by_type.get('sql生成失败', 0)/max(stats['failure_count'],1)*100:.1f}% |
| SQL不匹配 | {by_type.get('sql不匹配', 0)} | {by_type.get('sql不匹配', 0)/max(stats['failure_count'],1)*100:.1f}% |
| 结果不匹配 | {by_type.get('结果不匹配', 0)} | {by_type.get('结果不匹配', 0)/max(stats['failure_count'],1)*100:.1f}% |

---

## ⚠️ 失败原因Top10

| 排名 | 失败原因 | 数量 |
|------|----------|------|
"""

    reason_counts = sorted(by_reason.items(), key=lambda x: -x[1])
    for i, (reason, count) in enumerate(reason_counts[:10], 1):
        report += f"| {i} | {reason} | {count} |\n"

    report += f"""

---

## 🎯 难度维度分析

| 难度 | 总数 | 成功 | 失败 | 成功率 |
|------|------|------|------|--------|
"""

    diff_stats = defaultdict(lambda: {"total": 0, "success": 0})
    for item in all_failures:
        diff = item.get("difficulty", "unknown")
        diff_stats[diff]["total"] += 1
        if item.get("sql_match") == "matched" or item.get("result_match") == "matched":
            diff_stats[diff]["success"] += 1

    for diff in ["easy", "medium", "hard"]:
        d = diff_stats[diff]
        rate = d["success"] / max(d["total"], 1) * 100
        report += f"| {diff} | {d['total']} | {d['success']} | {d['total']-d['success']} | {rate:.1f}% |\n"

    report += f"""

---

## 📋 领域分布分析

| 领域 | 失败数 | 主要失败原因 |
|------|--------|--------------|
"""

    domain_stats = defaultdict(lambda: {"count": 0, "reasons": []})
    for item in all_failures:
        domain = item.get("domain", "未知")
        domain_stats[domain]["count"] += 1
        domain_stats[domain]["reasons"].append(item.get("failure_reason", ""))

    for domain, data in sorted(domain_stats.items(), key=lambda x: -x[1]["count"]):
        reason_counter = Counter(data["reasons"])
        top_reason = reason_counter.most_common(1)[0][0] if reason_counter else "未知"
        report += f"| {domain} | {data['count']} | {top_reason} |\n"

    report += f"""

---

## 🛠️ 改进建议

### 高优先级 (立即修复)

#### 1. 补充语义层指标定义
**问题**: MQL校验失败是主要失败原因之一
**影响**: {by_reason.get('MQL校验失败: 指标不存在', 0)} 处失败
**建议**:
- 在 `standard_metrics_dimensions` 表中添加缺失的指标:
  - `用户数量` (COUNT users.user_id)
  - `账户余额` (SUM users.balance)
  - `商品数量` (COUNT products.product_id)
- 在 `spoken_aliases` 表中添加口语别名:
  - "买家" -> 用户数量
  - "客户" -> 用户数量
  - "商品" -> 商品数量

#### 2. 修复JOIN路径缺失问题
**问题**: 多表关联查询失败
**影响**: {by_reason.get('SQL校验失败: 使用了不支持的表', 0)} 处失败
**建议**:
- 在 `table_relations` 表中补充表关联关系:
  - `users` -> `user_addresses` (用户与地址)
  - `orders` -> `shipments` (订单与物流)
  - `orders` -> `order_items` (订单与明细)

#### 3. 修复字段映射错误
**问题**: AI使用了不存在的字段
**影响**: {by_reason.get('SQL执行错误: 列不存在', 0)} 处失败
**建议**:
- 在 `table_metadata` 表中明确标注每个表的可用字段
- 在NL Parser的prompt中强调只使用白名单字段

### 中优先级 (短期内修复)

#### 4. 优化业务规则应用
**问题**: 订单统计未排除已取消订单
**建议**:
- 为订单相关指标配置 `default_filter = "order_status != 'cancelled'"`
- 在 `business_rules` 表中添加过滤规则

#### 5. 增强SQL归一化匹配逻辑
**问题**: 部分语义等价的SQL被判定为不匹配
**建议**:
- 改进 `SELECT *` vs `SELECT col1, col2` 的匹配
- 处理 `IN (1,2,3)` vs `= 1 OR = 2 OR = 3` 的等价转换

#### 6. 添加更多口语别名
**问题**: 特定领域的口语表达无法识别
**建议**:
- "女性用户" -> 用户数量 + gender='F' 过滤
- "已完成订单" -> 订单数量 + status='completed' 过滤

### 低优先级 (长期优化)

#### 7. 扩展测试数据集
- 增加更多边界条件测试
- 添加复杂多表JOIN场景
- 增加NULL值处理测试

#### 8. 优化错误提示
- 将通用错误消息具体化
- 提供修复建议而非仅报错

---

## 📝 详细失败列表

详见: `tests/failures_list.json`

---

*报告自动生成 by Test Analysis Script*
"""

    return report


def main():
    print("=" * 60)
    print("  SQL智能问答系统 - 测试结果分析")
    print("=" * 60)

    all_failures = []
    stats = {
        "total_questions": 0,
        "success_count": 0,
        "failure_count": 0,
        "success_rate": 0,
        "sql_match_count": 0,
        "sql_match_rate": 0,
        "result_match_count": 0,
        "result_match_rate": 0,
    }

    by_dataset = defaultdict(lambda: {
        "total": 0, "success": 0, "failure": 0,
        "sql_match": 0, "result_match": 0,
        "success_rate": 0, "sql_match_rate": 0, "result_match_rate": 0
    })

    by_type = Counter()
    by_reason = Counter()
    by_difficulty = defaultdict(lambda: {"total": 0, "success": 0})

    for dataset_key, dataset_name in DATASET_FILES.items():
        results_file = RESULTS_DIR / f"{dataset_key}_results.json"
        dataset_file = DATASETS_DIR / f"{dataset_key}.json"

        if not results_file.exists() or not dataset_file.exists():
            print(f"  [SKIP] {dataset_name}: 文件不存在")
            continue

        try:
            results = load_json(results_file)
            dataset = load_json(dataset_file)
        except Exception as e:
            print(f"  [ERROR] {dataset_name}: {e}")
            continue

        ds_total = len(dataset)
        ds_success = 0
        ds_sql_match = 0
        ds_result_match = 0

        print(f"\n  [{dataset_name}]")
        print(f"    总题数: {ds_total}")

        for idx in range(ds_total):
            result_item = results.get(str(idx), {})
            dataset_item = dataset[idx] if idx < len(dataset) else {}

            by_dataset[dataset_key]["total"] += 1
            stats["total_questions"] += 1

            ai_sql = result_item.get("ai_generated_sql", "")
            ai_error = result_item.get("ai_error", "")
            sql_match = result_item.get("sql_match", "")
            result_match = result_item.get("result_match", "")

            difficulty = dataset_item.get("difficulty", "unknown")
            by_difficulty[difficulty]["total"] += 1

            is_success = (sql_match == "matched" or result_match == "matched")
            is_sql_matched = sql_match == "matched"
            is_result_matched = result_match == "matched"

            if is_success:
                ds_success += 1
                stats["success_count"] += 1
                by_difficulty[difficulty]["success"] += 1

            if is_sql_matched:
                ds_sql_match += 1
                stats["sql_match_count"] += 1

            if is_result_matched:
                ds_result_match += 1
                stats["result_match_count"] += 1

            failure_type = None
            if not ai_sql and ai_error:
                failure_type = "sql生成失败"
            elif sql_match == "not_matched" and ai_sql:
                failure_type = "sql不匹配"
            elif result_match == "not_matched":
                failure_type = "结果不匹配"

            if failure_type:
                failure_item = classify_failure(
                    failure_type, result_item, dataset_item, idx, dataset_key
                )
                all_failures.append(failure_item)
                by_type[failure_type] += 1
                by_reason[failure_item["failure_reason"]] += 1
                by_dataset[dataset_key]["failure"] += 1

                print(f"    [{idx}] ❌ {failure_type}: {failure_item['failure_reason'][:40]}...")

        by_dataset[dataset_key]["success"] = ds_success
        by_dataset[dataset_key]["sql_match"] = ds_sql_match
        by_dataset[dataset_key]["result_match"] = ds_result_match
        by_dataset[dataset_key]["success_rate"] = ds_success / max(ds_total, 1) * 100
        by_dataset[dataset_key]["sql_match_rate"] = ds_sql_match / max(ds_total, 1) * 100
        by_dataset[dataset_key]["result_match_rate"] = ds_result_match / max(ds_total, 1) * 100

        print(f"    成功: {ds_success}, SQL匹配: {ds_sql_match}, 结果匹配: {ds_result_match}")

    stats["failure_count"] = len(all_failures)
    stats["success_rate"] = stats["success_count"] / max(stats["total_questions"], 1) * 100
    stats["sql_match_rate"] = stats["sql_match_count"] / max(stats["total_questions"], 1) * 100
    stats["result_match_rate"] = stats["result_match_count"] / max(stats["total_questions"], 1) * 100

    print("\n" + "=" * 60)
    print("  总体统计")
    print("=" * 60)
    print(f"  总题数: {stats['total_questions']}")
    print(f"  成功数: {stats['success_count']}")
    print(f"  失败数: {stats['failure_count']}")
    print(f"  成功率: {stats['success_rate']:.1f}%")
    print(f"  SQL匹配率: {stats['sql_match_rate']:.1f}%")
    print(f"  结果匹配率: {stats['result_match_rate']:.1f}%")

    failures_file = OUTPUT_DIR / "failures_list.json"
    save_json(all_failures, failures_file)
    print(f"\n  失败列表已保存: {failures_file}")

    report = generate_report(all_failures, stats, by_dataset, by_type, by_reason)
    report_file = OUTPUT_DIR / "analysis_report.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"  分析报告已保存: {report_file}")

    print("\n" + "=" * 60)
    print("  分析完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
