from flask import render_template, flash, redirect, url_for, request, jsonify, send_from_directory
from flask_login import login_user, logout_user, current_user, login_required
from app import create_app, db
from app.models import User, WorkSession, ActivityLog, Screenshot
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import os

app = create_app()

# --- ROTAS DO PAINEL ADMINISTRATIVO ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user is None or not user.check_password(password) or not user.is_admin:
            flash('Usuário ou senha inválidos, ou você não é um administrador.')
            return redirect(url_for('login'))
        login_user(user, remember=True)
        return redirect(url_for('dashboard'))
    return render_template('login.html', title='Login')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@app.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_admin: return redirect(url_for('login'))

    page = request.args.get('page', 1, type=int)
    employees = User.query.filter_by(is_admin=False).paginate(page=page, per_page=10)
    return render_template('dashboard.html', title='Dashboard', employees=employees)

@app.route('/employee/add', methods=['POST'])
@login_required
def add_employee():
    if not current_user.is_admin: return jsonify({'status': 'error', 'message': 'Acesso negado'}), 403

    full_name = request.form['full_name']
    username = request.form['username']
    password = request.form['password']

    if User.query.filter_by(username=username).first():
        flash(f'O nome de usuário "{username}" já existe.')
        return redirect(url_for('dashboard'))

    new_user = User(full_name=full_name, username=username)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()
    flash('Colaborador adicionado com sucesso!')
    return redirect(url_for('dashboard'))

@app.route('/employee/<int:user_id>')
@login_required
def employee_details(user_id):
    if not current_user.is_admin: return redirect(url_for('login'))

    user = User.query.get_or_404(user_id)

    # Filtros de data
    time_filter = request.args.get('filter', 'today')
    now = datetime.utcnow()
    if time_filter == 'week':
        start_date = now - timedelta(days=now.weekday())
    elif time_filter == 'month':
        start_date = now.replace(day=1)
    else: # today
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)

    sessions = WorkSession.query.filter(
        WorkSession.user_id == user_id,
        WorkSession.start_time >= start_date
    ).order_by(WorkSession.start_time.desc()).all()

    total_work_time = sum([(s.end_time - s.start_time).total_seconds() for s in sessions if s.end_time], 0)

    return render_template('employee_details.html', title=user.full_name, employee=user, sessions=sessions, total_work_time=total_work_time)

@app.route('/session/<int:session_id>')
@login_required
def session_details(session_id):
    if not current_user.is_admin: return redirect(url_for('login'))

    session = WorkSession.query.get_or_404(session_id)
    activities = ActivityLog.query.filter_by(session_id=session_id).order_by(ActivityLog.timestamp.desc()).all()
    screenshots = Screenshot.query.filter_by(session_id=session_id).order_by(Screenshot.timestamp.desc()).all()

    return render_template('session_details.html', title='Detalhes da Sessão', session=session, activities=activities, screenshots=screenshots)

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# --- ROTAS DA API PARA O CLIENTE WINDOWS ---

@app.route('/api/authenticate', methods=['POST'])
def api_authenticate():
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'status': 'error', 'message': 'Dados inválidos'}), 400

    user = User.query.filter_by(username=data['username']).first()
    if user and user.check_password(data['password']):
        if user.is_admin:
            return jsonify({'status': 'error', 'message': 'Login de admin não permitido no cliente'}), 403
        return jsonify({'status': 'success', 'user_id': user.id})

    return jsonify({'status': 'error', 'message': 'Credenciais inválidas'}), 401

@app.route('/api/session/start', methods=['POST'])
def api_session_start():
    data = request.get_json()
    if not data or 'user_id' not in data:
        return jsonify({'status': 'error', 'message': 'user_id faltando'}), 400

    new_session = WorkSession(user_id=data['user_id'])
    db.session.add(new_session)
    db.session.commit()
    return jsonify({'status': 'success', 'session_id': new_session.id})

@app.route('/api/session/end', methods=['POST'])
def api_session_end():
    data = request.get_json()
    if not data or 'session_id' not in data:
        return jsonify({'status': 'error', 'message': 'session_id faltando'}), 400

    session = WorkSession.query.get(data['session_id'])
    if session:
        session.end_time = datetime.utcnow()
        db.session.commit()
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'Sessão não encontrada'}), 404

@app.route('/api/log/activity', methods=['POST'])
def api_log_activity():
    data = request.get_json()
    if not data or 'session_id' not in data or 'activity_type' not in data or 'details' not in data or 'duration' not in data:
         return jsonify({'status': 'error', 'message': 'Dados de atividade incompletos'}), 400

    log = ActivityLog(
        session_id=data['session_id'],
        activity_type=data['activity_type'],
        details=data['details'],
        duration_seconds=data['duration']
    )
    db.session.add(log)
    db.session.commit()
    return jsonify({'status': 'success'})

@app.route('/api/upload/screenshot', methods=['POST'])
def api_upload_screenshot():
    if 'screenshot' not in request.files or 'session_id' not in request.form:
        return jsonify({'status': 'error', 'message': 'Dados do screenshot incompletos'}), 400

    file = request.files['screenshot']
    session_id = request.form['session_id']
    session = WorkSession.query.get(session_id)

    if file and session:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"user{session.user_id}_session{session_id}_{timestamp}.png"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        new_screenshot = Screenshot(session_id=session_id, filepath=filename)
        db.session.add(new_screenshot)
        db.session.commit()
        return jsonify({'status': 'success', 'path': filename})
    return jsonify({'status': 'error', 'message': 'Arquivo ou sessão inválida'}), 400
