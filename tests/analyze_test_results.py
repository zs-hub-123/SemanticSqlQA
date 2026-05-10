# -*- coding: utf-8 -*-
"""
测试结果深度分析脚本 V2
基于执行结果匹配(result_match)为主，SQL语义匹配(sql_match)为辅

评估标准优先级:
  1. result_match="matched" → ✅ 执行结果一致（最高可信度）
  2. sql_match="matched" but result_match≠"matched" → ⚠️ SQL等价但结果不同
  3. sql_match="not_matched" + 有AI SQL → ❌ SQL不等价
  4. 无AI SQL / AI报错 → ❌ 生成失败

输出:
  tests/analysis_report.md   - 完整分析报告(Markdown)
  tests/failures_list.json    - 结构化失败列表(JSON)
"""

import json
import os
import re
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent
RESULTS_DIR = BASE_DIR / "test_suite" / "results"
DATASETS_DIR = BASE_DIR / "test_suite" / "datasets"
OUTPUT_DIR = BASE_DIR / "tests"
OUTPUT_DIR.mkdir(exist_ok=True)

DATASETS = ["qa_simple", "qa_agg", "qa_join", "qa_advanced", "qa_synonyms"]
DATASET_NAMES = {
    "qa_simple": "简单查询", "qa_agg": "聚合查询",
    "qa_join": "多表关联", "qa_advanced": "高级查询",
    "qa_synonyms": "同义词/别名"
}


