"""
할일 REST API 서버
- GET    /api/todos               전체 할일 조회
- GET    /api/todos?status=...    상태별 조회 (pending / completed)
- GET    /api/todos?due=YYYY-MM-DD 마감일별 조회
- POST   /api/todos               할일 등록
- PUT    /api/todos/<id>          할일 수정
- DELETE /api/todos/<id>          할일 삭제
- GET    /api/health              서버 상태 확인
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json, uuid, os
from datetime import datetime

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

DB_FILE = os.path.join(os.path.dirname(__file__), 'todos.json')

# ── DB 헬퍼 ──────────────────────────────────────────
def load_todos():
    if not os.path.exists(DB_FILE):
        return []
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_todos(todos):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(todos, f, ensure_ascii=False, indent=2)

# ── 라우트 ───────────────────────────────────────────

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/api/health')
def health():
    todos = load_todos()
    pending = sum(1 for t in todos if not t.get('completed'))
    completed = sum(1 for t in todos if t.get('completed'))
    return jsonify({
        'status': 'ok',
        'server_time': datetime.now().isoformat(),
        'total_todos': len(todos),
        'pending': pending,
        'completed': completed
    })

@app.route('/api/todos', methods=['GET'])
def get_todos():
    todos = load_todos()
    status = request.args.get('status')   # pending / completed
    due = request.args.get('due')         # YYYY-MM-DD
    priority = request.args.get('priority')  # low / medium / high

    if status == 'pending':
        todos = [t for t in todos if not t.get('completed')]
    elif status == 'completed':
        todos = [t for t in todos if t.get('completed')]
    if due:
        todos = [t for t in todos if t.get('due_date') == due]
    if priority:
        todos = [t for t in todos if t.get('priority') == priority]

    todos.sort(key=lambda t: (t.get('due_date') or '9999', t.get('created_at', '')))
    return jsonify({'success': True, 'count': len(todos), 'todos': todos})

@app.route('/api/todos', methods=['POST'])
def create_todo():
    data = request.get_json(silent=True) or {}

    if not data.get('title'):
        return jsonify({'success': False, 'error': 'title은 필수입니다'}), 400

    if data.get('due_date'):
        try:
            datetime.strptime(data['due_date'], '%Y-%m-%d')
        except ValueError:
            return jsonify({'success': False, 'error': 'due_date 형식이 잘못됐습니다 (YYYY-MM-DD)'}), 400

    priority = data.get('priority', 'medium')
    if priority not in ('low', 'medium', 'high'):
        return jsonify({'success': False, 'error': 'priority는 low / medium / high 중 하나여야 합니다'}), 400

    todo = {
        'id':         str(uuid.uuid4()),
        'title':      data['title'][:100],
        'memo':       data.get('memo', '')[:500],
        'due_date':   data.get('due_date', ''),
        'priority':   priority,
        'completed':  False,
        'created_at': datetime.now().isoformat()
    }

    todos = load_todos()
    todos.append(todo)
    save_todos(todos)
    return jsonify({'success': True, 'todo': todo}), 201

@app.route('/api/todos/<todo_id>', methods=['PUT'])
def update_todo(todo_id):
    todos = load_todos()
    target = next((t for t in todos if t['id'] == todo_id), None)
    if not target:
        return jsonify({'success': False, 'error': '할일을 찾을 수 없습니다'}), 404

    data = request.get_json(silent=True) or {}

    if 'title' in data:
        target['title'] = data['title'][:100]
    if 'memo' in data:
        target['memo'] = data['memo'][:500]
    if 'due_date' in data:
        if data['due_date']:
            try:
                datetime.strptime(data['due_date'], '%Y-%m-%d')
            except ValueError:
                return jsonify({'success': False, 'error': 'due_date 형식이 잘못됐습니다 (YYYY-MM-DD)'}), 400
        target['due_date'] = data['due_date']
    if 'priority' in data:
        if data['priority'] not in ('low', 'medium', 'high'):
            return jsonify({'success': False, 'error': 'priority는 low / medium / high 중 하나여야 합니다'}), 400
        target['priority'] = data['priority']
    if 'completed' in data:
        target['completed'] = bool(data['completed'])
        if target['completed']:
            target['completed_at'] = datetime.now().isoformat()
        else:
            target.pop('completed_at', None)

    target['updated_at'] = datetime.now().isoformat()
    save_todos(todos)
    return jsonify({'success': True, 'todo': target})

@app.route('/api/todos/<todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
    todos = load_todos()
    new_todos = [t for t in todos if t['id'] != todo_id]
    if len(new_todos) == len(todos):
        return jsonify({'success': False, 'error': '할일을 찾을 수 없습니다'}), 404
    save_todos(new_todos)
    return jsonify({'success': True, 'message': '할일이 삭제되었습니다'})

if __name__ == '__main__':
    print("=" * 50)
    print("  할일 API 서버 시작")
    print("  http://localhost:5001")
    print()
    print("  API 엔드포인트:")
    print("  GET    /api/health")
    print("  GET    /api/todos")
    print("  GET    /api/todos?status=pending|completed")
    print("  GET    /api/todos?due=YYYY-MM-DD")
    print("  GET    /api/todos?priority=low|medium|high")
    print("  POST   /api/todos")
    print("  PUT    /api/todos/<id>")
    print("  DELETE /api/todos/<id>")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5001, debug=True)
