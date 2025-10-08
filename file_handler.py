import os
import random
from collections import OrderedDict
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

def _build_image_url(rel_path, src):
    normalized_src = _normalize_source(src)
    normalized_path = _normalize_slashes(rel_path or "")
    quoted_path = quote(normalized_path, safe="/")
    query = "?src=external" if normalized_src == "external" else "?src=internal"
    if quoted_path:
        return f"/image/{quoted_path}{query}"
    return f"/image/{query}"


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


def _build_image_entry(display_name, abs_path, rel_path, src):
    file_route = _build_file_route(abs_path, src)
    return {
        "name": display_name,
        "thumbnail_route": file_route,
        "url": _build_image_url(rel_path, src),
        "item_path": os.path.abspath(abs_path),
        "media_type": "image"
    }


def _build_video_entry(display_name, abs_path, rel_path, src):
    return {
        "name": display_name,
        "thumbnail_route": _find_video_thumbnail(abs_path, src),
        "url": _build_video_url(rel_path, src),
        "item_path": os.path.abspath(abs_path),
        "media_type": "video"
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
            files.append(_build_image_entry(entry, abs_entry, rel_entry, normalized_src))
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

    parent_relative = _normalize_slashes(os.path.dirname(safe_video_path))
    parent_url = _build_folder_url(parent_relative, normalized_src) if parent_relative else ("/" if normalized_src == "external" else "/?src=internal")

    folder_links = []
    if parent_relative:
        folder_links.append({
            "name": os.path.basename(parent_relative) or parent_relative,
            "url": parent_url
        })
    else:
        root_name = os.path.basename(os.path.normpath(DB_route_external if normalized_src == "external" else DB_route_internal)) or "Root"
        folder_links.append({
            "name": root_name,
            "url": parent_url
        })

    similar_items = _build_local_similar_items(target_path, base_dir, normalized_src, limit=6)

    metadata = {
        "name": file_name,
        "category": "video",
        "tags": [],
        "path": _build_video_url(safe_video_path, normalized_src),
        "thumbnail_route": thumbnail_route,
        "filesystem_path": os.path.abspath(os.path.dirname(target_path)),
        "folders": folder_links,
        "similar": similar_items
    }

    video_data = {
        "name": file_name,
        "relative_path": safe_video_path,
        "source_url": source_url,
        "thumbnail_route": thumbnail_route,
        "original_url": None,
        "mime_type": mime_type,
        "size_bytes": file_size,
        "size_display": _human_readable_size(file_size),
        "modified_time": modified_time.strftime("%Y-%m-%d %H:%M"),
        "parent_url": parent_url,
        "download_url": source_url,
        "folders": folder_links
    }

    return metadata, video_data


def get_image_details(image_path, src=None):
    """
    取得圖片詳細資訊與展示所需路徑。
    """
    normalized_src = _normalize_source(src)
    safe_image_path = _safe_relative_path(image_path)
    base_dir = DB_route_external if normalized_src == "external" else DB_route_internal
    target_path = os.path.join(base_dir, safe_image_path) if safe_image_path else base_dir

    if not os.path.isfile(target_path) or not _is_image_file(target_path):
        abort(404)

    file_name = os.path.basename(safe_image_path) if safe_image_path else os.path.basename(target_path)
    file_size = os.path.getsize(target_path)
    modified_time = datetime.fromtimestamp(os.path.getmtime(target_path))
    source_url = _build_file_route(target_path, normalized_src)
    mime_type = mimetypes.guess_type(file_name)[0] or "image/jpeg"

    parent_relative = _normalize_slashes(os.path.dirname(safe_image_path))
    parent_url = _build_folder_url(parent_relative, normalized_src) if parent_relative else ("/" if normalized_src == "external" else "/?src=internal")

    folder_links = []
    if parent_relative:
        folder_links.append({
            "name": os.path.basename(parent_relative) or parent_relative,
            "url": parent_url
        })
    else:
        root_name = os.path.basename(os.path.normpath(DB_route_external if normalized_src == "external" else DB_route_internal)) or "Root"
        folder_links.append({
            "name": root_name,
            "url": parent_url
        })

    similar_items = _build_local_similar_items(target_path, base_dir, normalized_src, limit=6)

    metadata = {
        "name": file_name,
        "category": "image",
        "tags": [],
        "path": _build_image_url(safe_image_path, normalized_src),
        "thumbnail_route": source_url,
        "filesystem_path": os.path.abspath(target_path),
        "folders": folder_links,
        "similar": similar_items
    }

    image_data = {
        "name": file_name,
        "relative_path": safe_image_path,
        "source_url": source_url,
        "thumbnail_route": source_url,
        "original_url": None,
        "mime_type": mime_type,
        "size_bytes": file_size,
        "size_display": _human_readable_size(file_size),
        "modified_time": modified_time.strftime("%Y-%m-%d %H:%M"),
        "parent_url": parent_url,
        "download_url": source_url,
        "folders": folder_links
    }

    return metadata, image_data

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
    folder_links = _build_eagle_folder_links([eagle_folder_id])
    folder_name = folder_links[0]["name"] if folder_links else eagle_folder_id

    metadata = {
        "name": folder_name,
        "category": "folder",
        "tags": ["eagle", "images"],
        "path": f"/EAGLE_folder/{eagle_folder_id}",
        "thumbnail_route": DEFAULT_THUMBNAIL_ROUTE,
        "filesystem_path": EG.EAGLE_get_current_library_path(),
        "folders": folder_links
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

def get_eagle_tags():
    """
    從 Eagle API 取得所有標籤資訊，整理給前端使用。
    """
    response = EG.EAGLE_get_tags()
    if response.get("status") != "success":
        abort(500, description=f"Failed to fetch Eagle tags: {response.get('data')}")

    raw_data = response.get("data", [])
    if isinstance(raw_data, dict):
        tag_entries = raw_data.get("tags") or raw_data.get("data") or []
    else:
        tag_entries = raw_data or []

    tags = []
    for entry in tag_entries:
        if isinstance(entry, dict):
            tag_name = entry.get("name") or entry.get("tag") or entry.get("title")
            count_value = (
                entry.get("count")
                or entry.get("itemCount")
                or entry.get("itemsCount")
                or entry.get("childCount")
            )
        else:
            tag_name = str(entry)
            count_value = None

        if not tag_name:
            continue

        try:
            count = int(count_value) if count_value is not None else None
        except (TypeError, ValueError):
            count = None

        tags.append({
            "name": tag_name,
            "count": count
        })

    tags.sort(key=lambda item: item["name"].lower())

    metadata = {
        "name": "EAGLE Tags",
        "category": "tag-list",
        "tags": ["eagle", "tags"],
        "path": "/EAGLE_tags",
        "thumbnail_route": DEFAULT_THUMBNAIL_ROUTE,
        "filesystem_path": EG.EAGLE_get_current_library_path()
    }

    return metadata, tags

def search_eagle_items(keyword, limit=120):
    """透過 Eagle API 搜尋關鍵字並回傳格式化後的列表。"""
    response = EG.EAGLE_list_items(keyword=keyword, limit=limit, orderBy="CREATEDATE")
    if response.get("status") != "success":
        abort(500, description=f"Failed to search Eagle items: {response.get('data')}")

    raw_items = response.get("data", [])
    data = _format_eagle_items(raw_items)

    metadata = {
        "name": f"Search Results: {keyword}",
        "category": "search",
        "tags": [keyword],
        "path": f"/search?query={keyword}",
        "thumbnail_route": DEFAULT_THUMBNAIL_ROUTE,
        "filesystem_path": EG.EAGLE_get_current_library_path()
    }

    return metadata, data

def _extract_folder_ids(raw_folders):
    """
    將 Eagle 回傳的 folder 資訊整理成 id list。
    """
    if not raw_folders:
        return []

    ids = OrderedDict()

    if not isinstance(raw_folders, (list, tuple, set)):
        raw_folders = [raw_folders]

    for entry in raw_folders:
        folder_id = None
        if isinstance(entry, str):
            folder_id = entry
        elif isinstance(entry, dict):
            folder_id = (
                entry.get("id")
                or entry.get("folderId")
                or entry.get("folder_id")
            )
        if folder_id:
            folder_id = str(folder_id).strip()
            if folder_id:
                ids.setdefault(folder_id, None)

    return list(ids.keys())


def _build_eagle_folder_links(folder_ids):
    """
    將 folder id 轉換成可供前端使用的連結資訊。
    """
    folder_ids = _extract_folder_ids(folder_ids)
    if not folder_ids:
        return []

    try:
        df = EG.EAGLE_get_folders_df_all(flatten=True)
    except Exception:
        df = None

    lookup = {}
    if df is not None and getattr(df, "empty", True) is False:
        for _, row in df.iterrows():
            row_id = str(row.get("id") or "").strip()
            if not row_id:
                continue
            lookup[row_id] = row.get("name") or row_id

    links = []
    seen = OrderedDict()
    for folder_id in folder_ids:
        if folder_id in seen:
            continue
        seen[folder_id] = None
        folder_name = lookup.get(folder_id, folder_id)
        links.append({
            "id": folder_id,
            "name": folder_name,
            "url": f"/EAGLE_folder/{folder_id}/"
        })

    links.sort(key=lambda item: item["name"].lower())
    return links


def _normalize_item_tags(raw_tags):
    """
    將 Eagle item 的標籤轉換成字串 list。
    """
    if not raw_tags:
        return []

    tags = OrderedDict()
    if isinstance(raw_tags, str):
        raw_tags = [raw_tags]

    for entry in raw_tags:
        tag = None
        if isinstance(entry, str):
            tag = entry
        elif isinstance(entry, dict):
            tag = entry.get("name") or entry.get("tag")
        if tag:
            normalized = tag.strip()
            if normalized:
                tags.setdefault(normalized, None)

    return list(tags.keys())


def _build_local_similar_items(target_path, base_dir, src, limit=6):
    """
    根據同資料夾內容挑選相似的本地項目。
    """
    parent_dir = os.path.dirname(target_path)
    try:
        entries = os.listdir(parent_dir)
    except (FileNotFoundError, PermissionError):
        return []

    candidates = []
    for entry in entries:
        if entry.startswith("."):
            continue
        abs_entry = os.path.join(parent_dir, entry)
        if abs_entry == target_path or not os.path.isfile(abs_entry):
            continue

        try:
            rel_entry = os.path.relpath(abs_entry, base_dir)
        except ValueError:
            continue
        rel_entry = _normalize_slashes(rel_entry)

        if _is_image_file(entry):
            candidates.append({
                "id": rel_entry,
                "name": os.path.splitext(entry)[0] or entry,
                "path": _build_image_url(rel_entry, src),
                "thumbnail_route": _build_file_route(abs_entry, src),
                "media_type": "image"
            })
        elif _is_video_file(entry):
            candidates.append({
                "id": rel_entry,
                "name": os.path.splitext(entry)[0] or entry,
                "path": _build_video_url(rel_entry, src),
                "thumbnail_route": _find_video_thumbnail(abs_entry, src),
                "media_type": "video"
            })

    if not candidates:
        return []

    sample_size = min(limit, len(candidates))
    if sample_size <= 0:
        return []

    return random.sample(candidates, sample_size)


def _build_eagle_similar_items(current_item_id, tags, folder_ids, limit=6):
    """
    根據標籤或資料夾推薦相似項目。
    """
    candidate_map = OrderedDict()

    def _accumulate_from_response(response):
        if response.get("status") != "success":
            return
        for raw in response.get("data", []) or []:
            other_id = raw.get("id")
            if not other_id or other_id == current_item_id:
                continue
            if other_id in candidate_map:
                continue
            candidate_map[other_id] = raw

    primary_tags = tags[:2] if tags else []
    for tag in primary_tags:
        try:
            resp = EG.EAGLE_list_items(tags=[tag], limit=120, orderBy="MODIFIEDDATE")
        except Exception:
            continue
        _accumulate_from_response(resp)
        if len(candidate_map) >= limit * 2:
            break

    if not candidate_map and folder_ids:
        primary_folders = folder_ids[:2]
        for folder_id in primary_folders:
            try:
                resp = EG.EAGLE_list_items(folders=[folder_id], limit=120, orderBy="MODIFIEDDATE")
            except Exception:
                continue
            _accumulate_from_response(resp)
            if len(candidate_map) >= limit * 2:
                break

    if not candidate_map:
        return []

    candidate_list = list(candidate_map.values())
    sample_size = min(limit, len(candidate_list))
    if sample_size == 0:
        return []

    sampled_raw = random.sample(candidate_list, sample_size)
    formatted_candidates = _format_eagle_items(sampled_raw)
    formatted_map = {item["id"]: item for item in formatted_candidates if item.get("id")}

    similar_items = []
    for raw in sampled_raw:
        item_id = raw.get("id")
        formatted = formatted_map.get(item_id)
        if not formatted:
            continue
        media_type = formatted.get("media_type")
        detail_path = f"/EAGLE_video/{item_id}/" if media_type == "video" else f"/EAGLE_image/{item_id}/"
        similar_items.append({
            "id": item_id,
            "name": formatted.get("name") or "Untitled",
            "path": detail_path,
            "thumbnail_route": formatted.get("thumbnail_route") or DEFAULT_THUMBNAIL_ROUTE,
            "media_type": media_type
        })

    return similar_items


def get_eagle_video_details(item_id):
    """
    從 Eagle API 取得單一影片項目的詳細資訊並組合成播放器頁面需要的結構。
    """
    response = EG.EAGLE_get_item_info(item_id)
    if response.get("status") != "success":
        abort(500, description=f"Failed to fetch Eagle item info: {response.get('data')}")

    item = response.get("data")
    if not item or isinstance(item, list):
        abort(404, description="Video item not found.")

    raw_ext = item.get("ext") or ""
    ext = raw_ext.lower().lstrip(".")
    file_name = item.get("name") or item_id
    file_name_with_ext = item.get("fileName")

    if not ext and file_name_with_ext:
        _, inferred_ext = os.path.splitext(file_name_with_ext)
        ext = inferred_ext.lower().lstrip(".")

    if ext not in VIDEO_EXTENSIONS:
        abort(404, description="Requested Eagle item is not a video.")

    base_library_path = EG.EAGLE_get_current_library_path()
    item_dir = os.path.join(base_library_path, "images", f"{item_id}.info")

    candidate_files = []
    if file_name:
        candidate_files.append(f"{file_name}.{ext}")
    if file_name_with_ext:
        candidate_files.append(file_name_with_ext)
    candidate_files.append(f"{item_id}.{ext}")

    video_path = None
    for candidate in candidate_files:
        candidate_path = os.path.join(item_dir, candidate)
        if os.path.isfile(candidate_path):
            video_path = candidate_path
            break

    if video_path is None and os.path.isdir(item_dir):
        for entry in os.listdir(item_dir):
            if _is_video_file(entry):
                video_path = os.path.join(item_dir, entry)
                file_name, ext = os.path.splitext(entry)
                ext = ext.lstrip(".").lower()
                break

    if video_path is None:
        abort(404, description="Video file not found on disk.")

    normalized_abs_path = _normalize_slashes(os.path.abspath(video_path))
    relative_path = _normalize_slashes(os.path.relpath(video_path, base_library_path))
    file_size = os.path.getsize(video_path)
    modified_time = datetime.fromtimestamp(os.path.getmtime(video_path))

    stream_route = f"/serve_image/{normalized_abs_path}"

    thumbnail_route = DEFAULT_VIDEO_THUMBNAIL_ROUTE
    if os.path.isdir(item_dir):
        stem = os.path.splitext(os.path.basename(video_path))[0]
        for image_ext in IMAGE_EXTENSIONS:
            candidate_thumb = os.path.join(item_dir, f"{stem}_thumbnail.{image_ext}")
            if os.path.isfile(candidate_thumb):
                thumbnail_route = f"/serve_image/{_normalize_slashes(os.path.abspath(candidate_thumb))}"
                break

    tags = item.get("tags") or []
    tags = _normalize_item_tags(tags)

    original_url = item.get("website") or item.get("url")
    folder_ids = _extract_folder_ids(item.get("folders"))
    fallback_folder = item.get("folderId") or item.get("folder_id")
    if not folder_ids and fallback_folder:
        folder_ids = _extract_folder_ids([fallback_folder])
    folder_links = _build_eagle_folder_links(folder_ids)
    similar_items = _build_eagle_similar_items(item_id, tags, folder_ids)

    metadata = {
        "name": item.get("name") or os.path.basename(video_path),
        "category": "eagle-video",
        "tags": tags,
        "path": f"/EAGLE_video/{item_id}/",
        "thumbnail_route": thumbnail_route,
        "filesystem_path": normalized_abs_path,
        "description": item.get("annotation") or item.get("note"),
        "folders": folder_links,
        "similar": similar_items
    }

    video_data = {
        "name": metadata["name"],
        "relative_path": relative_path,
        "source_url": stream_route,
        "original_url": original_url,
        "thumbnail_route": thumbnail_route,
        "mime_type": mimetypes.guess_type(video_path)[0] or "video/mp4",
        "size_bytes": file_size,
        "size_display": _human_readable_size(file_size),
        "modified_time": modified_time.strftime("%Y-%m-%d %H:%M"),
        "parent_url": None,
        "download_url": stream_route,
        "folders": folder_links
    }

    return metadata, video_data

def get_eagle_image_details(item_id):
    """
    從 Eagle API 取得單一圖片項目的詳細資訊並組合成展示頁面需要的結構。
    """
    response = EG.EAGLE_get_item_info(item_id)
    if response.get("status") != "success":
        abort(500, description=f"Failed to fetch Eagle item info: {response.get('data')}")

    item = response.get("data")
    if not item or isinstance(item, list):
        abort(404, description="Image item not found.")

    raw_ext = item.get("ext") or ""
    ext = raw_ext.lower().lstrip(".")
    file_name = item.get("name") or item_id
    file_name_with_ext = item.get("fileName")

    base_library_path = EG.EAGLE_get_current_library_path()
    item_dir = os.path.join(base_library_path, "images", f"{item_id}.info")

    candidate_files = []
    if file_name_with_ext:
        candidate_files.append(file_name_with_ext)
    if file_name:
        candidate_files.append(f"{file_name}.{ext}" if ext else file_name)
    candidate_files.append(f"{item_id}.{ext}" if ext else item_id)

    image_path = None
    resolved_ext = ext
    for candidate in candidate_files:
        if not candidate:
            continue
        candidate_path = os.path.join(item_dir, candidate)
        if os.path.isfile(candidate_path):
            resolved_ext = os.path.splitext(candidate)[1].lstrip(".").lower()
            if resolved_ext in IMAGE_EXTENSIONS:
                image_path = candidate_path
                break

    if image_path is None and os.path.isdir(item_dir):
        for entry in os.listdir(item_dir):
            entry_ext = os.path.splitext(entry)[1].lstrip(".").lower()
            if entry_ext in IMAGE_EXTENSIONS:
                image_path = os.path.join(item_dir, entry)
                resolved_ext = entry_ext
                break

    if image_path is None:
        abort(404, description="Image file not found on disk.")

    normalized_abs_path = _normalize_slashes(os.path.abspath(image_path))
    relative_path = _normalize_slashes(os.path.relpath(image_path, base_library_path))
    file_size = os.path.getsize(image_path)
    modified_time = datetime.fromtimestamp(os.path.getmtime(image_path))

    stream_route = f"/serve_image/{normalized_abs_path}"

    tags = _normalize_item_tags(item.get("tags"))
    original_url = item.get("website") or item.get("url")
    folder_ids = _extract_folder_ids(item.get("folders"))
    fallback_folder = item.get("folderId") or item.get("folder_id")
    if not folder_ids and fallback_folder:
        folder_ids = _extract_folder_ids([fallback_folder])
    folder_links = _build_eagle_folder_links(folder_ids)
    similar_items = _build_eagle_similar_items(item_id, tags, folder_ids)

    metadata = {
        "name": item.get("name") or os.path.basename(image_path),
        "category": "eagle-image",
        "tags": tags,
        "path": f"/EAGLE_image/{item_id}/",
        "thumbnail_route": stream_route,
        "filesystem_path": normalized_abs_path,
        "description": item.get("annotation") or item.get("note"),
        "folders": folder_links,
        "similar": similar_items
    }

    image_data = {
        "name": metadata["name"],
        "relative_path": relative_path,
        "source_url": stream_route,
        "original_url": original_url,
        "thumbnail_route": stream_route,
        "mime_type": mimetypes.guess_type(image_path)[0] or f"image/{resolved_ext or 'jpeg'}",
        "size_bytes": file_size,
        "size_display": _human_readable_size(file_size),
        "modified_time": modified_time.strftime("%Y-%m-%d %H:%M"),
        "parent_url": None,
        "download_url": stream_route,
        "folders": folder_links
    }

    return metadata, image_data

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
        normalized_ext = (image_ext or "").lower()
        is_video = normalized_ext in VIDEO_EXTENSIONS
        if normalized_ext == "mp4":
            thumbnail_route = f"/serve_image/{base}/images/{image_id}.info/{image_name}_thumbnail.png"
        else:
            thumbnail_route = image_path

        data.append({
            "id": image_id,
            "name": image_name,
            "url": image_path,
            "thumbnail_route": thumbnail_route,
            "item_path": os.path.abspath(os.path.join(base, "images", f"{image_id}.info", f"{image_name}.{image_ext}")),
            "media_type": "video" if is_video else "image",
            "ext": normalized_ext
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
