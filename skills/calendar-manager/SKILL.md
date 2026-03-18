---
name: calendar-manager
description: 캘린더 일정을 관리합니다. 일정 조회, 생성, 수정, 삭제 작업이 필요할 때 사용합니다.
---

캘린더 MCP 서버(`mcp__calendar__*` 도구)를 활용해 사용자의 일정을 관리합니다.

## 사용 가능한 도구

- `mcp__calendar__get_events` — 일정 조회 (전체 / 날짜별 / 월별)
- `mcp__calendar__create_event` — 새 일정 등록
- `mcp__calendar__update_event` — 기존 일정 수정
- `mcp__calendar__delete_event` — 일정 삭제
- `mcp__calendar__get_health` — 서버 상태 확인

## 작업 절차

1. 사용자 요청에서 날짜, 제목, 시간 정보를 파악합니다.
2. 날짜 형식은 항상 YYYY-MM-DD, 시간은 HH:MM 으로 변환합니다.
3. 일정 조회 시 date(특정일) 또는 month(월 전체) 파라미터를 적절히 선택합니다.
4. 일정 생성 시 색상은 내용에 맞게 선택합니다:
   - 업무/회의: `#4299e1` (파란색)
   - 개인/약속: `#68d391` (초록색)
   - 마감/중요: `#fc8181` (빨간색)
   - 이벤트: `#f6ad55` (주황색)
   - 기념일: `#b794f4` (보라색)
5. 결과를 사용자 친화적으로 요약해 보여줍니다.
