from flask import Flask, render_template, request, jsonify, session, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from functools import wraps
import os
import uuid
import config

app = Flask(__name__)
app.secret_key = config.api_token


API_TOKEN = config.api_token


basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'monitor.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class Node(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    server_id = db.Column(db.String(32), unique=True, nullable=False)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    cpu_usage = db.Column(db.Float)
    memory_usage = db.Column(db.Float)
    disk_usage = db.Column(db.Float)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login')
def login_page():
    return render_template('login.html')


@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    if data and data.get('password') == config.passwd:
        session['logged_in'] = True
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': '密碼錯誤'})


@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('logged_in', None)
    return jsonify({'success': True})


@app.route('/api/check-login')
def check_login():
    return jsonify({'logged_in': session.get('logged_in', False)})


@app.route('/api/nodes')
def get_nodes():
    nodes = Node.query.all()
    return jsonify([{
        'id': node.id,
        'name': node.name,
        'server_id': node.server_id,
        'last_seen': node.last_seen.isoformat(),
        'cpu_usage': node.cpu_usage,
        'memory_usage': node.memory_usage,
        'disk_usage': node.disk_usage
    } for node in nodes])


@app.route('/add')
def add_page():
    if not session.get('logged_in'):
        return redirect('/login')
    return render_template('add.html')


@app.route('/api/nodes', methods=['POST'])
def add_node():
    if not session.get('logged_in'):
        return jsonify({'error': '請先登入'}), 401
        
    data = request.json
    if not data or not data.get('name'):
        return jsonify({'error': '節點名稱不能為空'}), 400
        
    server_id = str(uuid.uuid4())
    node = Node(
        name=data['name'],
        server_id=server_id
    )
    db.session.add(node)
    db.session.commit()
    return jsonify({'message': 'Node added successfully', 'id': node.id, 'server_id': server_id})


def require_token(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'No token provided'}), 401
        
        token = auth_header.split(' ')[1]
        if token != API_TOKEN:
            return jsonify({'error': 'Invalid token'}), 401
            
        return f(*args, **kwargs)
    return decorated_function


@app.route('/api/nodes/<server_id>/status', methods=['POST'])
@require_token
def update_node_status(server_id):
    node = Node.query.filter_by(server_id=server_id).first_or_404()
    data = request.json
    node.cpu_usage = data.get('cpu_usage')
    node.memory_usage = data.get('memory_usage')
    node.disk_usage = data.get('disk_usage')
    node.last_seen = datetime.utcnow()
    db.session.commit()
    return jsonify({'message': 'Status updated successfully'})


@app.route('/api/nodes/<int:node_id>', methods=['DELETE'])
def delete_node(node_id):
    if not session.get('logged_in'):
        return jsonify({'error': '請先登入'}), 401
        
    data = request.json
    if not data or not data.get('password') or data['password'] != config.passwd:
        return jsonify({'error': '密碼錯誤'}), 401
        
    node = Node.query.get_or_404(node_id)
    db.session.delete(node)
    db.session.commit()
    return jsonify({'message': '節點已刪除'})

@app.route('/edit')
def edit_page():
    if not session.get('logged_in'):
        return redirect('/login')
    return render_template('edit.html')

@app.route('/api/nodes/<int:node_id>', methods=['GET'])
def get_node(node_id):
    if not session.get('logged_in'):
        return jsonify({'error': '請先登入'}), 401
        
    node = Node.query.get_or_404(node_id)
    return jsonify({
        'id': node.id,
        'name': node.name,
        'server_id': node.server_id,
        'last_seen': node.last_seen.isoformat(),
        'cpu_usage': node.cpu_usage,
        'memory_usage': node.memory_usage,
        'disk_usage': node.disk_usage
    })

@app.route('/api/nodes/<int:node_id>', methods=['PUT'])
def update_node(node_id):
    if not session.get('logged_in'):
        return jsonify({'error': '請先登入'}), 401
        
    data = request.json
    if not data or not data.get('name'):
        return jsonify({'error': '節點名稱不能為空'}), 400
        
    node = Node.query.get_or_404(node_id)
    node.name = data['name']
    db.session.commit()
    return jsonify({'message': '節點更新成功', 'id': node.id})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True,host='0.0.0.0',port=config.port)