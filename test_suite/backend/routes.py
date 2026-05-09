from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import uuid
import threading
import time
from test_suite.backend import storage
from backend.utils.database import db_manager

router = APIRouter(prefix="/api/test", tags=["测试套件"])

auto_test_tasks: dict = {}
auto_test_lock = threading.Lock()


class ExecuteRequest(BaseModel):
    sql: str
    type: str = "correct"


class MatchRequest(BaseModel):
    match_type: str
    value: str


class AutoTestStartRequest(BaseModel):
    interval: int = 30
    skip_existing: bool = True


@router.get("/datasets")
def list_datasets():
    datasets = storage.list_datasets()
    for ds in datasets:
        stats = storage.get_dataset_stats(ds["name"])
        ds["stats"] = stats
    return {"success": True, "datasets": datasets}


@router.get("/dataset/{dataset_name}")
def get_dataset(dataset_name: str, page: int = 1, page_size: int = 10):
    dataset = storage.load_dataset(dataset_name)
    if not dataset:
        raise HTTPException(status_code=404, detail="数据集不存在")
    total = len(dataset)
    page = max(1, page)
    page_size = max(1, min(100, page_size))
    total_pages = (total + page_size - 1) // page_size
    start = (page - 1) * page_size
    end = start + page_size
    stats = storage.get_dataset_stats(dataset_name)
    results = storage.load_results(dataset_name)
    questions = []
    for idx, item in enumerate(dataset[start:end], start=start + 1):
        key = str(idx - 1)
        result = results.get(key, {})
        questions.append({
            "index": idx - 1,
            "question": item["question"],
            "difficulty": item.get("difficulty", ""),
            "technique": item.get("technique", ""),
            "domain": item.get("domain", ""),
            "tables": item.get("tables", []),
            "tested": bool(result.get("ai_generated_sql")) or bool(result.get("ai_error")),
            "sql_match": result.get("sql_match"),
            "result_match": result.get("result_match"),
            "correct_executed": result.get("correct_sql_result") is not None,
            "ai_executed": result.get("ai_sql_result") is not None,
            "ai_error": bool(result.get("ai_error")),
        })
    return {
        "success": True,
        "dataset": dataset_name,
        "questions": questions,
        "stats": stats,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
        }
    }


@router.get("/question/{dataset_name}/{question_index}")
def get_question(dataset_name: str, question_index: int):
    dataset = storage.load_dataset(dataset_name)
    if question_index < 0 or question_index >= len(dataset):
        raise HTTPException(status_code=404, detail="问题不存在")
    item = dataset[question_index]
    result = storage.get_question_result(dataset_name, question_index) or {}
    return {
        "success": True,
        "question": {
            "index": question_index,
            "question": item["question"],
            "sql": item["sql"],
            "difficulty": item.get("difficulty", ""),
            "technique": item.get("technique", ""),
            "domain": item.get("domain", ""),
            "tables": item.get("tables", []),
        },
        "result": result,
    }


