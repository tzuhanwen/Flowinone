import os
import random
import src.eagle_api as EG
from flask import abort
from config import DB_route_internal, DB_route_external

def get_all_folders_info(src):
    """
    取得 DB_route 內的所有子資料夾資訊，符合 EAGLE API 格式
    src: internal or external
    """

    if src == "external":
        base_dir = DB_route_external
    else:
        base_dir = DB_route_internal
    folders = [f for f in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, f))]

    metadata = {
        "name": "All Collections",
        "category": "collections",
        "tags": ["collection", "group", "Main"],
        # "path": "/collections",
        "thumbnail_route": "/static/default_thumbnail.jpg"
    }

    data = []
    for folder in folders:
        folder_path = os.path.join(base_dir, folder)

        # 隨機選擇一張圖片作為縮圖
        image_files = [f for f in os.listdir(folder_path) if f.endswith(('jpg', 'jpeg', 'png', 'gif'))]
        thumbnail_path = random.choice(image_files) if image_files else "/static/default_thumbnail.jpg"

        image_path = os.path.join(folder_path, thumbnail_path).replace('\\', '/')
        if src == "external":
            temp1 = f"/serve_image/{image_path}"
            temp = f"/both/{folder}"
        else:
            temp1 = f"/{str(image_path)}"
            temp = f"/both/{folder}/?src=internal"
        data.append({
            "name": folder,
            "thumbnail_route": temp1,
            "url": temp,
        })

    return metadata, data

def get_folder_images(folder_path, src=None):
    """
    取得指定資料夾內的所有圖片，符合 EAGLE API 格式
    從任意資料夾（base_dir + folder_path）中取得圖片
    """

    if src == 'external':
        base_dir = DB_route_external
    else:
        base_dir = DB_route_internal  # default to static/temp_for_display

    ### image_folder
    abs_folder_path = os.path.join(base_dir, folder_path)
    if not os.path.isdir(abs_folder_path):
        abort(404)
    
    metadata = {
        "name": os.path.basename(folder_path),  #folder_path
        "category": "folder",
        "tags": ["grid", "slide", "test_tag_default"],
        "path": f"/both/{folder_path}",
        "thumbnail_route": "/static/default_thumbnail.jpg"
    }

    data = []
    image_files = [f for f in os.listdir(abs_folder_path) if f.endswith(('png', 'jpg', 'jpeg', 'gif'))]
    image_files.sort()

    for img in image_files:
        image_path = os.path.join(abs_folder_path, img).replace('\\', '/')
        if src == "external":
            temp = f"/serve_image/{image_path}"
            temp1 = f"/serve_image/{image_path}"
        else:
            temp = f"/{image_path}"
            temp1 = f"/{image_path}"

        data.append({
            "name": img,
            # "path": image_path,
            "thumbnail_route": temp1,
            "url": temp
        })

    return metadata, data

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
        "thumbnail_route": "/static/default_thumbnail.jpg"
    }

    data = []
    for folder in response.get("data", {}).get("folders", []):
        folder_id = folder.get("id")
        folder_name = folder.get("name", "Unnamed Folder")

        # 取得 Eagle 資料夾內的縮圖
        folder_response = EG.EAGLE_list_items(folders=[folder_id])
        image_items = folder_response.get("data", [])
        image_items.sort(key=lambda x: x.get("name", ""))
        thumbnail_path = f"/serve_image/{EG.EAGLE_get_current_library_path()}/images/{image_items[0]['id']}.info/{image_items[0]['name']}.{image_items[0]['ext']}" if image_items else "/static/default_thumbnail.jpg"

        data.append({
            "name": folder_name,
            "id": folder_id,
            "url": f"/EAGLE_folder/{folder_id}/",
            "thumbnail_route": thumbnail_path
        })

    return metadata, data

def get_eagle_images_by_folderid(eagle_folder_id):
    """
    獲取 Eagle API 提供的指定資料夾內的圖片資訊，符合 EAGLE API 格式
    """
    response = EG.EAGLE_list_items(folders=[eagle_folder_id])
    if response.get("status") != "success":
        abort(500, description=f"Failed to fetch images from Eagle folder: {response.get('data')}")

    metadata = {
        "name": eagle_folder_id,
        "category": "folder",
        "tags": ["eagle", "images"],
        "path": f"/EAGLE_folder/{eagle_folder_id}",
        "thumbnail_route": "/static/default_thumbnail.jpg"
    }

    data = []
    image_items = response.get("data", [])
    image_items.sort(key=lambda x: x.get("name", ""))  # 按名稱排序

    for image in image_items:
        image_id = image.get("id")
        image_name = image.get("name", "unknown")
        image_ext = image.get("ext", "jpg")
        image_path = f"/serve_image/{EG.EAGLE_get_current_library_path()}/images/{image_id}.info/{image_name}.{image_ext}"

        thumbnail_route = image_path  # 假設縮圖與原圖相同
        if image_ext == "mp4":
            thumbnail_route = f"/serve_image/{EG.EAGLE_get_current_library_path()}/images/{image_id}.info/{image_name}_thumbnail.png"
        data.append({
            "name": image_name,
            # "path": image_path,
            "thumbnail_route": thumbnail_route,
            "url": image_path
        })

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
        "thumbnail_route": "/static/default_thumbnail.jpg"
    }

    # 取得所有圖片
    data = []
    image_items = response.get("data", [])
    image_items.sort(key=lambda x: x.get("name", ""))  # 按名稱排序

    for image in image_items:
        image_id = image.get("id")
        image_name = image.get("name", "unknown")
        image_ext = image.get("ext", "jpg")
        image_path = f"/serve_image/{EG.EAGLE_get_current_library_path()}/images/{image_id}.info/{image_name}.{image_ext}"

        data.append({
            "name": image_name,
            # "path": image_path,
            "thumbnail_route": image_path,  # 假設縮圖與原圖相同
            "url": image_path
        })

    return metadata, data