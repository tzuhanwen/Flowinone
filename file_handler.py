import os
from datetime import datetime
from urllib.parse import quote
import mimetypes
import src.eagle_api as EG
from flask import abort
from config import DB_route_internal, DB_route_external


IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
VIDEO_EXTENSIONS = {"mp4", "mov", "avi", "mkv", "webm", "m4v"}
DEFAULT_THUMBNAIL_ROUTE = "/static/default_thumbnail.svg"
DEFAULT_VIDEO_THUMBNAIL_ROUTE = "/static/default_video_thumbnail.svg"


def _normalize_source(src):
    return "external" if src == "external" else "internal"


def _normalize_slashes(path):
    return path.replace("\\", "/")


def _is_image_file(filename):
    return os.path.splitext(filename)[1].lower().lstrip(".") in IMAGE_EXTENSIONS


def _is_video_file(filename):
    return os.path.splitext(filename)[1].lower().lstrip(".") in VIDEO_EXTENSIONS


def _build_file_route(abs_path, src):
    normalized = _normalize_slashes(abs_path)
    if src == "external":
        return f"/serve_image/{normalized}"
    return f"/{normalized}"


def _build_folder_url(rel_path, src):
    normalized_src = _normalize_source(src)
    normalized_path = _normalize_slashes(rel_path or "")
    quoted_path = quote(normalized_path, safe="/")

    if normalized_src == "external":
        return f"/both/{quoted_path}" if quoted_path else "/"

    if quoted_path:
        return f"/both/{quoted_path}/?src=internal"
    return "/?src=internal"


def _build_video_url(rel_path, src):
    normalized = _normalize_slashes(rel_path)
    quoted_path = quote(normalized, safe="/")
    query = "?src=external" if _normalize_source(src) == "external" else "?src=internal"
    return f"/video/{quoted_path}{query}"


def _find_video_thumbnail(abs_video_path, src):
    base, _ = os.path.splitext(abs_video_path)
    candidates = []
    for ext in IMAGE_EXTENSIONS:
        candidates.append(f"{base}_thumbnail.{ext}")
        candidates.append(f"{base}.{ext}")

    for candidate in candidates:
        if os.path.isfile(candidate):
            return _build_file_route(candidate, src)

    return DEFAULT_VIDEO_THUMBNAIL_ROUTE


def _find_directory_thumbnail(abs_folder_path, src):
    for root, _, files in os.walk(abs_folder_path):
        for file_name in sorted(files):
            abs_file_path = os.path.join(root, file_name)
            if _is_image_file(file_name):
                return _build_file_route(abs_file_path, src)
            if _is_video_file(file_name):
                return _find_video_thumbnail(abs_file_path, src)
    return DEFAULT_THUMBNAIL_ROUTE


def _build_folder_entry(display_name, abs_path, rel_path, src):
    return {
        "name": display_name,
        "thumbnail_route": _find_directory_thumbnail(abs_path, src),
        "url": _build_folder_url(rel_path, src),
        "item_path": os.path.abspath(abs_path)
    }


def _build_image_entry(display_name, abs_path, src):
    file_route = _build_file_route(abs_path, src)
    return {
        "name": display_name,
        "thumbnail_route": file_route,
        "url": file_route,
        "item_path": os.path.abspath(abs_path)
    }


def _build_video_entry(display_name, abs_path, rel_path, src):
    return {
        "name": display_name,
        "thumbnail_route": _find_video_thumbnail(abs_path, src),
        "url": _build_video_url(rel_path, src),
        "item_path": os.path.abspath(abs_path)
    }


def _collect_directory_entries(base_dir, relative_path, src):
    normalized_src = _normalize_source(src)
    target_dir = os.path.join(base_dir, relative_path) if relative_path else base_dir
    if not os.path.isdir(target_dir):
        abort(404)

    try:
        entries = sorted(os.listdir(target_dir))
    except FileNotFoundError:
        abort(404)

    folders, files = [], []
    for entry in entries:
        if entry.startswith("."):
            continue
        abs_entry = os.path.join(target_dir, entry)
        rel_entry = os.path.relpath(abs_entry, base_dir)
        rel_entry = _normalize_slashes(rel_entry)

        if os.path.isdir(abs_entry):
            folders.append(_build_folder_entry(entry, abs_entry, rel_entry, normalized_src))
        elif _is_image_file(entry):
            files.append(_build_image_entry(entry, abs_entry, normalized_src))
        elif _is_video_file(entry):
            files.append(_build_video_entry(entry, abs_entry, rel_entry, normalized_src))

    return folders + files


def _human_readable_size(num_bytes):
    if num_bytes < 1024:
        return f"{num_bytes} B"
    units = ["KB", "MB", "GB", "TB", "PB"]
    size = float(num_bytes)
    for unit in units:
        size /= 1024.0
        if size < 1024.0 or unit == units[-1]:
            return f"{size:.2f} {unit}"

    return f"{size:.2f} PB"


