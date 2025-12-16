# init_db.py

from app import app  # 导入已创建的 app 实例
from database import db
from models import User, Post, Comment, Like, Question, Tag  # 确保所有模型被加载

def init_database():
    print("Dropping all tables...")
    db.drop_all()
    
    print("Creating all tables...")
    db.create_all()
    
    print("Database has been reinitialized!")

if __name__ == "__main__":
    with app.app_context():  # 必须在应用上下文中执行
        init_database()