def load_json(p):
    with open(p, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(data, p):
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def classify_error_deep(error_msg: str, question: str, ai_sql: str,
                        correct_sql: str) -> dict:
    diag = {"category": "", "subcategory": "", "root_cause": "",
            "suggested_fix": "", "missing_data": []}
    err_lower = (error_msg or "").lower()

    if '无法理解' in error_msg or ('无法理解' in error_msg[:20]):
        diag["category"] = "NL_PARSE_FAIL"
        diag["subcategory"] = "模型无法提取指标/维度"
        keywords = extract_unrecognized_terms(question)
        if keywords:
            diag["root_cause"] = f"口语词未被识别: {', '.join(keywords)}"
            diag["missing_data"] = keywords
            diag["suggested_fix"] = f"在spoken_aliases中添加映射: {keywords} → 对应标准指标"
        else:
            diag["root_cause"] = "问题过于口语化或超出词汇表范围"
            diag["suggested_fix"] = "增加Few-shot示例或扩展标准词汇表"

    elif 'mql校验失败' in err_lower and '不存在' in error_msg:
        diag["category"] = "METRIC_NOT_FOUND"
        m = re.search(r"指标\s*'([^']+)'", error_msg)
        missing_metric = m.group(1) if m else "未知指标"
        diag["missing_data"].append(missing_metric)
        diag["root_cause"] = f"标准指标表中缺少: '{missing_metric}'"
        diag["suggested_fix"] = f"在standard_metrics_dimensions中插入 '{missing_metric}' 指标定义"

    elif 'mql校验失败' in err_lower:
        diag["category"] = "MQL_VALIDATE_FAIL"
        diag["root_cause"] = error_msg[:100]
        diag["suggested_fix"] = "检查MQL校验规则是否过严，考虑放宽或增加两步聚合策略"

    elif '未找到相关的业务表' in error_msg or 'no candidate' in err_lower:
        diag["category"] = "NO_CANDIDATE_TABLE"
        diag["root_cause"] = "find_candidate_tables()返回空集合"
        diag["suggested_fix"] = "检查指标/维度的physical_table映射是否正确"

    elif 'sql校验失败' in err_lower:
        diag["category"] = "SQL_VALIDATE_FAIL"
        if '非法表名' in error_msg or '不支持的表' in error_msg:
            m = re.search(r"非法表名:\s*(\w+)", error_msg)
            bad_table = m.group(1) if m else "?"
            diag["subcategory"] = "使用了白名单外的表"
            diag["root_cause"] = f"候选表列表遗漏了: {bad_table}"
            diag["missing_data"].append(bad_table)
            diag["suggested_fix"] = f"在table_relations中补充 {bad_table} 的关联关系"
        elif '非法字段' in error_msg:
            m = re.search(r"非法字段[::]\s*(\w+\.?\w*)", error_msg)
            bad_field = m.group(1) if m else "?"
            diag["subcategory"] = "使用了不存在的字段"
            diag["root_cause"] = f"AI生成了不存在的字段: {bad_field}"
            diag["suggested_fix"] = "检查TableSchemaService的表结构定义是否完整"
        else:
            diag["subcategory"] = "其他SQL校验错误"
            diag["root_cause"] = error_msg[:100]

    elif '多次尝试后未能生成' in error_msg or 'retry' in err_lower:
        diag["category"] = "RETRY_EXHAUSTED"
        diag["root_cause"] = "LLM多次生成均未通过校验"
        diag["suggested_fix"] = "检查MQL约束是否与候选表冲突，或降低约束严格度"

    elif ai_sql and not error_msg:
        diag["category"] = "SQL_MISMATCH"
        diff = analyze_sql_diff(correct_sql, ai_sql)
        diag.update(diff)

    else:
        diag["category"] = "OTHER_ERROR"
        diag["root_cause"] = (error_msg or "未知")[:120]
        diag["suggested_fix"] = "检查具体错误日志"

    return diag


def extract_unrecognized_terms(question: str) -> list:
    terms_map = {
        '商户': '店铺数量', '商家': '店铺数量', '卖家': '店铺数量',
        '客户': '用户数量', '买家': '用户数量', '会员': '用户数量',
        '货品': '商品数量', '物品': '商品数量', '产品': '商品数量',
        '券': '优惠券数量', '活动': '活动数量', '快递': '物流单数量',
        '地址': '地址数量', '类目': '类目名称', '品类': '类目名称',
        '评价': '店铺评分数量', '评分': '平均评分', 'DSR': 'DSR描述分',
        '轨迹': '物流轨迹数量', '明细': '订单明细数量', '流水': '支付笔数',
        '属性': 'SKU数量', '规格': 'SKU数量', 'SKU': 'SKU数量',
    }
    found = []
    for term, target in terms_map.items():
        if term in question:
            found.append(f"'{term}'→'{target}'")
    return found


def analyze_sql_diff(correct: str, ai: str) -> dict:
    c_lower = correct.lower()
    a_lower = ai.lower()
    diffs = []
    if 'count(*)' in a_lower and 'count(*)' not in c_lower:
        diffs.append("AI用COUNT(*)而答案用COUNT(field)")
    elif 'count(distinct' in a_lower and 'count(distinct' not in c_lower:
        diffs.append("AI用COUNT(DISTINCT)而答案用普通COUNT")
    if 'join' in a_lower and 'join' not in c_lower:
        diffs.append("AI多用了JOIN")
    elif 'join' not in a_lower and 'join' in c_lower:
        diffs.append("AI缺少必要的JOIN")
    where_in_ai = bool(re.search(r'\bwhere\b', a_lower))
    where_in_correct = bool(re.search(r'\bwhere\b', c_lower))
    if where_in_ai and not where_in_correct:
        diffs.append("AI多加了WHERE条件(可能是业务规则自动注入)")
    elif not where_in_ai and where_in_correct:
        diffs.append("AI缺少WHERE条件")
    group_in_ai = bool(re.search(r'\bgroup by\b', a_lower))
    group_in_correct = bool(re.search(r'\bgroup by\b', c_lower))
    if group_in_ai != group_in_correct:
        diffs.append(f"GROUP BY不一致(AI:{group_in_ai}, 答案:{group_in_correct})")
    agg_funcs = ['sum(', 'avg(', 'min(', 'max(', 'count(']
    for func in agg_funcs:
        if func in a_lower and func not in c_lower:
            diffs.append(f"AI多用了{func.upper()}聚合")
        elif func not in a_lower and func in c_lower:
            diffs.append(f"AI缺少{func.upper()}聚合")
    if a_lower.count('from') > c_lower.count('from'):
        diffs.append("AI用了更多FROM子句(多余表)")
    if not diffs:
        diffs.append("SQL结构差异(具体字段名/别名/排序等)")
    return {
        "subcategory": "SQL语义差异",
        "root_cause": "; ".join(diffs),
        "suggested_fix": (
            "优化NLParser prompt中的Few-shot示例; "
            "或在MQL约束中明确指定聚合方式和JOIN策略"
        )
    }


def main():
    print("=" * 70)
    print("  SemanticSqlQA 测试结果深度分析 V2")
    print("  基于执行结果匹配(result_match)为主")
    print("=" * 70)
    print(f"  分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    all_items = []
    stats = defaultdict(int)
    by_dataset = defaultdict(lambda: defaultdict(int))
    by_category = Counter()
    by_subcategory = Counter()
    missing_metrics = set()
    missing_tables = set()
    unrecognized_terms_counter = Counter()

    for ds_key in DATASETS:
        res_file = RESULTS_DIR / f"{ds_key}_results.json"
        data_file = DATASETS_DIR / f"{ds_key}.json"
        if not res_file.exists():
            print(f"\n  [SKIP] {ds_key}: 结果文件不存在")
            continue
        results = load_json(res_file)
        dataset = load_json(data_file)
        total = len(dataset)
        ds_stats = {"total": total, "tested": 0, "result_pass": 0,
                     "sql_pass": 0, "result_fail": 0, "ai_error": 0, "not_tested": 0}
        print(f"\n  [{DATASET_NAMES.get(ds_key, ds_key)}] ({ds_key})")
        print(f"    总题数: {total}")
        for idx in range(total):
            key = str(idx)
            r = results.get(key, {})
            q_item = dataset[idx]
            question = q_item.get("question", "")
            correct_sql = q_item.get("sql", "") or ""
            ai_sql = r.get("ai_generated_sql", "") or ""
            ai_error = r.get("ai_error", "") or ""
            sql_match = r.get("sql_match", "") or ""
            result_match = r.get("result_match", "") or ""
            has_ai = bool(ai_sql) or bool(ai_error)
            if not has_ai:
                ds_stats["not_tested"] += 1
                continue
            ds_stats["tested"] += 1
            item = {
                "id": f"{ds_key}_{idx}", "dataset": ds_key,
                "dataset_name": DATASET_NAMES.get(ds_key, ds_key),
                "idx": idx, "question": question,
                "correct_sql_snip": correct_sql[:150],
                "ai_sql_snip": ai_sql[:200],
                "ai_error_snip": (ai_error or "")[:150],
                "sql_match": sql_match, "result_match": result_match,
                "difficulty": q_item.get("difficulty", ""),
                "technique": q_item.get("technique", ""),
                "domain": q_item.get("domain", ""),
                "final_status": "", "category": "",
                "subcategory": "", "root_cause": "",
                "suggested_fix": "", "missing_data": [],
            }
            if result_match == "matched":
                item["final_status"] = "PASS_RESULT"
                ds_stats["result_pass"] += 1
                stats["total_pass"] += 1
                by_dataset[ds_key]["pass"] += 1
            elif sql_match == "matched":
                item["final_status"] = "PASS_SQL_ONLY"
                ds_stats["sql_pass"] += 1
                stats["total_pass_sql_only"] += 1
                item["root_cause"] = "SQL等价但执行结果不同(可能因业务规则注入)"
            elif ai_error:
                item["final_status"] = "FAIL_AI_ERROR"
                ds_stats["ai_error"] += 1
                stats["total_fail_ai_error"] += 1
                diag = classify_error_deep(ai_error, question, ai_sql, correct_sql)
                item.update(diag)
                by_category[diag["category"]] += 1
                if diag.get("subcategory"):
                    by_subcategory[diag["subcategory"]] += 1
                for md in item["missing_data"]:
                    if any(kw in md.lower() for kw in ['指标', 'metric']):
                        missing_metrics.add(md)
                    if any(kw in md.lower() for kw in ['表', 'table']):
                        missing_tables.add(md)
            elif ai_sql:
                item["final_status"] = "FAIL_SQL_MISMATCH"
                ds_stats["result_fail"] += 1
                stats["total_fail_mismatch"] += 1
                diag = classify_error_deep("", question, ai_sql, correct_sql)
                item.update(diag)
                by_category[diag["category"]] += 1
                if diag.get("subcategory"):
                    by_subcategory[diag["subcategory"]] += 1
            else:
                item["final_status"] = "FAIL_NO_SQL"
                ds_stats["ai_error"] += 1
            all_items.append(item)
            status_icon = "✅" if "PASS" in item["final_status"] else "❌"
            if "FAIL" in item["final_status"]:
                cat_tag = item.get("category", "?")[:12]
                print(f"    #{idx:3d} {status_icon} [{cat_tag}] {question[:60]}")
        by_dataset[ds_key] = ds_stats
        rate = (ds_stats["result_pass"] + ds_stats["sql_pass"]) / max(ds_stats["tested"], 1) * 100
        print(f"    已测试: {ds_stats['tested']}/{total} | "
              f"结果通过: {ds_stats['result_pass']} | SQL通过: {ds_stats['sql_pass']} | 准确率: {rate:.1f}%")

    fail_items = [it for it in all_items if "FAIL" in it["final_status"]]
    tested_total = sum(d["tested"] for d in by_dataset.values())
    print("\n" + "=" * 70)
    print("  总体统计（以执行结果匹配为准）")
    print("=" * 70)
    print(f"  总题数:       {len(all_items)} | 已测试: {tested_total}")
    print(f"  结果匹配通过: {stats.get('total_pass', 0)} ({stats.get('total_pass',0)/max(tested_total,1)*100:.1f}%)")
    print(f"  AI生成失败:   {stats.get('total_fail_ai_error', 0)} ({stats.get('total_fail_ai_error',0)/max(tested_total,1)*100:.1f}%)")
    print(f"  SQL不匹配:   {stats.get('total_fail_mismatch', 0)} ({stats.get('total_fail_mismatch',0)/max(tested_total,1)*100:.1f}%)")
    print(f"  准确率(宽松): {(stats.get('total_pass',0)+stats.get('total_pass_sql_only',0))/max(tested_total,1)*100:.1f}%")
    print(f"\n  失败分类:")
    for cat, cnt in by_category.most_common():
        pct = cnt / max(len(fail_items), 1) * 100
        print(f"    {cat}: {cnt} ({pct:.1f}%)")

    for it in fail_items:
        terms = extract_unrecognized_terms(it["question"])
        for t in terms:
            unrecognized_terms_counter[t] += 1

    print(f"\n  高频未识别口语词Top20:")
    for term, cnt in unrecognized_terms_counter.most_common(20):
        print(f"    {term}: 出现{cnt}次")

    failures_output = []
    for it in fail_items:
        failures_output.append({
            "id": it["id"], "dataset": it["dataset_name"], "idx": it["idx"],
            "question": it["question"], "difficulty": it["difficulty"],
            "correct_sql": it["correct_sql_snip"],
            "ai_sql": it["ai_sql_snip"], "error": it["ai_error_snip"],
            "final_status": it["final_status"], "category": it["category"],
            "subcategory": it["subcategory"], "root_cause": it["root_cause"],
            "suggested_fix": it["suggested_fix"], "missing_data": it["missing_data"],
        })
    save_json(failures_output, OUTPUT_DIR / "failures_list.json")
    print(f"\n  失败列表已保存: {OUTPUT_DIR / 'failures_list.json'} ({len(failures_output)}条)")

    report = generate_report(all_items, fail_items, stats, by_dataset,
                            by_category, by_subcategory, missing_metrics,
                            missing_tables, unrecognized_terms_counter)
    with open(OUTPUT_DIR / "analysis_report.md", 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"  分析报告已保存: {OUTPUT_DIR / 'analysis_report.md'}")
    print("\n" + "=" * 70)
    print("  分析完成!")
    print("=" * 70)


def generate_report(all_items, fails, stats, by_ds, by_cat, by_subcat,
                      missing_metrics, missing_tables, alias_counts):
    tested_total = sum(d["tested"] for d in by_ds.values())
    report = f"""# SemanticSqlQA 测试结果深度分析报告

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**评估标准**: 以 **result_match(执行结果匹配)** 为主要判定依据

---

## 一、总体概览

| 指标 | 数值 |
|------|------|
| 总题数 | {len(all_items)} |
| 已测试 | {tested_total} |
| **结果匹配通过** | **{stats.get('total_pass', 0)}** ({stats.get('total_pass',0)/max(tested_total,1)*100:.1f}%) |
| AI生成失败 | {stats.get('total_fail_ai_error', 0)} ({stats.get('total_fail_ai_error',0)/max(tested_total,1)*100:.1f}%) |
| SQL不匹配 | {stats.get('total_fail_mismatch', 0)} ({stats.get('total_fail_mismatch',0)/max(tested_total,1)*100:.1f}%) |

### 各数据集详情

| 数据集 | 总数 | 已测 | 结果✅ | AI报错❌ | SQL差异❌ | 准确率 |
|--------|------|------|--------|----------|----------|--------|
"""
    for ds_key, ds_name in DATASET_NAMES.items():
        d = by_ds.get(ds_key, {})
        t = d.get("total", 0); te = d.get("tested", 0)
        rp = d.get("result_pass", 0); ae = d.get("ai_error", 0)
        rf = d.get("result_fail", 0)
        rate = (rp + d.get("sql_pass", 0)) / max(te, 1) * 100
        report += f"| {ds_name} | {t} | {te} | {rp} | {ae} | {rf} | {rate:.1f}% |\n"

    report += f"""

## 二、失败分类详情

| 排名 | 类别 | 数量 | 占比 |
|------|------|------|------|
"""
    for i, (cat, cnt) in enumerate(by_cat.most_common(), 1):
        pct = cnt / max(len(fails), 1) * 100
        report += f"| {i} | {cat} | {cnt} | {pct:.1f}% |\n"

    report += f"""

## 三、数据驱动修复建议

### 高频未识别口语词Top20

| 口语词 | 出现次数 |
|--------|---------|
"""
    for term, cnt in alias_counts.most_common(20):
        report += f"| {term} | {cnt}次 |\n"

    report += f"""

> **修复方式**: 在 `fix_semantic_v4.py` 的 Part 2 中 INSERT INTO spoken_aliases

### 改进优先级

#### P0 - 立即修复
| 改进项 | 影响数 | 预期效果 |
|--------|-------|---------|
| 补充高频口语别名 | ~{by_cat.get('NL_PARSE_FAIL', 0)} | NL_PARSE_FAIL↓70% |
| 补充缺失标准指标 | ~{by_cat.get('METRIC_NOT_FOUND', 0)} | METRIC_NOT_FOUND↓90% |
| 补充表关联关系 | ~{by_cat.get('SQL_VALIDATE_FAIL', 0)+by_cat.get('NO_CANDIDATE_TABLE', 0)} | WHITELIST↓80% |

#### P1 - 短期优化
| 改进项 | 影响数 | 预期效果 |
|--------|-------|---------|
| COUNT(*)策略统一 | ~{by_cat.get('SQL_MISMATCH', 0)*30//100} | SQL_MISMATCH↓30% |
| Few-shot增强 | ~{by_cat.get('NL_PARSE_FAIL', 0)*40//100} | 边界case↑ |

## 四、行动清单

```bash
python fix_semantic_v4.py      # V4全面修复
python init_semantic_db.py     # 或完整初始化(V1→V4)
python start.py               # 重启服务
# 前端自动测试验证效果
```

---
*由 tests/analyze_test_results.py 自动生成*
"""
    return report


if __name__ == "__main__":
    main()
