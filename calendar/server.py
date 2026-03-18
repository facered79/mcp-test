"""
캘린더 REST API 서버
- GET    /api/events          전체 일정 조회
- GET    /api/events?date=... 날짜별 일정 조회
- POST   /api/events          일정 등록
- PUT    /api/events/<id>     일정 수정
- DELETE /api/events/<id>     일정 삭제
- GET    /api/health          서버 상태 확인
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json, uuid, os
from datetime import datetime

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

DB_FILE = os.path.join(os.path.dirname(__file__), 'events.json')

# ── DB 헬퍼 ──────────────────────────────────────────
def load_events():
    if not os.path.exists(DB_FILE):
        return []
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_events(events):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(events, f, ensure_ascii=False, indent=2)

# ── 라우트 ───────────────────────────────────────────

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/api/health')
def health():
    events = load_events()
    return jsonify({
        'status': 'ok',
        'server_time': datetime.now().isoformat(),
        'total_events': len(events)
    })

@app.route('/api/events', methods=['GET'])
def get_events():
    events = load_events()
    date = request.args.get('date')       # ?date=2026-03-18
    month = request.args.get('month')     # ?month=2026-03
    if date:
        events = [e for e in events if e.get('date') == date]
    elif month:
        events = [e for e in events if e.get('date', '').startswith(month)]
    events.sort(key=lambda e: (e.get('date', ''), e.get('start', '')))
    return jsonify({'success': True, 'count': len(events), 'events': events})

@app.route('/api/events', methods=['POST'])
def create_event():
    data = request.get_json(silent=True) or {}

    # 필수값 검증
    if not data.get('title'):
        return jsonify({'success': False, 'error': 'title은 필수입니다'}), 400
    if not data.get('date'):
        return jsonify({'success': False, 'error': 'date는 필수입니다 (YYYY-MM-DD)'}), 400

    # 날짜 형식 검증
    try:
        datetime.strptime(data['date'], '%Y-%m-%d')
    except ValueError:
        return jsonify({'success': False, 'error': 'date 형식이 잘못됐습니다 (YYYY-MM-DD)'}), 400

    event = {
        'id':        str(uuid.uuid4()),
        'date':      data['date'],
        'title':     data['title'][:40],
        'start':     data.get('start', ''),
        'end':       data.get('end', ''),
        'memo':      data.get('memo', '')[:200],
        'color':     data.get('color', '#4299e1'),
        'created_at': datetime.now().isoformat()
    }

    events = load_events()
    events.append(event)
    save_events(events)

    return jsonify({'success': True, 'event': event}), 201

@app.route('/api/events/<event_id>', methods=['PUT'])
def update_event(event_id):
    events = load_events()
    target = next((e for e in events if e['id'] == event_id), None)
    if not target:
        return jsonify({'success': False, 'error': '일정을 찾을 수 없습니다'}), 404

    data = request.get_json(silent=True) or {}
    for field in ('title', 'date', 'start', 'end', 'memo', 'color'):
        if field in data:
            target[field] = data[field]
    target['updated_at'] = datetime.now().isoformat()

    save_events(events)
    return jsonify({'success': True, 'event': target})

@app.route('/api/events/<event_id>', methods=['DELETE'])
def delete_event(event_id):
    events = load_events()
    new_events = [e for e in events if e['id'] != event_id]
    if len(new_events) == len(events):
        return jsonify({'success': False, 'error': '일정을 찾을 수 없습니다'}), 404
    save_events(new_events)
    return jsonify({'success': True, 'message': '일정이 삭제되었습니다'})

if __name__ == '__main__':
    print("=" * 50)
    print("  캘린더 API 서버 시작")
    print("  http://localhost:5000")
    print()
    print("  API 엔드포인트:")
    print("  GET    /api/health")
    print("  GET    /api/events?date=YYYY-MM-DD")
    print("  GET    /api/events?month=YYYY-MM")
    print("  POST   /api/events")
    print("  PUT    /api/events/<id>")
    print("  DELETE /api/events/<id>")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=True)
