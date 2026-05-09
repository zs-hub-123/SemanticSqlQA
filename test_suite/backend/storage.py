import json
import os
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

BASE_DIR = Path(__file__).parent.parent
DATASETS_DIR = BASE_DIR / "datasets"
RESULTS_DIR = BASE_DIR / "results"

DATASET_FILES = {
    "qa_simple": "qa_simple.json",
    "qa_agg": "qa_agg.json",
    "qa_join": "qa_join.json",
    "qa_advanced": "qa_advanced.json",
    "qa_synonyms": "qa_synonyms.json",
}

DATASET_LABELS = {
    "qa_simple": "简单查询",
    "qa_agg": "聚合查询",
    "qa_join": "多表关联",
    "qa_advanced": "高级查询",
    "qa_synonyms": "同义词/别名",
}


def _get_results_path(dataset_name: str) -> Path:
    return RESULTS_DIR / f"{dataset_name}_results.json"


def load_dataset(dataset_name: str) -> List[Dict]:
    filename = DATASET_FILES.get(dataset_name)
    if not filename:
        return []
    filepath = DATASETS_DIR / filename
    if not filepath.exists():
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def list_datasets() -> List[Dict]:
    datasets = []
    for key in DATASET_FILES:
        filepath = DATASETS_DIR / DATASET_FILES[key]
        if filepath.exists():
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            datasets.append({
                "name": key,
                "label": DATASET_LABELS.get(key, key),
                "count": len(data),
                "filename": DATASET_FILES[key],
            })
    return datasets


def load_results(dataset_name: str) -> Dict[str, Dict]:
    filepath = _get_results_path(dataset_name)
    if filepath.exists():
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_results(dataset_name: str, results: Dict[str, Dict]):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    filepath = _get_results_path(dataset_name)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)


def get_question_result(dataset_name: str, question_index: int) -> Optional[Dict]:
    results = load_results(dataset_name)
    return results.get(str(question_index))


def update_question_result(dataset_name: str, question_index: int, data: Dict):
    results = load_results(dataset_name)
    key = str(question_index)
    if key not in results:
        results[key] = {}
    results[key].update(data)
    results[key]["updated_at"] = time.time()
    save_results(dataset_name, results)


def _get_match_value(item: Dict, field: str) -> Optional[bool]:
    val = item.get(field)
    if val == "matched":
        return True
    if val == "not_matched":
        return False
    return None


def get_dataset_stats(dataset_name: str) -> Dict:
    dataset = load_dataset(dataset_name)
    results = load_results(dataset_name)
    total = len(dataset)
    tested = 0
    ai_generated = 0
    correct_executed = 0
    ai_executed = 0
    sql_match_count = 0
    result_match_count = 0
    result_match_set = 0
    for key, item in results.items():
        has_ai = bool(item.get("ai_generated_sql")) or bool(item.get("ai_error"))
        if has_ai:
            tested += 1
            sql_val = _get_match_value(item, "sql_match")
            if sql_val is True:
                sql_match_count += 1
        has_ai_gen = bool(item.get("ai_generated_sql"))
        if has_ai_gen:
            ai_generated += 1
            res_val = _get_match_value(item, "result_match")
            if res_val is True:
                result_match_count += 1
            if res_val is not None:
                result_match_set += 1
        if item.get("correct_sql_result") is not None:
            correct_executed += 1
        if item.get("ai_sql_result") is not None:
            ai_executed += 1
    return {
        "total": total,
        "tested": tested,
        "ai_generated": ai_generated,
        "correct_executed": correct_executed,
        "ai_executed": ai_executed,
        "sql_match_count": sql_match_count,
        "result_match_count": result_match_count,
        "result_match_set": result_match_set,
        "sql_generation_accuracy": round(sql_match_count / tested * 100, 1) if tested > 0 else 0,
        "sql_execution_accuracy": round(result_match_count / tested * 100, 1) if tested > 0 else 0,
        "result_accuracy": round(result_match_count / tested * 100, 1) if tested > 0 else 0,
        "test_coverage": round(tested / total * 100, 1) if total > 0 else 0,
    }


def get_all_stats() -> Dict:
    datasets = list_datasets()
    total_questions = 0
    total_tested = 0
    total_ai_generated = 0
    total_sql_match = 0
    total_result_match = 0
    total_result_set = 0
    total_correct_executed = 0
    total_ai_executed = 0
    per_dataset = {}
    for ds in datasets:
        name = ds["name"]
        stats = get_dataset_stats(name)
        per_dataset[name] = stats
        total_questions += stats["total"]
        total_tested += stats["tested"]
        total_ai_generated += stats["ai_generated"]
        total_sql_match += stats["sql_match_count"]
        total_result_match += stats["result_match_count"]
        total_result_set += stats["result_match_set"]
        total_correct_executed += stats["correct_executed"]
        total_ai_executed += stats["ai_executed"]
    return {
        "total_questions": total_questions,
        "total_datasets": len(datasets),
        "total_tested": total_tested,
        "total_ai_generated": total_ai_generated,
        "total_correct_executed": total_correct_executed,
        "total_ai_executed": total_ai_executed,
        "total_sql_match": total_sql_match,
        "total_result_match": total_result_match,
        "total_result_set": total_result_set,
        "overall_sql_generation_accuracy": round(total_sql_match / total_tested * 100, 1) if total_tested > 0 else 0,
        "overall_sql_execution_accuracy": round(total_result_match / total_tested * 100, 1) if total_tested > 0 else 0,
        "overall_result_accuracy": round(total_result_match / total_tested * 100, 1) if total_tested > 0 else 0,
        "per_dataset": per_dataset,
    }


def reset_results(dataset_name: str = None) -> Dict[str, bool]:
    """
    重置测试结果文件

    Args:
        dataset_name: 可选，指定数据集名称。为空则重置所有结果。

    Returns:
        重置成功的数据集列表
    """
    reset_list = []
    if dataset_name:
        if dataset_name in DATASET_FILES:
            filepath = _get_results_path(dataset_name)
            if filepath.exists():
                filepath.unlink()
            reset_list.append(dataset_name)
    else:
        for name in DATASET_FILES:
            filepath = _get_results_path(name)
            if filepath.exists():
                filepath.unlink()
            reset_list.append(name)
    return {"reset_datasets": reset_list, "success": True}
