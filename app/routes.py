from flask import render_template, flash, redirect, url_for, request, jsonify, send_from_directory, Blueprint
from flask_login import login_user, logout_user, current_user, login_required
from app import db, login_manager # Mantenha essas importações
from app.models import User, WorkSession, ActivityLog, Screenshot
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import os
from flask import current_app # Adicionado para garantir acesso a app.config

# --- Crie um Blueprint para as suas rotas ---
main_bp = Blueprint('main', __name__)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- ROTAS DO PAINEL ADMINISTRATIVO ---

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard')) # CORRIGIDO: adicionado 'main.'
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user is None or not user.check_password(password) or not user.is_admin:
            flash('Usuário ou senha inválidos, ou você não é um administrador.')
            return redirect(url_for('main.login')) # CORRIGIDO: adicionado 'main.'
        login_user(user, remember=True)
        return redirect(url_for('main.dashboard')) # CORRIGIDO: adicionado 'main.'
    return render_template('login.html', title='Login')

@main_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.login')) # CORRIGIDO: adicionado 'main.'

@main_bp.route('/')
@main_bp.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_admin: return redirect(url_for('main.login')) # CORRIGIDO: adicionado 'main.'

    page = request.args.get('page', 1, type=int)
    employees = User.query.filter_by(is_admin=False).paginate(page=page, per_page=10)
    return render_template('dashboard.html', title='Dashboard', employees=employees)

@main_bp.route('/employee/add', methods=['POST'])
@login_required
def add_employee():
    if not current_user.is_admin: return jsonify({'status': 'error', 'message': 'Acesso negado'}), 403

    full_name = request.form['full_name']
    username = request.form['username']
    password = request.form['password']

    if User.query.filter_by(username=username).first():
        flash(f'O nome de usuário "{username}" já existe.')
        return redirect(url_for('main.dashboard')) # CORRIGIDO: adicionado 'main.'

    new_user = User(full_name=full_name, username=username)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()
    flash('Colaborador adicionado com sucesso!')
    return redirect(url_for('main.dashboard')) # CORRIGIDO: adicionado 'main.'

@main_bp.route('/employee/<int:user_id>')
@login_required
def employee_details(user_id):
    if not current_user.is_admin: return redirect(url_for('main.login')) # CORRIGIDO: adicionado 'main.'

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

@main_bp.route('/session/<int:session_id>')
@login_required
def session_details(session_id):
    if not current_user.is_admin: return redirect(url_for('main.login')) # CORRIGIDO: adicionado 'main.'

    session = WorkSession.query.get_or_404(session_id)
    activities = ActivityLog.query.filter_by(session_id=session_id).order_by(ActivityLog.timestamp.desc()).all()
    screenshots = Screenshot.query.filter_by(session_id=session_id).order_by(Screenshot.timestamp.desc()).all()

    return render_template('session_details.html', title='Detalhes da Sessão', session=session, activities=activities, screenshots=screenshots)

