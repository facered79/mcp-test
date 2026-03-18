# MCP Test — Model Context Protocol 서버 구성

Claude Code와 연동되는 MCP(Model Context Protocol) 서버 구성 및 테스트 프로젝트입니다.

## 개요

캘린더 관리와 할 일(Todo) 관리를 위한 MCP 서버를 구현하고, Claude Code에 연동하여 AI가 직접 일정과 태스크를 관리할 수 있도록 합니다.

## MCP 서버 목록

| 서버 | 기능 |
|------|------|
| Calendar MCP | 일정 생성, 조회, 수정, 삭제 |
| Todo MCP | 할 일 목록 관리 |

## 기술 스택

- Language: Python
- Protocol: MCP (Model Context Protocol)
- Config: `.mcp.json`

## 설정 방법

`.mcp.json` 파일을 Claude Code 설정에 등록하면 AI가 MCP 서버 도구를 사용할 수 있습니다.

```json
{
  "mcpServers": {
    "calendar": {
      "command": "python",
      "args": ["calendar_server.py"]
    },
    "todo": {
      "command": "python",
      "args": ["todo_server.py"]
    }
  }
}
```

## 실행

```bash
pip install -r requirements.txt
python calendar_server.py
# 또는
python todo_server.py
```

## 라이선스

MIT
