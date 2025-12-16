# backend/app.py
from flask import Flask
from flask_cors import CORS
from config import Config
from database import db
from flask_migrate import Migrate
import os

migrate = Migrate()

AVATAR_UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'avatars')
os.makedirs(AVATAR_UPLOAD_FOLDER, exist_ok=True)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app, supports_credentials=True)
    db.init_app(app)

    # 初始化 Flask-Migrate
    migrate.init_app(app, db)

    # 启用 SQLite 外键支持
    from sqlalchemy import event
    from sqlalchemy.engine import Engine

    @event.listens_for(Engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    # 注册蓝图
    from api.auth_bp import auth_bp
    from api.post_bp import post_bp
    from api.user_bp import user_bp
    from api.comment_bp import comment_bp
    from api.interaction_bp import interaction_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(post_bp, url_prefix='/api/posts')
    app.register_blueprint(user_bp, url_prefix='/api/user')
    app.register_blueprint(comment_bp, url_prefix='/api')
    app.register_blueprint(interaction_bp, url_prefix='/api')
    
    return app

app = create_app()

if __name__ == '__main__':
    
    with app.app_context():
        from models import User, Post, Comment, Like
 
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=True
    )