@main_bp.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)
@app.route('/employee/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_employee(user_id):
    if not current_user.is_admin: return redirect(url_for('login'))
    employee = User.query.get_or_404(user_id)
    if request.method == 'POST':
        employee.full_name = request.form['full_name']
        password = request.form['password']
        if password:
            employee.set_password(password)
        db.session.commit()
        flash('Colaborador atualizado com sucesso!')
        return redirect(url_for('dashboard'))
    return render_template('edit_employee.html', title='Editar Colaborador', employee=employee)

@app.route('/employee/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_employee(user_id):
    if not current_user.is_admin: return redirect(url_for('login'))
    employee = User.query.get_or_404(user_id)
    # O SQLAlchemy irá deletar em cascata os dados relacionados se configurado,
    # mas para garantir, podemos deletar manualmente os dados associados.
    WorkSession.query.filter_by(user_id=employee.id).delete()
    # Adicione aqui deleções para ActivityLog e Screenshot se necessário
    db.session.delete(employee)
    db.session.commit()
    flash('Colaborador e todos os seus dados foram excluídos com sucesso.')
    return redirect(url_for('dashboard'))

# --- ROTAS DA API PARA O CLIENTE WINDOWS ---

@main_bp.route('/api/authenticate', methods=['POST'])
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

@main_bp.route('/api/session/start', methods=['POST'])
def api_session_start():
    data = request.get_json()
    if not data or 'user_id' not in data:
        return jsonify({'status': 'error', 'message': 'user_id faltando'}), 400

    new_session = WorkSession(user_id=data['user_id'])
    db.session.add(new_session)
    db.session.commit()
    return jsonify({'status': 'success', 'session_id': new_session.id})

@main_bp.route('/api/session/end', methods=['POST'])
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

@main_bp.route('/api/log/activity', methods=['POST'])
def api_log_activity():
    data = request.get_json()
    if not data or 'session_id' not in data or 'activity_type' not in data or 'details' not in data or 'duration' not in data:
        return jsonify({'status': 'error', 'message': 'Dados de atividade incompletos'}), 400

    # LINHA 157 - DEVE TER EXATAMENTE 4 ESPAÇOS DE INDENTAÇÃO AQUI
    log = ActivityLog(
        session_id=data['session_id'], # DEVE TER EXATAMENTE 8 ESPAÇOS AQUI
        activity_type=data['activity_type'], # DEVE TER EXATAMENTE 8 ESPAÇOS AQUI
        details=data['details'], # DEVE TER EXATAMENTE 8 ESPAÇOS AQUI
        duration_seconds=data['duration'] # DEVE TER EXATAMENTE 8 ESPAÇOS AQUI
    ) # ESTE PARÊNTESES FINAL DEVE TER 4 ESPAÇOS DE INDENTAÇÃO
    db.session.add(log) # DEVE TER EXATAMENTE 4 ESPAÇOS DE INDENTAÇÃO
    db.session.commit() # DEVE TER EXATAMENTE 4 ESPAÇOS DE INDENTAÇÃO
    return jsonify({'status': 'success'}) # DEVE TER EXATAMENTE 4 ESPAÇOS DE INDENTAÇÃO
@main_bp.route('/api/upload/screenshot', methods=['POST'])
def api_upload_screenshot():
    if 'screenshot' not in request.files or 'session_id' not in request.form:
        return jsonify({'status': 'error', 'message': 'Dados do screenshot incompletos'}), 400

    file = request.files['screenshot']
    session_id = request.form['session_id']
    session = WorkSession.query.get(session_id)

    if file and session:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"user{session.user_id}_session{session_id}_{timestamp}.png"
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        new_screenshot = Screenshot(session_id=session_id, filepath=filename)
        db.session.add(new_screenshot)
        db.session.commit()
        return jsonify({'status': 'success', 'path': filename})
    return jsonify({'status': 'error', 'message': 'Arquivo ou sessão inválida'}), 400
@app.route('/api/heartbeat', methods=['POST'])
def api_heartbeat():
    data = request.get_json()
    if not data or 'session_id' not in data:
        return jsonify({'status': 'error', 'message': 'session_id faltando'}), 400

    session = WorkSession.query.get(data['session_id'])
    if session:
        session.last_heartbeat = datetime.utcnow()
        db.session.commit()
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'Sessão não encontrada'}), 404

@app.route('/api/users/status')
@login_required
def api_users_status():
    if not current_user.is_admin:
        return jsonify({'status': 'error', 'message': 'Acesso negado'}), 403

    online_users = {}
    # Encontra sessões ativas (sem end_time) cujo último heartbeat foi nos últimos 2 minutos
    cutoff_time = datetime.utcnow() - timedelta(minutes=2)
    active_sessions = WorkSession.query.filter(
        WorkSession.end_time.is_(None),
        WorkSession.last_heartbeat > cutoff_time
    ).all()

    for session in active_sessions:
        online_users[session.user_id] = {
            'status': 'online',
            'session_start_time': session.start_time.isoformat() + 'Z' # Formato ISO com Z para UTC
        }

    return jsonify(online_users)