@router.post("/generate-ai/{dataset_name}/{question_index}")
def generate_ai_sql(dataset_name: str, question_index: int):
    dataset = storage.load_dataset(dataset_name)
    if question_index < 0 or question_index >= len(dataset):
        raise HTTPException(status_code=404, detail="问题不存在")
    item = dataset[question_index]
    question = item["question"]

    try:
        from backend.services.pipeline import QAPipeline
        from backend.core.config import config as app_config
        from backend.utils.database import DatabaseConnection

        biz_db = DatabaseConnection(app_config.business_db_config)
        sem_db = DatabaseConnection(app_config.semantic_db_config)
        biz_db.connect()
        sem_db.connect()
        try:
            pipeline = QAPipeline(sem_db, biz_db)
            pipeline_result = pipeline.process(question)
            ai_sql = pipeline_result.get("sql", "")
            explanation = pipeline_result.get("explanation", "")
            error = pipeline_result.get("error")
            tables_used = pipeline_result.get("tables_used", [])
            elapsed = pipeline_result.get("elapsed_time", 0)

            existing = storage.get_question_result(dataset_name, question_index) or {}
            sql_match_manual = existing.get("sql_match_manual", False)
            update_data = {
                "ai_generated_sql": ai_sql,
                "ai_explanation": explanation,
                "ai_error": error,
                "ai_tables_used": tables_used,
                "ai_elapsed": elapsed,
                "ai_generated_at": __import__("time").time(),
            }
            if not sql_match_manual:
                correct_sql = item["sql"]
                sql_matched = _compare_sql(correct_sql, ai_sql) if ai_sql else False
                update_data["sql_match"] = "matched" if sql_matched else "not_matched"

            storage.update_question_result(dataset_name, question_index, update_data)

            return {
                "success": True,
                "ai_sql": ai_sql,
                "explanation": explanation,
                "error": error,
                "elapsed": elapsed,
                "sql_match": update_data.get("sql_match", existing.get("sql_match")),
            }
        except Exception as e:
            __import__("traceback").print_exc()
            storage.update_question_result(dataset_name, question_index, {
                "ai_generated_sql": "",
                "ai_error": str(e),
                "sql_match": "not_matched",
                "ai_generated_at": __import__("time").time(),
            })
            return {"success": False, "error": str(e)}
        finally:
            biz_db.close()
            sem_db.close()
    except Exception as outer_e:
        storage.update_question_result(dataset_name, question_index, {
            "ai_generated_sql": "",
            "ai_error": str(outer_e),
            "sql_match": "not_matched",
            "ai_generated_at": __import__("time").time(),
        })
        return {"success": False, "error": str(outer_e)}


@router.post("/execute/{dataset_name}/{question_index}")
def execute_sql(dataset_name: str, question_index: int, req: ExecuteRequest):
    from backend.core.config import config as app_config
    from backend.utils.database import DatabaseConnection

    biz_db = DatabaseConnection(app_config.business_db_config)
    biz_db.connect()
    try:
        result = biz_db.execute_query(req.sql)
        columns = list(result[0].keys()) if result else []
        rows = [list(r.values()) for r in result]
        row_count = len(result)

        if req.type == "correct":
            storage.update_question_result(dataset_name, question_index, {
                "correct_sql_result": {"columns": columns, "rows": rows, "row_count": row_count},
                "correct_executed_at": __import__("time").time(),
            })
        else:
            update_data = {
                "ai_sql_result": {"columns": columns, "rows": rows, "row_count": row_count},
                "ai_executed_at": __import__("time").time(),
            }
            existing = storage.get_question_result(dataset_name, question_index) or {}
            result_match_manual = existing.get("result_match_manual", False)
            if not result_match_manual:
                correct_res = existing.get("correct_sql_result")
                if correct_res and correct_res.get("row_count") is not None:
                    ai_res = {"columns": columns, "rows": rows, "row_count": row_count}
                    result_matched = _compare_results(correct_res, ai_res)
                    update_data["result_match"] = "matched" if result_matched else "not_matched"
            storage.update_question_result(dataset_name, question_index, update_data)

        return {
            "success": True,
            "columns": columns,
            "rows": rows,
            "row_count": row_count,
        }
    except Exception as e:
        error_msg = str(e)
        if req.type == "ai":
            storage.update_question_result(dataset_name, question_index, {
                "ai_sql_result": None,
                "ai_execute_error": error_msg,
                "ai_executed_at": __import__("time").time(),
            })
        return {"success": False, "error": error_msg}
    finally:
        biz_db.close()


@router.post("/match/{dataset_name}/{question_index}")
def set_match_status(dataset_name: str, question_index: int, req: MatchRequest):
    dataset = storage.load_dataset(dataset_name)
    if question_index < 0 or question_index >= len(dataset):
        raise HTTPException(status_code=404, detail="问题不存在")

    if req.match_type not in ("sql_match", "result_match"):
        raise HTTPException(status_code=400, detail="match_type 必须是 sql_match 或 result_match")
    if req.value not in ("matched", "not_matched", ""):
        raise HTTPException(status_code=400, detail="value 必须是 matched, not_matched 或空字符串")

    update_val = req.value if req.value else None
    manual_flag = req.match_type + "_manual"
    update_data = {req.match_type: update_val}
    if req.value:
        update_data[manual_flag] = True
    else:
        update_data[manual_flag] = False
    storage.update_question_result(dataset_name, question_index, update_data)
    return {"success": True, "match_type": req.match_type, "value": update_val}


