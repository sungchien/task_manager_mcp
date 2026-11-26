import json
import os
import tempfile
from pathlib import Path
from mcp.server.mcpserver import MCPServer

# 1. 初始化 FastMCP 物件，設定 Server 識別名稱
mcp = MCPServer("Local_Task_Manager")

# 2. 硬碟儲存路徑與預設待辦事項
TASKS_FILE = Path(__file__).resolve().parent / "tasks.json"
DEFAULT_TASKS = [
    {"id": 1, "title": "批改期末作業講義", "completed": False},
    {"id": 2, "title": "更新下學期 Agent ⼤綱", "completed": True},
]


def _save_tasks(tasks: list[dict], tasks_file: Path | None = None) -> None:
    """以原子寫入方式將待辦事項清單儲存至硬碟中的 JSON 檔案。"""
    target_file = TASKS_FILE if tasks_file is None else tasks_file
    target_file.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        dir=target_file.parent,
        prefix=f".{target_file.stem}_",
        suffix=".tmp",
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(tasks, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp_path, target_file)
    except BaseException:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def _load_tasks(tasks_file: Path | None = None) -> list[dict]:
    """從硬碟讀取待辦事項清單；若檔案尚未存在則建立預設清單。"""
    target_file = TASKS_FILE if tasks_file is None else tasks_file
    if not target_file.exists():
        tasks = [dict(task) for task in DEFAULT_TASKS]
        _save_tasks(tasks, target_file)
        return tasks

    with target_file.open("r", encoding="utf-8") as f:
        return json.load(f)


# 3. 使⽤ @mcp.tool() 宣告可供 Agent 調⽤的⼯具
@mcp.tool()
def get_all_tasks() -> str:
    """
    獲取⽬前系統中所有的待辦事項清單與其完成狀態。
    """
    tasks = _load_tasks()
    return json.dumps(tasks, ensure_ascii=False, indent=2)


@mcp.tool()
def add_new_task(title: str) -> str:
    """
    新增⼀個待辦事項到系統中。
    參數:
    title: 待辦事項的標題或內容描述。
    """
    tasks = _load_tasks()
    next_id = max((task["id"] for task in tasks), default=0) + 1
    new_task = {
        "id": next_id,
        "title": title,
        "completed": False,
    }
    tasks.append(new_task)
    _save_tasks(tasks)
    return json.dumps(
        {"status": "success", "added_task": new_task},
        ensure_ascii=False,
    )


@mcp.tool()
def mark_task_completed(task_id: int) -> str:
    """
    將指定的待辦事項標記為「已完成」。
    參數:
    task_id: 欲標記的待辦事項唯⼀ ID (整數)。
    """
    tasks = _load_tasks()
    for task in tasks:
        if task["id"] == task_id:
            task["completed"] = True
            _save_tasks(tasks)
            msg = f"任務 ID {task_id} 已成功標記為完成。"

            return json.dumps(
                {"status": "success", "message": msg},
                ensure_ascii=False,
            )
    err = f"找不到 ID 為 {task_id} 的任務。"
    return json.dumps(
        {"status": "error", "message": err},
        ensure_ascii=False,
    )

# 4. 設定以 stdio 傳輸模式啟動 Server
if __name__ == "__main__":
    mcp.run(transport="stdio")