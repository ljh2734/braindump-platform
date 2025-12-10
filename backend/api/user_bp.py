# backend/api/user_bp.py
"""
用户 API 蓝图：处理用户相关 HTTP 请求
- 头像上传（调用 user_service）
"""

import os
from flask import Blueprint, request, jsonify, current_app
from utils.auth_utils import login_required
from services.user_service import save_avatar, update_user_avatar, AvatarUploadError


user_bp = Blueprint('user', __name__)


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

        return jsonify({
            'message': '头像上传成功',
            'avatar_url': avatar_url
        }), 200

    except AvatarUploadError as e:
        # 业务逻辑错误（如格式、大小、文件系统问题）
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        # 未预期错误（记录日志，生产环境应使用 logging）
        print(f"[Avatar Upload] Unexpected error: {repr(e)}")
        return jsonify({'error': '服务器内部错误'}), 500