@router.get("/stats/{dataset_name}")
def get_stats(dataset_name: str):
    dataset = storage.load_dataset(dataset_name)
    if not dataset:
        raise HTTPException(status_code=404, detail="数据集不存在")
    stats = storage.get_dataset_stats(dataset_name)
    return {"success": True, "stats": stats}


@router.get("/stats")
def get_all_stats():
    stats = storage.get_all_stats()
    return {"success": True, "stats": stats}


@router.post("/reset")
def reset_test_results(dataset_name: str = None):
    """重置测试结果，可指定数据集或重置所有"""
    result = storage.reset_results(dataset_name)
    return {"success": True, **result}


@router.post("/auto-test/start/{dataset_name}")
def start_auto_test(dataset_name: str, req: AutoTestStartRequest):
    dataset = storage.load_dataset(dataset_name)
    if not dataset:
        raise HTTPException(status_code=404, detail="数据集不存在")

    with auto_test_lock:
        for tid, task in auto_test_tasks.items():
            if task["dataset_name"] == dataset_name and task["running"]:
                return {"success": False, "error": "该数据集已有自动测试在运行"}

        results = storage.load_results(dataset_name)
        pending = []
        for idx in range(len(dataset)):
            key = str(idx)
            item = results.get(key, {})
            has_ai = bool(item.get("ai_generated_sql")) or bool(item.get("ai_error")) or item.get("sql_match") is not None
            if req.skip_existing and has_ai:
                continue
            pending.append(idx)

        if not pending:
            return {"success": False, "error": "没有待测试的问题"}

        task_id = str(uuid.uuid4())
        auto_test_tasks[task_id] = {
            "dataset_name": dataset_name,
            "running": True,
            "interval": req.interval,
            "skip_existing": req.skip_existing,
            "pending": pending[:],
            "current": 0,
            "total": len(pending),
            "completed": 0,
            "errors": [],
            "started_at": time.time(),
        }

    thread = threading.Thread(target=_run_auto_test, args=(task_id,), daemon=True)
    thread.start()

    return {"success": True, "task_id": task_id, "total": len(pending)}


