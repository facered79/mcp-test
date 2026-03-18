"""
할일 MCP 서버

제공 도구(Tools):
  - get_todos    : 할일 조회 (전체 / 상태별 / 마감일별 / 우선순위별)
  - create_todo  : 할일 등록
  - update_todo  : 할일 수정 (내용, 완료 여부 등)
  - delete_todo  : 할일 삭제
  - get_health   : 서버 상태 확인

실행:
  python mcp_server.py

Claude Code 등록 (.mcp.json):
  {
    "mcpServers": {
      "todo": {
        "command": "python",
        "args": ["C:/Users/student/Documents/mcp_test/todo/mcp_server.py"]
      }
    }
  }
"""

import asyncio
import json
import os
import uuid
from datetime import datetime
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# ── 데이터 저장 경로 ──────────────────────────────────────
DB_FILE = os.path.join(os.path.dirname(__file__), "todos.json")

# ── DB 헬퍼 ──────────────────────────────────────────────
def load_todos() -> list[dict]:
    if not os.path.exists(DB_FILE):
        return []
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_todos(todos: list[dict]) -> None:
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(todos, f, ensure_ascii=False, indent=2)

def ok(data: Any) -> list[TextContent]:
    return [TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2))]

def err(msg: str) -> list[TextContent]:
    return [TextContent(type="text", text=json.dumps({"success": False, "error": msg}, ensure_ascii=False))]