def _safe_relative_path(path):
    if not path:
        return ""
    normalized = _normalize_slashes(os.path.normpath(path))
    if normalized.startswith("../") or normalized == "..":
        abort(403)
    if os.path.isabs(path):
        abort(403)
    return normalized

def get_all_folders_info(src):
    """
    取得 DB_route 內的所有子資料夾資訊，符合 EAGLE API 格式
    src: internal or external
    """

    normalized_src = _normalize_source(src)
    base_dir = DB_route_external if normalized_src == "external" else DB_route_internal

    if not os.path.isdir(base_dir):
        abort(404)

    metadata = {
        "name": "All Collections",
        "category": "collections",
        "tags": ["collection", "group", "Main"],
        "path": "/" if normalized_src == "external" else "/?src=internal",
        "thumbnail_route": DEFAULT_THUMBNAIL_ROUTE,
        "filesystem_path": os.path.abspath(base_dir)
    }

    data = _collect_directory_entries(base_dir, "", normalized_src)
    return metadata, data

def get_folder_images(folder_path, src=None):
    """
    取得指定資料夾內的所有圖片，符合 EAGLE API 格式
    從任意資料夾（base_dir + folder_path）中取得圖片
    """

    normalized_src = _normalize_source(src)
    safe_folder_path = _safe_relative_path(folder_path)
    base_dir = DB_route_external if normalized_src == "external" else DB_route_internal

    target_dir = os.path.join(base_dir, safe_folder_path) if safe_folder_path else base_dir
    if not os.path.isdir(target_dir):
        abort(404)
    
    metadata = {
        "name": os.path.basename(safe_folder_path.rstrip("/")) if safe_folder_path else os.path.basename(os.path.normpath(base_dir)),
        "category": "folder",
        "tags": ["grid", "slide", "test_tag_default"],
        "path": _build_folder_url(safe_folder_path, normalized_src),
        "thumbnail_route": _find_directory_thumbnail(target_dir, normalized_src),
        "filesystem_path": os.path.abspath(target_dir)
    }

    data = _collect_directory_entries(base_dir, safe_folder_path, normalized_src)
    return metadata, data


def get_video_details(video_path, src=None):
    """
    取得影片詳細資訊與播放所需路徑。
    """
    normalized_src = _normalize_source(src)
    safe_video_path = _safe_relative_path(video_path)
    base_dir = DB_route_external if normalized_src == "external" else DB_route_internal
    target_path = os.path.join(base_dir, safe_video_path) if safe_video_path else base_dir

    if not os.path.isfile(target_path) or not _is_video_file(target_path):
        abort(404)

    file_name = os.path.basename(safe_video_path) if safe_video_path else os.path.basename(target_path)
    file_size = os.path.getsize(target_path)
    modified_time = datetime.fromtimestamp(os.path.getmtime(target_path))
    thumbnail_route = _find_video_thumbnail(target_path, normalized_src)
    source_url = _build_file_route(target_path, normalized_src)
    mime_type = mimetypes.guess_type(file_name)[0] or "video/mp4"

    metadata = {
        "name": file_name,
        "category": "video",
        "tags": [],
        "path": _build_video_url(safe_video_path, normalized_src),
        "thumbnail_route": thumbnail_route,
        "filesystem_path": os.path.abspath(os.path.dirname(target_path))
    }

    parent_relative = _normalize_slashes(os.path.dirname(safe_video_path))
    parent_url = _build_folder_url(parent_relative, normalized_src) if parent_relative else ("/" if normalized_src == "external" else "/?src=internal")

    video_data = {
        "name": file_name,
        "relative_path": safe_video_path,
        "source_url": source_url,
        "thumbnail_route": thumbnail_route,
        "mime_type": mime_type,
        "size_bytes": file_size,
        "size_display": _human_readable_size(file_size),
        "modified_time": modified_time.strftime("%Y-%m-%d %H:%M"),
        "parent_url": parent_url,
        "download_url": source_url
    }

    return metadata, video_data

def get_eagle_folders():
    """
    獲取 Eagle API 提供的所有資料夾資訊
    """
    response = EG.EAGLE_get_library_info()
    if response.get("status") != "success":
        abort(500, description=f"Failed to fetch Eagle folders: {response.get('data')}")

    metadata = {
        "name": "All Eagle Folders",
        "category": "collections",
        "tags": ["eagle", "folders"],
        "path": "/EAGLE_folder",
        "thumbnail_route": DEFAULT_THUMBNAIL_ROUTE,
        "filesystem_path": EG.EAGLE_get_current_library_path()
    }

    data = []
    for folder in response.get("data", {}).get("folders", []):
        folder_id = folder.get("id")
        folder_name = folder.get("name", "Unnamed Folder")

        # 取得 Eagle 資料夾內的縮圖
        folder_response = EG.EAGLE_list_items(folders=[folder_id])
        image_items = folder_response.get("data", [])
        image_items.sort(key=lambda x: x.get("name", ""))
        thumbnail_path = f"/serve_image/{EG.EAGLE_get_current_library_path()}/images/{image_items[0]['id']}.info/{image_items[0]['name']}.{image_items[0]['ext']}" if image_items else DEFAULT_THUMBNAIL_ROUTE

        data.append({
            "name": folder_name,
            "id": folder_id,
            "url": f"/EAGLE_folder/{folder_id}/",
            "thumbnail_route": thumbnail_path,
            "item_path": None
        })

    return metadata, data

