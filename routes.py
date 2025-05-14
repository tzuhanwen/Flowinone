import os
import random
from flask import Flask, render_template, abort, send_from_directory, request
from file_handler import get_folders_info, get_folder_images, get_eagle_folders, get_eagle_images_by_folderid, get_eagle_images_by_tag
from config import index_folder, DB_route

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

        metadata, data = get_folders_info(source)
        return render_template('index.html', metadata=metadata, data=data)

    @app.route('/both/<path:folder_path>/')
    def view_both(folder_path):
        """取得指定資料夾內的所有圖片"""

        source = request.args.get('src', 'external')

        if source == 'external':
            base_dir = DB_route
        else:
            base_dir = index_folder  # static 裡的資料夾

        metadata, data = get_folder_images(folder_path, base_dir, source)
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

    @app.route('/EAGLE_folder/')
    def list_all_eagle_folder():
        """列出所有 Eagle 資料夾，並符合 EAGLE API 樣式"""
        metadata, data = get_eagle_folders()
        return render_template("index.html", metadata=metadata, data=data)

    @app.route('/EAGLE_folder/<eagle_folder_id>/')
    def view_eagle_folder(eagle_folder_id):
        """顯示指定 Eagle 資料夾 ID 下的所有圖片"""
        metadata, data = get_eagle_images_by_folderid(eagle_folder_id)
        return render_template('view_both.html', metadata=metadata, data=data)

    @app.route('/serve_image/<path:image_path>')
    def serve_image_by_full_path(image_path):
        """提供靜態圖片服務"""
        directory, filename = os.path.split(image_path)
        directory = '/' + directory
        return send_from_directory(directory, filename)
    
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
        return render_template('view_both.html', metadata=metadata, data=data)