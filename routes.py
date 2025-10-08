import os
import platform
import subprocess
from urllib.parse import unquote
from flask import Flask, render_template, abort, send_from_directory, request, redirect, url_for
from file_handler import (
    get_all_folders_info,
    get_folder_images,
    get_video_details,
    get_eagle_folders,
    get_eagle_images_by_folderid,
    get_eagle_images_by_tag,
    get_eagle_tags,
    get_eagle_video_details,
    get_subfolders_info,
)
from config import DB_route_internal, DB_route_external


def _path_is_within_roots(target_path, roots):
    """Ensure the requested path stays inside one of the configured roots."""
    try:
        normalized_target = os.path.abspath(target_path)
        for root in roots:
            if not root:
                continue
            normalized_root = os.path.abspath(root)
            if os.path.commonpath([normalized_target, normalized_root]) == normalized_root:
                return True
    except ValueError:
        return False
    return False


def _open_in_file_manager(target_path):
    """Open a folder in the host file manager."""
    system = platform.system()
    if system == "Darwin":
        subprocess.Popen(["open", target_path])
    elif system == "Windows":
        os.startfile(target_path)  # type: ignore[attr-defined]
    else:
        subprocess.Popen(["xdg-open", target_path])

def register_routes_debug(app):
    @app.route('/debug/')
    def debug_print():
        # df_folders_info = EG.EAGLE_get_folders_df()
        # print(df_folders_info.shape)
        # print(df_folders_info.columns)
        df_to_post = [
            {'author': 'Lynn','title': 'Blog Post 1','content': 'First post content','date_posted': 'September 3, 2018'},
            {'author': 'Lydia','title': 'Blog Post 2','content': 'Second post content','date_posted': 'September 6, 2018'}
            ]
        return render_template('test_arg.html', title='All in One', df_to_post=df_to_post)

def register_routes(app):
    """
    註冊 Flask 路由
    """

    @app.route('/')
    def index():
        """獲取所有資料夾，並符合 EAGLE API 格式"""

        source = request.args.get('src', 'external')

        metadata, data = get_all_folders_info(source)
        return render_template('index.html', metadata=metadata, data=data)
    
    @app.route('/open_path/')
    def open_filesystem_path():
        """Open the requested path in the local file manager."""
        raw_path = request.args.get('path')
        if not raw_path:
            abort(400)

        decoded_path = os.path.abspath(unquote(raw_path))
        if not os.path.exists(decoded_path):
            abort(404)

        allowed_roots = [DB_route_external, DB_route_internal]
        if not _path_is_within_roots(decoded_path, allowed_roots):
            abort(403)

        target_directory = decoded_path if os.path.isdir(decoded_path) else os.path.dirname(decoded_path)
        if not target_directory:
            abort(404)

        try:
            _open_in_file_manager(target_directory)
        except Exception as exc:
            abort(500, description=f"Failed to open path: {exc}")

        return redirect(request.referrer or url_for('index'))

    @app.route('/both/<path:folder_path>/')
    def view_both(folder_path):
        """
        取得指定資料夾內的所有圖片
        src: internal or external
        """
        source = request.args.get('src', 'external')

        metadata, data = get_folder_images(folder_path, source)
        return render_template('view_both.html', metadata=metadata, data=data)

    @app.route('/grid/<path:folder_path>/')
    def view_grid(folder_path):
        """取得指定資料夾內的所有圖片（Grid 模式）"""
        metadata, data = get_folder_images(folder_path)
        return render_template('view_grid.html', metadata=metadata, data=data)

    @app.route('/slide/<path:folder_path>/')
    def view_slide(folder_path):
        """取得指定資料夾內的所有圖片（Slide 模式）"""
        metadata, data = get_folder_images(folder_path)
        return render_template('view_slide.html', metadata=metadata, data=data)

    @app.route('/EAGLE_folders/')
    def list_all_eagle_folder():
        """列出所有 Eagle 資料夾，並符合 EAGLE API 樣式"""
        metadata, data = get_eagle_folders()
        return render_template("index.html", metadata=metadata, data=data)

    @app.route('/EAGLE_tags/')
    def list_eagle_tags():
        """列出 Eagle 中的所有標籤並提供連結"""
        metadata, tags = get_eagle_tags()
        return render_template("eagle_tags.html", metadata=metadata, tags=tags)

    @app.route('/EAGLE_folder/<eagle_folder_id>/')
    def view_eagle_folder(eagle_folder_id):
        """顯示指定 Eagle 資料夾 ID 下的所有圖片"""
        metadata, data = get_eagle_images_by_folderid(eagle_folder_id)
        
        # 加入子資料夾為類似圖片格式
        subfolders = get_subfolders_info(eagle_folder_id)
        data = subfolders + data

        current_url = request.full_path
        if current_url and current_url.endswith('?'):
            current_url = current_url[:-1]

        for item in data:
            if item.get("media_type") == "video" and item.get("id"):
                item["url"] = url_for("view_eagle_video", item_id=item["id"], return_to=current_url)
        
        return render_template('view_both.html', metadata=metadata, data=data)

    @app.route('/serve_image/<path:image_path>')
    def serve_image_by_full_path(image_path):
        """提供靜態圖片服務"""
        directory, filename = os.path.split(image_path)
        directory = '/' + directory
        return send_from_directory(directory, filename)

    @app.route('/video/<path:video_path>')
    def view_video(video_path):
        """顯示影片播放頁面"""
        source = request.args.get('src', 'external')
        metadata, video = get_video_details(video_path, source)
        return render_template('video_player.html', metadata=metadata, video=video)
    
    @app.route('/EAGLE_tag/<target_tag>/')
    def view_images_by_tag(target_tag):
        """
        顯示所有帶有指定標籤的圖片，並符合 EAGLE API 格式。

        Args:
            target_tag (str): 要查詢的標籤。

        Returns:
            渲染的 HTML 頁面，顯示所有具有該標籤的圖片。
        """
        metadata, data = get_eagle_images_by_tag(target_tag)

        current_url = request.full_path
        if current_url and current_url.endswith('?'):
            current_url = current_url[:-1]

        for item in data:
            if item.get("media_type") == "video" and item.get("id"):
                item["url"] = url_for("view_eagle_video", item_id=item["id"], return_to=current_url)

        return render_template('view_both.html', metadata=metadata, data=data)

    @app.route('/EAGLE_video/<item_id>/')
    def view_eagle_video(item_id):
        """顯示 Eagle 影片的詳細資訊與播放器頁面"""
        metadata, video = get_eagle_video_details(item_id)
        return_to = request.args.get("return_to")
        if return_to:
            video["parent_url"] = return_to
        else:
            video["parent_url"] = request.referrer or url_for("index")
        return render_template('video_player.html', metadata=metadata, video=video)
