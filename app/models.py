from app import db, login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    full_name = db.Column(db.String(120))
    is_admin = db.Column(db.Boolean, default=False)
    work_sessions = db.relationship('WorkSession', backref='employee', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class WorkSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, index=True, nullable=True)
    last_heartbeat = db.Column(db.DateTime, default=datetime.utcnow) # <- ADICIONE ESTA LINHA
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    activities = db.relationship('ActivityLog', backref='session', lazy='dynamic', cascade="all, delete-orphan")
    screenshots = db.relationship('Screenshot', backref='session', lazy='dynamic', cascade="all, delete-orphan")

class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    activity_type = db.Column(db.String(50)) # 'website' or 'program'
    details = db.Column(db.String(500))
    duration_seconds = db.Column(db.Integer)
    session_id = db.Column(db.Integer, db.ForeignKey('work_session.id'))

class Screenshot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    filepath = db.Column(db.String(200)) # Path to the image file
    session_id = db.Column(db.Integer, db.ForeignKey('work_session.id'))