@router.post("/auto-test/stop/{task_id}")
def stop_auto_test(task_id: str):
    with auto_test_lock:
        task = auto_test_tasks.get(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        task["running"] = False
    return {"success": True}


@router.get("/auto-test/status/{task_id}")
def get_auto_test_status(task_id: str):
    with auto_test_lock:
        task = auto_test_tasks.get(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        return {
            "success": True,
            "running": task["running"],
            "dataset_name": task["dataset_name"],
            "skip_existing": task.get("skip_existing", True),
            "total": task["total"],
            "completed": task["completed"],
            "position": task.get("position", 0),
            "current": task["current"],
            "interval": task["interval"],
            "errors": task["errors"][-20:],
            "elapsed": round(time.time() - task["started_at"], 1),
        }


def _run_auto_test(task_id: str):
    from backend.services.pipeline import QAPipeline
    from backend.core.config import config as app_config
    from backend.utils.database import DatabaseConnection

    task = auto_test_tasks.get(task_id)
    if not task:
        return

    dataset_name = task["dataset_name"]
    dataset = storage.load_dataset(dataset_name)

    biz_db = DatabaseConnection(app_config.business_db_config)
    sem_db = DatabaseConnection(app_config.semantic_db_config)
    biz_db.connect()
    sem_db.connect()

    try:
        for pos, idx in enumerate(task["pending"]):
            with auto_test_lock:
                if not task["running"]:
                    break
                task["current"] = idx
                task["position"] = pos

            item = dataset[idx]
            question = item["question"]
            correct_sql = item["sql"]

            # Step 1: Execute correct SQL
            try:
                res = biz_db.execute_query(correct_sql)
                columns = list(res[0].keys()) if res else []
                rows = [list(r.values()) for r in res]
                row_count = len(res)
                storage.update_question_result(dataset_name, idx, {
                    "correct_sql_result": {"columns": columns, "rows": rows, "row_count": row_count},
                    "correct_executed_at": time.time(),
                })
            except Exception as e:
                error_msg = str(e)
                storage.update_question_result(dataset_name, idx, {
                    "correct_sql_result": None,
                    "correct_execute_error": error_msg,
                    "correct_executed_at": time.time(),
                })
                with auto_test_lock:
                    task["errors"].append({"index": idx, "question": question, "step": "正确SQL执行", "error": error_msg})

            # Step 2: Generate AI SQL
            pipeline = None
            try:
                pipeline = QAPipeline(sem_db, biz_db)
                pipeline_result = pipeline.process(question)
                ai_sql = pipeline_result.get("sql", "")
                explanation = pipeline_result.get("explanation", "")
                error = pipeline_result.get("error")
                elapsed = pipeline_result.get("elapsed_time", 0)

                existing = storage.get_question_result(dataset_name, idx) or {}
                sql_match_manual = existing.get("sql_match_manual", False)
                update_data = {
                    "ai_generated_sql": ai_sql,
                    "ai_explanation": explanation,
                    "ai_error": error,
                    "ai_elapsed": elapsed,
                    "ai_generated_at": time.time(),
                }
                if not sql_match_manual:
                    sql_matched = _compare_sql(correct_sql, ai_sql) if ai_sql else False
                    update_data["sql_match"] = "matched" if sql_matched else "not_matched"
                storage.update_question_result(dataset_name, idx, update_data)

                if error:
                    with auto_test_lock:
                        task["errors"].append({"index": idx, "question": question, "step": "AI生成", "error": error})

                if ai_sql and not error:
                    try:
                        ai_res = biz_db.execute_query(ai_sql)
                        ai_columns = list(ai_res[0].keys()) if ai_res else []
                        ai_rows = [list(r.values()) for r in ai_res]
                        ai_row_count = len(ai_res)

                        ai_update = {
                            "ai_sql_result": {"columns": ai_columns, "rows": ai_rows, "row_count": ai_row_count},
                            "ai_executed_at": time.time(),
                        }
                        result_match_manual = existing.get("result_match_manual", False)
                        if not result_match_manual:
                            correct_res = storage.get_question_result(dataset_name, idx) or {}
                            cr = correct_res.get("correct_sql_result")
                            if cr and cr.get("row_count") is not None:
                                ar = {"columns": ai_columns, "rows": ai_rows, "row_count": ai_row_count}
                                result_matched = _compare_results(cr, ar)
                                ai_update["result_match"] = "matched" if result_matched else "not_matched"
                        storage.update_question_result(dataset_name, idx, ai_update)
                    except Exception as e:
                        storage.update_question_result(dataset_name, idx, {
                            "ai_sql_result": None,
                            "ai_execute_error": str(e),
                            "result_match": "not_matched",
                            "ai_executed_at": time.time(),
                        })
                        with auto_test_lock:
                            task["errors"].append({"index": idx, "question": question, "step": "AI SQL执行", "error": str(e)})

            except Exception as e:
                __import__("traceback").print_exc()
                storage.update_question_result(dataset_name, idx, {
                    "ai_generated_sql": "",
                    "ai_error": str(e),
                    "sql_match": "not_matched",
                    "ai_generated_at": time.time(),
                })
                with auto_test_lock:
                    task["errors"].append({"index": idx, "question": question, "step": "AI生成", "error": str(e)})

            with auto_test_lock:
                task["completed"] += 1

            with auto_test_lock:
                if not task["running"]:
                    break
            time.sleep(task["interval"])
    finally:
        biz_db.close()
        sem_db.close()
        with auto_test_lock:
            task["running"] = False

# 比较SQL语句是否相等（语义等价）
def _compare_sql(sql1: str, sql2: str) -> bool:
    """
    比较两条SQL语句是否语义等价
    - 忽略大小写和空白符差异
    - 忽略反引号和中括号差异
    - 忽略AS别名差异
    - 忽略SQL注释(-- 和 /* */)
    - 忽略表前缀(如 orders.total_amount → total_amount)
    """
    import re
    if not sql1 or not sql2:
        return False

    def normalize(sql):
        s = sql.lower()
        s = re.sub(r"--.*$", "", s, flags=re.MULTILINE)
        s = re.sub(r"/\*.*?\*/", "", s, flags=re.DOTALL)
        s = re.sub(r"[`\[\]]", "", s)
        s = re.sub(r"\s+", " ", s)
        s = s.strip()
        s = re.sub(r"\s*,\s*", ",", s)
        s = re.sub(r"\s*\(\s*", "(", s)
        s = re.sub(r"\s*\)\s*", ")", s)
        s = re.sub(r"\s+as\s+[^\s,\)]+\s*(?=[,\)]|$)", " ", s)
        s = re.sub(r"'[^']*'", "''", s)
        s = re.sub(r"\s+", " ", s)
        return s.strip()

    def strip_table_prefix(sql):
        s = re.sub(r"(\w+)\.(\w+)", r"\2", sql)
        return s

    n1 = strip_table_prefix(normalize(sql1))
    n2 = strip_table_prefix(normalize(sql2))
    return n1 == n2


def _compare_results(res1: dict, res2: dict) -> bool:
    """
    比较两个执行结果是否语义等价
    - 行数必须相同
    - 列名允许不同（AI生成的列名可能经过美化）
    - 行的值必须完全匹配
    """
    if not res1 or not res2:
        return False

    r1_rows = res1.get("rows", [])
    r2_rows = res2.get("rows", [])

    if res1.get("row_count") != res2.get("row_count"):
        return False

    if len(r1_rows) != len(r2_rows):
        return False

    for row1, row2 in zip(r1_rows, r2_rows):
        if len(row1) != len(row2):
            return False
        for v1, v2 in zip(row1, row2):
            if str(v1) != str(v2):
                return False

    return True


@router.post("/auto-match/{dataset_name}")
def auto_match_dataset(dataset_name: str):
    """
    自动匹配数据集中所有已生成结果的题目
    - 对已有ai_generated_sql和correct_sql的题目进行SQL匹配
    - 对已有ai_sql_result和correct_sql_result的题目进行结果匹配
    """
    dataset = storage.load_dataset(dataset_name)
    if not dataset:
        raise HTTPException(status_code=404, detail="数据集不存在")

    results = storage.load_results(dataset_name)

    sql_matched_count = 0
    sql_not_matched_count = 0
    result_matched_count = 0
    result_not_matched_count = 0
    skipped_count = 0
    errors = []

    for idx in range(len(dataset)):
        key = str(idx)
        result = results.get(key, {})

        existing = storage.get_question_result(dataset_name, idx) or {}

        sql_match_manual = existing.get("sql_match_manual", False)
        result_match_manual = existing.get("result_match_manual", False)

        correct_sql = dataset[idx].get("sql", "")
        ai_sql = result.get("ai_generated_sql", "")

        if ai_sql and correct_sql:
            if not sql_match_manual:
                sql_matched = _compare_sql(correct_sql, ai_sql)
                storage.update_question_result(dataset_name, idx, {
                    "sql_match": "matched" if sql_matched else "not_matched"
                })
                if sql_matched:
                    sql_matched_count += 1
                else:
                    sql_not_matched_count += 1
        else:
            skipped_count += 1

        correct_res = result.get("correct_sql_result")
        ai_res = result.get("ai_sql_result")

        if correct_res and ai_res:
            if not result_match_manual:
                res_matched = _compare_results(correct_res, ai_res)
                storage.update_question_result(dataset_name, idx, {
                    "result_match": "matched" if res_matched else "not_matched"
                })
                if res_matched:
                    result_matched_count += 1
                else:
                    result_not_matched_count += 1

    return {
        "success": True,
        "dataset": dataset_name,
        "total": len(dataset),
        "sql_matched": sql_matched_count,
        "sql_not_matched": sql_not_matched_count,
        "result_matched": result_matched_count,
        "result_not_matched": result_not_matched_count,
        "skipped": skipped_count,
    }
