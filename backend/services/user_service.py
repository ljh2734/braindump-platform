# backend/services/user_service.py
import os
from werkzeug.utils import secure_filename
from utils.auth_utils import authenticate_user, register_user, encode_auth_token
from database import db
from models import User


# ======================
# 认证与注册服务
# ======================

def login_service(email, password):
    """登录服务：返回 token 或错误"""
    user = authenticate_user(email, password)
    if not user:
        return None, "Invalid email or password."
    token = encode_auth_token(user.id)
    return {'token': token, 'user': user.to_dict()}, None


def register_service(email, username, password):
    """注册服务：返回用户信息或错误"""
    try:
        user = register_user(email, username, password)
        return user.to_dict(), None
    except ValueError as e:
        return None, str(e)


# ======================
# 头像上传服务
# ======================

class AvatarUploadError(Exception):
    """头像上传专用异常"""
    pass


def save_avatar(user_id, file, upload_folder, max_size=2 * 1024 * 1024, allowed_extensions={'png', 'jpg', 'jpeg', 'gif'}):
    """
    安全地保存用户头像
    
    :param user_id: 用户 ID
    :param file: Flask FileStorage 对象
    :param upload_folder: 上传目标目录（绝对路径）
    :param max_size: 最大文件大小（字节）
    :param allowed_extensions: 允许的扩展名集合
    :return: avatar_url (相对 URL)
    :raises AvatarUploadError: 上传失败时抛出
    """
    if not file or not file.filename:
        raise AvatarUploadError("No file provided")

    filename = file.filename
    ext = filename.rsplit('.', 1)[-1].lower()

    if ext not in allowed_extensions:
        raise AvatarUploadError("Invalid file type. Only PNG, JPG, JPEG, GIF allowed.")

    # 校验大小
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    if size > max_size:
        raise AvatarUploadError(f"File too large. Max size is {max_size // 1024} KB.")

    # 安全命名：完全由后端控制
    safe_filename = f"user_{user_id}.{ext}"
    filepath = os.path.join(upload_folder, safe_filename)

    os.makedirs(upload_folder, exist_ok=True)

    try:
        file.save(filepath)
    except Exception as e:
        raise AvatarUploadError(f"Failed to save file: {str(e)}")

    return f"/static/uploads/avatars/{safe_filename}"


def update_user_avatar(user_id, avatar_url):
    """更新用户头像 URL 到数据库"""
    user = User.query.get(user_id)
    if not user:
        raise AvatarUploadError("User not found")
    user.avatar_url = avatar_url
    db.session.commit()
    return user