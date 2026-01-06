"""
用户 API 蓝图：处理用户相关 HTTP 请求
- 头像上传（调用 user_service）
"""

import os
from flask import Blueprint, request, jsonify, current_app, send_from_directory
from utils.auth_utils import login_required
from services.user_service import save_avatar, update_user_avatar, AvatarUploadError
from database import db

user_bp = Blueprint('user', __name__)


@user_bp.route('/me')
@login_required
def get_current_user(current_user):
    user_data = current_user.to_dict()
    
    # 安全转换头像 URL：/static/... → /api/user/avatar/...
    avatar_url = user_data.get('avatar_url')
    if avatar_url and avatar_url.startswith('/static/uploads/avatars/'):
        filename = avatar_url.split('/')[-1]
        user_data['avatar_url'] = f"/api/user/avatar/{filename}"
    
    return jsonify(user_data), 200

@user_bp.route('/avatar', methods=['POST'])
@login_required
def upload_avatar(current_user):
    """
    安全上传用户头像
    - 文件名由后端生成（user_{id}.{ext}），不使用原始文件名
    - 限制类型：PNG/JPG/JPEG/GIF
    - 限制大小：2MB
    - 存储路径：/static/uploads/avatars/ （与代码分离）

    请求示例：
        POST /api/user/avatar
        Authorization: Bearer <token>
        Content-Type: multipart/form-data
        Body: avatar=<file>
    """
    # 1. 检查文件是否存在
    if 'avatar' not in request.files:
        return jsonify({'error': 'No file provided. Use field name "avatar".'}), 400

    file = request.files['avatar']
    if file.filename == '':
        return jsonify({'error': 'Empty filename.'}), 400

    # 2. 构建安全的上传目录（项目根目录下的 static/uploads/avatars）
    upload_folder = os.path.join(
        current_app.root_path,
        '..',  # 返回项目根目录
        'static',
        'uploads',
        'avatars'
    )

    try:
        # 3. 调用服务层：保存文件 + 返回 URL
        avatar_url = save_avatar(
            user_id=current_user.id,
            file=file,
            upload_folder=upload_folder,
            max_size=2 * 1024 * 1024,  # 2MB
            allowed_extensions={'png', 'jpg', 'jpeg', 'gif'}
        )

        # 4. 更新数据库
        update_user_avatar(current_user.id, avatar_url)

        # 提取文件名（如 "user_1.jpg"）
        filename = os.path.basename(avatar_url)

        # 构造正确的 API 路径
        api_avatar_url = f"/api/user/avatar/{filename}"

        return jsonify({
            'message': '头像上传成功',
            'avatar_url': api_avatar_url
        }), 200

    except AvatarUploadError as e:
        # 业务逻辑错误（如格式、大小、文件系统问题）
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        # 未预期错误（记录日志）
        print(f"[Avatar Upload] Unexpected error: {repr(e)}")
        return jsonify({'error': '服务器内部错误'}), 500
    

@user_bp.route('/username', methods=['PUT'])
@login_required
def update_username(current_user):
    """修改用户名"""
    data = request.get_json()
    new_username = data.get('username')
    
    if not new_username or len(new_username.strip()) < 2:
        return jsonify({'error': '昵称至少需要2个字符'}), 400
    
    new_username = new_username.strip()
    
    # 检查是否已存在
    from models import User
    if User.query.filter(User.username == new_username, User.id != current_user.id).first():
        return jsonify({'error': '该昵称已被占用'}), 400
    
    current_user.username = new_username
    db.session.commit()
    
    return jsonify({
        'message': '昵称更新成功',
        'username': current_user.username
    }), 200

# 提供用户头像
@user_bp.route('/avatar/<filename>')
def serve_user_avatar(filename):
    # 1. 安全校验：防止路径穿越
    if '..' in filename or filename.startswith('/') or filename.startswith('\\'):
        return jsonify({'error': 'Invalid filename'}), 400
    
    # 2. 校验扩展名
    allowed_ext = {'jpg', 'jpeg', 'png', 'gif'}
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    if ext not in allowed_ext:
        return jsonify({'error': 'Unsupported image format'}), 400

    # 3. 构建头像目录（与 save_avatar 逻辑一致）
    avatar_dir = os.path.join(
        current_app.root_path,
        '..',
        'static',
        'uploads',
        'avatars'
    )
    
    # 4. 发送文件
    try:
        return send_from_directory(avatar_dir, filename)
    except FileNotFoundError:
        return jsonify({'error': 'Avatar not found'}), 404
    
# 获取指定用户信息（公开信息）
@user_bp.route('/<int:user_id>')
def get_user_by_id(user_id):
    """
    获取用户公开信息（无需登录）
    返回: { id, username, avatar_url }
    """
    from models import User
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # 只返回安全字段（避免泄露 email 等）
    return jsonify({
        'id': user.id,
        'username': user.username,
        'avatar_url': user.avatar_url or '/static/default-avatar.png'
    }), 200