# ── MCP 서버 ──────────────────────────────────────────────
app = Server("todo-mcp")

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_todos",
            description="할일 목록을 조회합니다. status(pending/completed), due(YYYY-MM-DD), priority(low/medium/high)로 필터링할 수 있습니다.",
            inputSchema={
                "type": "object",
                "properties": {
                    "status":   {"type": "string", "description": "상태 필터 (pending 또는 completed)", "enum": ["pending", "completed"]},
                    "due":      {"type": "string", "description": "마감일 필터 (YYYY-MM-DD)"},
                    "priority": {"type": "string", "description": "우선순위 필터 (low / medium / high)", "enum": ["low", "medium", "high"]}
                }
            }
        ),
        Tool(
            name="create_todo",
            description="새 할일을 등록합니다.",
            inputSchema={
                "type": "object",
                "required": ["title"],
                "properties": {
                    "title":    {"type": "string", "description": "할일 제목 (최대 100자)"},
                    "memo":     {"type": "string", "description": "메모 (최대 500자)"},
                    "due_date": {"type": "string", "description": "마감일 (YYYY-MM-DD)"},
                    "priority": {
                        "type": "string",
                        "description": "우선순위 (기본값: medium)",
                        "enum": ["low", "medium", "high"]
                    }
                }
            }
        ),
        Tool(
            name="update_todo",
            description="기존 할일을 수정합니다. id는 필수이며, 수정할 필드만 전달합니다. completed를 true로 설정하면 완료 처리됩니다.",
            inputSchema={
                "type": "object",
                "required": ["id"],
                "properties": {
                    "id":        {"type": "string", "description": "수정할 할일 ID"},
                    "title":     {"type": "string", "description": "새 제목"},
                    "memo":      {"type": "string", "description": "새 메모"},
                    "due_date":  {"type": "string", "description": "새 마감일 (YYYY-MM-DD)"},
                    "priority":  {"type": "string", "description": "새 우선순위", "enum": ["low", "medium", "high"]},
                    "completed": {"type": "boolean", "description": "완료 여부 (true: 완료, false: 미완료)"}
                }
            }
        ),
        Tool(
            name="delete_todo",
            description="할일을 삭제합니다.",
            inputSchema={
                "type": "object",
                "required": ["id"],
                "properties": {
                    "id": {"type": "string", "description": "삭제할 할일 ID"}
                }
            }
        ),
        Tool(
            name="get_health",
            description="할일 서버 상태와 전체/미완료/완료 할일 수를 확인합니다.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:

    # ── get_health ─────────────────────────────────────
    if name == "get_health":
        todos = load_todos()
        pending = sum(1 for t in todos if not t.get("completed"))
        completed = sum(1 for t in todos if t.get("completed"))
        return ok({
            "success": True,
            "status": "ok",
            "server_time": datetime.now().isoformat(),
            "total_todos": len(todos),
            "pending": pending,
            "completed": completed,
            "db_file": DB_FILE
        })

    # ── get_todos ──────────────────────────────────────
    elif name == "get_todos":
        todos = load_todos()
        status   = arguments.get("status")
        due      = arguments.get("due")
        priority = arguments.get("priority")

        if status == "pending":
            todos = [t for t in todos if not t.get("completed")]
        elif status == "completed":
            todos = [t for t in todos if t.get("completed")]
        if due:
            todos = [t for t in todos if t.get("due_date") == due]
        if priority:
            todos = [t for t in todos if t.get("priority") == priority]

        todos.sort(key=lambda t: (t.get("due_date") or "9999", t.get("created_at", "")))
        return ok({"success": True, "count": len(todos), "todos": todos})

    # ── create_todo ────────────────────────────────────
    elif name == "create_todo":
        if not arguments.get("title"):
            return err("title은 필수입니다")

        if arguments.get("due_date"):
            try:
                datetime.strptime(arguments["due_date"], "%Y-%m-%d")
            except ValueError:
                return err("due_date 형식이 잘못됐습니다 (YYYY-MM-DD)")

        priority = arguments.get("priority", "medium")
        if priority not in ("low", "medium", "high"):
            return err("priority는 low / medium / high 중 하나여야 합니다")

        todo = {
            "id":         str(uuid.uuid4()),
            "title":      arguments["title"][:100],
            "memo":       arguments.get("memo", "")[:500],
            "due_date":   arguments.get("due_date", ""),
            "priority":   priority,
            "completed":  False,
            "created_at": datetime.now().isoformat()
        }
        todos = load_todos()
        todos.append(todo)
        save_todos(todos)
        return ok({"success": True, "todo": todo})

    # ── update_todo ────────────────────────────────────
    elif name == "update_todo":
        todo_id = arguments.get("id")
        if not todo_id:
            return err("id는 필수입니다")

        todos = load_todos()
        target = next((t for t in todos if t["id"] == todo_id), None)
        if not target:
            return err(f"할일을 찾을 수 없습니다: {todo_id}")

        if "title" in arguments:
            target["title"] = arguments["title"][:100]
        if "memo" in arguments:
            target["memo"] = arguments["memo"][:500]
        if "due_date" in arguments:
            if arguments["due_date"]:
                try:
                    datetime.strptime(arguments["due_date"], "%Y-%m-%d")
                except ValueError:
                    return err("due_date 형식이 잘못됐습니다 (YYYY-MM-DD)")
            target["due_date"] = arguments["due_date"]
        if "priority" in arguments:
            if arguments["priority"] not in ("low", "medium", "high"):
                return err("priority는 low / medium / high 중 하나여야 합니다")
            target["priority"] = arguments["priority"]
        if "completed" in arguments:
            target["completed"] = bool(arguments["completed"])
            if target["completed"]:
                target["completed_at"] = datetime.now().isoformat()
            else:
                target.pop("completed_at", None)

        target["updated_at"] = datetime.now().isoformat()
        save_todos(todos)
        return ok({"success": True, "todo": target})

    # ── delete_todo ────────────────────────────────────
    elif name == "delete_todo":
        todo_id = arguments.get("id")
        if not todo_id:
            return err("id는 필수입니다")

        todos = load_todos()
        new_todos = [t for t in todos if t["id"] != todo_id]
        if len(new_todos) == len(todos):
            return err(f"할일을 찾을 수 없습니다: {todo_id}")

        save_todos(new_todos)
        return ok({"success": True, "message": "할일이 삭제되었습니다", "id": todo_id})

    else:
        return err(f"알 수 없는 도구: {name}")

# ── 진입점 ────────────────────────────────────────────────
async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
