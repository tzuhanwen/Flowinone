import os
import random
import src.eagle_api as EG
from flask import abort

index_folder = 'static/temp_for_display'

def get_folders_info():
    """
    取得 index_folder 內的所有子資料夾資訊，符合 EAGLE API 格式
    """
    folders = [f for f in os.listdir(index_folder) if os.path.isdir(os.path.join(index_folder, f))]

    metadata = {
        "name": "All Collections",
        "category": "collections",
        "tags": ["collection", "group"],
        # "path": "/collections",
        "thumbnail_route": "/static/default_thumbnail.jpg"
    }

    data = []
    for folder in folders:
        folder_path = os.path.join(index_folder, folder)

        # 隨機選擇一張圖片作為縮圖
        image_files = [f for f in os.listdir(folder_path) if f.endswith(('jpg', 'jpeg', 'png', 'gif'))]
        thumbnail_path = random.choice(image_files) if image_files else "/static/default_thumbnail.jpg"

        temp = os.path.join(folder_path, thumbnail_path).replace('\\', '/')
        data.append({
            "name": folder,
            "url": f"/both/{folder}",
            "thumbnail_route": f"/{str(temp)}"
        })

    return metadata, data

def get_folder_images(folder_path):
    """
    取得指定資料夾內的所有圖片，符合 EAGLE API 格式
    """
    image_folder = os.path.join(index_folder, folder_path)
    if not os.path.isdir(image_folder):
        abort(404)

    metadata = {
        "name": folder_path,
        "category": "folder",
        "tags": ["grid", "slide"],
        "path": f"/both/{folder_path}",
        "thumbnail_route": "/static/default_thumbnail.jpg"
    }

    data = []
    image_files = [f for f in os.listdir(image_folder) if f.endswith(('png', 'jpg', 'jpeg', 'gif'))]
    image_files.sort()

    for image_file in image_files:
        image_path = os.path.join(image_folder, image_file).replace('\\', '/')
        data.append({
            "name": image_file,
            # "path": image_path,
            "thumbnail_route": f"/{image_path}",
            "url": f"/{image_path}"
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

        data.append({
            "name": image_name,
            # "path": image_path,
            "thumbnail_route": image_path,  # 假設縮圖與原圖相同
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