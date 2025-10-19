from flask import render_template, request, url_for, abort, jsonify
from file_handler import (
    get_eagle_folders,
    get_eagle_images_by_folderid,
    get_eagle_images_by_tag,
    get_eagle_tags,
    get_eagle_image_details,
    get_eagle_video_details,
    get_subfolders_info,
    get_eagle_stream_items,
)


def list_all_eagle_folder():
    """列出所有 Eagle 資料夾，並符合 EAGLE API 樣式"""
    metadata, data = get_eagle_folders()
    return render_template("view_both.html", metadata=metadata, data=data)


def view_eagle_folder(eagle_folder_id):
    """顯示指定 Eagle 資料夾 ID 下的所有圖片"""
    metadata, data = get_eagle_images_by_folderid(eagle_folder_id)

    # 加入子資料夾為類似圖片格式
    subfolders = get_subfolders_info(eagle_folder_id)
    data = subfolders + data

    current_url = request.full_path
    if current_url and current_url.endswith("?"):
        current_url = current_url[:-1]

    for item in data:
        if item.get("media_type") == "video" and item.get("id"):
            item["url"] = url_for(
                "view_eagle_video", item_id=item["id"], return_to=current_url
            )
        elif item.get("media_type") == "image" and item.get("id"):
            item["url"] = url_for(
                "view_eagle_image", item_id=item["id"], return_to=current_url
            )

    return render_template("view_both.html", metadata=metadata, data=data)


def list_eagle_tags():
    """列出 Eagle 中的所有標籤並提供連結"""
    metadata, tags = get_eagle_tags()
    return render_template("eagle_tags.html", metadata=metadata, tags=tags)


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
    if current_url and current_url.endswith("?"):
        current_url = current_url[:-1]

    for item in data:
        if item.get("media_type") == "video" and item.get("id"):
            item["url"] = url_for(
                "view_eagle_video", item_id=item["id"], return_to=current_url
            )
        elif item.get("media_type") == "image" and item.get("id"):
            item["url"] = url_for(
                "view_eagle_image", item_id=item["id"], return_to=current_url
            )

    return render_template("view_both.html", metadata=metadata, data=data)


def eagle_stream():
    """顯示無限滾動串流頁面"""
    return render_template("eagle_stream.html")


def view_eagle_video(item_id):
    """顯示 Eagle 影片的詳細資訊與播放器頁面"""
    metadata, video = get_eagle_video_details(item_id)
    return_to = request.args.get("return_to")
    if return_to:
        video["parent_url"] = return_to
    else:
        video["parent_url"] = request.referrer or url_for("index")
    return render_template("video_player.html", metadata=metadata, video=video)


def view_eagle_image(item_id):
    """顯示 Eagle 圖片的詳細資訊與展示頁面"""
    metadata, image = get_eagle_image_details(item_id)
    return_to = request.args.get("return_to")
    if return_to:
        image["parent_url"] = return_to
    else:
        image["parent_url"] = request.referrer or url_for("index")
    return render_template("image_viewer.html", metadata=metadata, image=image)


def eagle_stream_data():
    """提供 Eagle 串流頁面使用的資料"""
    try:
        offset = int(request.args.get("offset", 0))
        limit = int(request.args.get("limit", 30))
    except ValueError:
        abort(400, description="Invalid offset or limit")

    limit = max(1, min(limit, 60))
    offset = max(0, offset)

    data = get_eagle_stream_items(offset=offset, limit=limit)
    items = []
    for item in data:
        item_id = item.get("id")
        if not item_id:
            continue
        if item.get("media_type") == "video":
            detail_url = url_for("view_eagle_video", item_id=item_id)
        else:
            detail_url = url_for("view_eagle_image", item_id=item_id)

        items.append(
            {
                "id": item_id,
                "name": item.get("name"),
                "thumbnail_route": item.get("thumbnail_route"),
                "detail_url": detail_url,
                "media_type": item.get("media_type"),
                "ext": item.get("ext"),
            }
        )

    return jsonify({"items": items, "nextOffset": offset + len(items)})


routes = [
    ["/EAGLE_folders/", list_all_eagle_folder],
    ["/EAGLE_folder/<eagle_folder_id>/", view_eagle_folder],
    ["/EAGLE_tags/", list_eagle_tags],
    ["/EAGLE_tag/<target_tag>/", view_images_by_tag],
    ["/EAGLE_stream/", eagle_stream],
    ["/EAGLE_video/<item_id>/", view_eagle_video],
    ["/EAGLE_image/<item_id>/", view_eagle_image],
    ["/api/EAGLE_stream/", eagle_stream_data],
]
