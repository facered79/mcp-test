"""
캘린더 MCP 서버

제공 도구(Tools):
  - get_events       : 일정 조회 (전체 / 날짜 / 월별)
  - create_event     : 일정 등록
  - update_event     : 일정 수정
  - delete_event     : 일정 삭제
  - get_health       : 서버 상태 확인

실행:
  python mcp_server.py

Claude Code 등록 (.mcp.json):
  {
    "mcpServers": {
      "calendar": {
        "command": "python",
        "args": ["C:/Users/student/Documents/mcp_test/calendar/mcp_server.py"]
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
DB_FILE = os.path.join(os.path.dirname(__file__), "events.json")

# ── DB 헬퍼 ──────────────────────────────────────────────
def load_events() -> list[dict]:
    if not os.path.exists(DB_FILE):
        return []
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_events(events: list[dict]) -> None:
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=2)

def ok(data: Any) -> list[TextContent]:
    return [TextContent(type="text", text=json.dumps(data, ensure_ascii=False, indent=2))]

def err(msg: str) -> list[TextContent]:
    return [TextContent(type="text", text=json.dumps({"success": False, "error": msg}, ensure_ascii=False))]

# ── MCP 서버 ──────────────────────────────────────────────
app = Server("calendar-mcp")

@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_events",
            description="캘린더 일정을 조회합니다. date(YYYY-MM-DD) 또는 month(YYYY-MM) 파라미터로 필터링할 수 있습니다.",
            inputSchema={
                "type": "object",
                "properties": {
                    "date":  {"type": "string", "description": "특정 날짜 조회 (YYYY-MM-DD)"},
                    "month": {"type": "string", "description": "특정 월 조회 (YYYY-MM)"}
                }
            }
        ),
        Tool(
            name="create_event",
            description="캘린더에 새 일정을 등록합니다.",
            inputSchema={
                "type": "object",
                "required": ["date", "title"],
                "properties": {
                    "date":  {"type": "string", "description": "날짜 (YYYY-MM-DD)"},
                    "title": {"type": "string", "description": "일정 제목 (최대 40자)"},
                    "start": {"type": "string", "description": "시작 시간 (HH:MM)"},
                    "end":   {"type": "string", "description": "종료 시간 (HH:MM)"},
                    "memo":  {"type": "string", "description": "메모 (최대 200자)"},
                    "color": {
                        "type": "string",
                        "description": "색상 hex 코드",
                        "enum": ["#4299e1", "#68d391", "#fc8181", "#f6ad55", "#b794f4", "#76e4f7"]
                    }
                }
            }
        ),
        Tool(
            name="update_event",
            description="기존 일정을 수정합니다. id는 필수이며, 나머지 필드 중 수정할 것만 전달합니다.",
            inputSchema={
                "type": "object",
                "required": ["id"],
                "properties": {
                    "id":    {"type": "string", "description": "수정할 일정 ID"},
                    "title": {"type": "string", "description": "새 제목"},
                    "date":  {"type": "string", "description": "새 날짜 (YYYY-MM-DD)"},
                    "start": {"type": "string", "description": "새 시작 시간 (HH:MM)"},
                    "end":   {"type": "string", "description": "새 종료 시간 (HH:MM)"},
                    "memo":  {"type": "string", "description": "새 메모"},
                    "color": {"type": "string", "description": "새 색상 hex 코드"}
                }
            }
        ),
        Tool(
            name="delete_event",
            description="일정을 삭제합니다.",
            inputSchema={
                "type": "object",
                "required": ["id"],
                "properties": {
                    "id": {"type": "string", "description": "삭제할 일정 ID"}
                }
            }
        ),
        Tool(
            name="get_health",
            description="캘린더 서버 상태와 전체 일정 수를 확인합니다.",
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
        events = load_events()
        return ok({
            "success": True,
            "status": "ok",
            "server_time": datetime.now().isoformat(),
            "total_events": len(events),
            "db_file": DB_FILE
        })

    # ── get_events ─────────────────────────────────────
    elif name == "get_events":
        events = load_events()
        date  = arguments.get("date")
        month = arguments.get("month")
        if date:
            events = [e for e in events if e.get("date") == date]
        elif month:
            events = [e for e in events if e.get("date", "").startswith(month)]
        events.sort(key=lambda e: (e.get("date", ""), e.get("start", "")))
        return ok({"success": True, "count": len(events), "events": events})

    # ── create_event ────────────────────────────────────
    elif name == "create_event":
        if not arguments.get("title"):
            return err("title은 필수입니다")
        if not arguments.get("date"):
            return err("date는 필수입니다 (YYYY-MM-DD)")
        try:
            datetime.strptime(arguments["date"], "%Y-%m-%d")
        except ValueError:
            return err("date 형식이 잘못됐습니다 (YYYY-MM-DD)")

        event = {
            "id":         str(uuid.uuid4()),
            "date":       arguments["date"],
            "title":      arguments["title"][:40],
            "start":      arguments.get("start", ""),
            "end":        arguments.get("end", ""),
            "memo":       arguments.get("memo", "")[:200],
            "color":      arguments.get("color", "#4299e1"),
            "created_at": datetime.now().isoformat()
        }
        events = load_events()
        events.append(event)
        save_events(events)
        return ok({"success": True, "event": event})

    # ── update_event ────────────────────────────────────
    elif name == "update_event":
        event_id = arguments.get("id")
        if not event_id:
            return err("id는 필수입니다")

        events = load_events()
        target = next((e for e in events if e["id"] == event_id), None)
        if not target:
            return err(f"일정을 찾을 수 없습니다: {event_id}")

        for field in ("title", "date", "start", "end", "memo", "color"):
            if field in arguments:
                target[field] = arguments[field]
        target["updated_at"] = datetime.now().isoformat()
        save_events(events)
        return ok({"success": True, "event": target})

    # ── delete_event ────────────────────────────────────
    elif name == "delete_event":
        event_id = arguments.get("id")
        if not event_id:
            return err("id는 필수입니다")

        events = load_events()
        new_events = [e for e in events if e["id"] != event_id]
        if len(new_events) == len(events):
            return err(f"일정을 찾을 수 없습니다: {event_id}")

        save_events(new_events)
        return ok({"success": True, "message": "일정이 삭제되었습니다", "id": event_id})

    else:
        return err(f"알 수 없는 도구: {name}")

# ── 진입점 ────────────────────────────────────────────────
async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