def get_eagle_images_by_folderid(eagle_folder_id):
    """
    獲取 Eagle API 提供的指定資料夾內的圖片資訊，符合 EAGLE API 格式
    """
    response = EG.EAGLE_list_items(folders=[eagle_folder_id])
    if response.get("status") != "success":
        abort(500, description=f"Failed to fetch images from Eagle folder: {response.get('data')}")

    # df = EG.EAGLE_get_folders_df()
    # row = df[df["id"] == eagle_folder_id]  ###並沒有recursive地找...
    # if row.empty:
    #     return []
    # folder_name = row.iloc[0]["name"]
    folder_name = eagle_folder_id

    metadata = {
        "name": folder_name,
        "category": "folder",
        "tags": ["eagle", "images"],
        "path": f"/EAGLE_folder/{eagle_folder_id}",
        "thumbnail_route": DEFAULT_THUMBNAIL_ROUTE,
        "filesystem_path": EG.EAGLE_get_current_library_path()
    }
    image_items = response.get("data", [])
    data = _format_eagle_items(image_items)
    return metadata, data

def get_eagle_images_by_tag(target_tag):
    """
    從 Eagle API 獲取所有帶有指定標籤的圖片，符合 EAGLE API 格式。

    Args:
        target_tag (str): 要查詢的標籤。

    Returns:
        (metadata, data): 以符合 EAGLE API 樣式的 `metadata` 與 `data`
    """
    # 從 Eagle API 獲取帶有該標籤的圖片
    response = EG.EAGLE_list_items(tags=[target_tag], orderBy="CREATEDATE")
    if response.get('status') == 'error':
        abort(500, description=f"Error fetching images with tag '{target_tag}': {response.get('data')}")

    # 設定 metadata
    metadata = {
        "name": f"Images with Tag: {target_tag}",
        "category": "tag",
        "tags": [target_tag],
        "path": f"/EAGLE_tag/{target_tag}",
        "thumbnail_route": DEFAULT_THUMBNAIL_ROUTE,
        "filesystem_path": EG.EAGLE_get_current_library_path()
    }

    image_items = response.get("data", [])
    data = _format_eagle_items(image_items)
    return metadata, data

def _format_eagle_items(image_items):
    """
    將 Eagle 圖片清單格式化成 EAGLE API 樣式的 data list。
    """
    image_items.sort(key=lambda x: x.get("name", "")) # 按名稱排序
    data = []

    base = EG.EAGLE_get_current_library_path()
    for image in image_items:
        image_id = image.get("id")
        image_name = image.get("name", "unknown")
        image_ext = image.get("ext", "jpg")
        image_path = f"/serve_image/{base}/images/{image_id}.info/{image_name}.{image_ext}"

        # 特別處理影片縮圖
        if image_ext == "mp4":
            thumbnail_route = f"/serve_image/{base}/images/{image_id}.info/{image_name}_thumbnail.png"
        else:
            thumbnail_route = image_path

        data.append({
            "name": image_name,
            "url": image_path,
            "thumbnail_route": thumbnail_route,
            "item_path": os.path.abspath(os.path.join(base, "images", f"{image_id}.info", f"{image_name}.{image_ext}"))
        })

    return data

def get_subfolders_info(folder_id):
    """
    根據指定的 folder_id，取出其 children（子資料夾 id list），
    並組成符合前端展示格式的 list of dict。
    """
    df = EG.EAGLE_get_folders_df()

    # 找出指定 folder row
    row = df[df["id"] == folder_id]
    if row.empty:
        return []

    children_infos = row.iloc[0]["children"]  # 是 list
    result = []

    for child_info in children_infos:
        child_id = child_info["id"]
        # child_row = df[df["id"] == child_info["id"]]
        # if child_row.empty:
            # continue

        # child = child_row.iloc[0]
        sub_name = child_info.get("name", f"(unnamed-{child_id})")
        path = f"/EAGLE_folder/{child_id}"

        # 嘗試取一張圖作為縮圖
        folder_response = EG.EAGLE_list_items(folders=[child_id])
        thumbnail_route = DEFAULT_THUMBNAIL_ROUTE
        if folder_response.get("status") == "success" and folder_response.get("data"):
            first_img = folder_response["data"][0]
            image_id = first_img["id"]
            image_name = first_img["name"]
            image_ext = first_img["ext"]
            base = EG.EAGLE_get_current_library_path()
            thumbnail_route = f"/serve_image/{base}/images/{image_id}.info/{image_name}.{image_ext}"

        result.append({
            "name": f"📁 {sub_name}",
            "url": path,
            "thumbnail_route": thumbnail_route,
            "item_path": None
        })

    return result
