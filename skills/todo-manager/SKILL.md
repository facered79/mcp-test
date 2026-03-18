---
name: todo-manager
description: 할일 목록을 관리합니다. 태스크 조회, 생성, 수정, 완료 처리, 삭제 작업이 필요할 때 사용합니다.
---

할일 MCP 서버(`mcp__todo__*` 도구)를 활용해 사용자의 태스크를 관리합니다.

## 사용 가능한 도구

- `mcp__todo__get_todos` — 할일 조회 (전체 / 상태별 / 마감일별 / 우선순위별)
- `mcp__todo__create_todo` — 새 할일 등록
- `mcp__todo__update_todo` — 할일 수정 또는 완료 처리
- `mcp__todo__delete_todo` — 할일 삭제
- `mcp__todo__get_health` — 서버 상태 확인

## 작업 절차

1. 사용자 요청에서 제목, 마감일, 우선순위 정보를 파악합니다.
2. 마감일 형식은 항상 YYYY-MM-DD 로 변환합니다.
3. 우선순위 기준:
   - `high` — 긴급하거나 중요한 작업
   - `medium` — 일반적인 작업 (기본값)
   - `low` — 여유 있는 작업
4. 완료 처리 시 `update_todo`에 `completed: true` 를 전달합니다.
5. 조회 시 상태(pending/completed), 마감일, 우선순위 필터를 적절히 조합합니다.
6. 결과를 우선순위와 마감일 순으로 정렬해 보여줍니다.
