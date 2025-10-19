from flask import render_template,  redirect, url_for
from file_handler import (
    get_chrome_bookmarks,
    get_chrome_youtube_bookmarks,
)


def view_chrome_root():
    """預設顯示書籤列 (bookmark_bar)。"""
    return redirect(url_for('view_chrome_folder', folder_path='bookmark_bar'))


def view_chrome_folder(folder_path):
    """瀏覽 Chrome 書籤資料夾。"""
    metadata, data = get_chrome_bookmarks(folder_path)
    return render_template('view_both.html', metadata=metadata, data=data)


def view_chrome_youtube():
    """專門顯示 YouTube 書籤"""
    metadata, data = get_chrome_youtube_bookmarks()
    return render_template('view_both.html', metadata=metadata, data=data)


routes = [
    ['/chrome/', view_chrome_root],
    ['/chrome/<path:folder_path>/', view_chrome_folder],
    ['/chrome_youtube/', view_chrome_youtube],
]