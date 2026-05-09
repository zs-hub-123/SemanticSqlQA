
# 初始化测试结果文件
# 每个数据集对应一个结果文件，文件名格式为 "qa_simple_results.json"

import json
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
RESULTS_DIR = BASE_DIR / "test_suite" / "results"
DATASETS_DIR = BASE_DIR / "test_suite" / "datasets"

RESULTS_DIR.mkdir(parents=True, exist_ok=True)

dataset_files = {
    "qa_simple": "qa_simple.json",
    "qa_agg": "qa_agg.json",
    "qa_join": "qa_join.json",
    "qa_advanced": "qa_advanced.json",
    "qa_synonyms": "qa_synonyms.json",
}

for name, filename in dataset_files.items():
    result_file = RESULTS_DIR / f"{name}_results.json"
    if result_file.exists():
        print(f"  {result_file.name} 已存在，跳过")
        continue
    filepath = DATASETS_DIR / filename
    if not filepath.exists():
        print(f"  警告: {filepath} 不存在，跳过 {name}")
        continue
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    results = {}
    for idx in range(len(data)):
        results[str(idx)] = {}
    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"  创建 {result_file.name} ({len(data)} 题)")
