import os
# import re
import random
import pandas as pd
from flask import Flask, render_template, jsonify, send_from_directory, abort
import src.eagle_api as EG

#from .. import utility #import 上一個資料夾



app = Flask(__name__)
index_folder = 'static/Collection_main'
index_folder = 'static/temp_for_display'

# ---------------------------------------------------------------------------------------------------------------
def get_folder_name(df_folders_info, folder_id):
    """
    获取指定文件夹的 coverId。

    Args:
        df_folders_info (pd.DataFrame): 包含文件夹信息的 DataFrame。
        folder_id (str): 要查找的文件夹 ID。

    Returns:
        str: 对应文件夹的 coverId，如果未找到，返回 None。
    """
    # 筛选出 id 匹配的行
    folder_row = df_folders_info[df_folders_info["id"] == folder_id]
    # print()
    if not folder_row.empty:
        # 提取 coverId
        return folder_row.iloc[0]["name"]
    return None

def get_directory_structure(rootdir):
    ### for sidebar, 暫時不用
    """
    遍歷根目錄，生成包含資料夾和文件的結構。
    """
    dir_structure = {}
    for dirpath, dirnames, filenames in os.walk(rootdir):
        # 生成相對路徑
        rel_path = os.path.relpath(dirpath, rootdir)
        if rel_path == ".":
            rel_path = ""
        dir_structure[rel_path] = {
            "dirs": sorted(dirnames),
            "files": sorted(filenames)
        }
    return dir_structure

### Main API functions ----home_test_arg
# 加入title參數給模板
@app.route('/index_old')
def index_old():
    # 获取 index 目录下的所有子目录
    folders = [f for f in os.listdir(index_folder) if os.path.isdir(os.path.join(index_folder, f))]

    ### 尋找縮圖：弄成一個function, 需要上面的index_folder parameter
    folder_thumbnails = {}
    for folder in folders:
        folder_path = os.path.join(index_folder, folder)
        # 获取文件夹中的第一層所有图像文件
        image_files = [f for f in os.listdir(folder_path) if f.endswith(('.jpg', '.jpeg', '.png', '.gif'))]
        if image_files:
            # 随机选择一张图片作为缩略图
            thumbnail = random.choice(image_files)
            folder_thumbnails[folder] = os.path.join(folder_path, thumbnail).replace('\\', '/')


    title = 'Index page, set lists'
    # rootdir = 'static'
    # dir_structure = get_directory_structure(rootdir)    

    return render_template('index_old.html', title=title, folder_thumbnails=folder_thumbnails)  ### dir_structure=dir_structure
# ---------------------------------------------------------------------------------------------------------------


@app.route('/')
def index_new():
    ### 還沒好，input argument樣式不對

    """
    取得 index_folder 內的所有子資料夾，並符合 EAGLE API 格式
    """
    folders = [f for f in os.listdir(index_folder) if os.path.isdir(os.path.join(index_folder, f))]

    # 設定 metadata
    metadata = {
        "name": "All Collections",
        "category": "collection",
        "tags": ["collection", "group"],
        "path": "/collections",
        "thumbnail_route": "/static/default_thumbnail.jpg"  # 預設縮圖
    }

    # 準備資料夾清單
    data = []
    for folder in folders:
        folder_path = os.path.join(index_folder, folder)
        
        # 獲取第一層所有圖片作為縮圖
        image_files = [f for f in os.listdir(folder_path) if f.endswith(('.jpg', '.jpeg', '.png', '.gif'))]
        if image_files:
            thumbnail = random.choice(image_files)
            thumbnail_path = os.path.join(folder_path, thumbnail).replace('\\', '/')
        else:
            thumbnail_path = "/static/default_thumbnail.jpg"

        # 加入資料夾資訊
        data.append({
            "name": folder,
            "path": f"/both/{folder}",  # 指向該資料夾的 API 路徑
            "thumbnail_route": thumbnail_path
        })

    return render_template('index_new.html', metadata=metadata, data=data)






# 開發中 ---------------------------------------------------------------------------------------------------------------
@app.route('/images/<filename>')
def serve_image_old(filename):
    # http://127.0.0.1:5894/images/1732508730554.jpeg 成功指到桌面上的檔案
    path = '/Users/alvin/Desktop'
    # 1732508730554.jpeg
    return send_from_directory(path, filename)


@app.route('/serve_image/<path:image_path>')
def serve_image_by_full_path(image_path):
    """
    动态服务指定路径的图片。

    Args:
        image_path (str): 图片的完整文件路径。

    Returns:
        图片文件。
    """
    directory, filename = os.path.split(image_path)
    # print(directory)
    directory = '/' + directory
    return send_from_directory(directory, filename)


@app.route('/EAGLE_folder_old/')
def list_all_eagle_folder_old():
    """
    列出所有 Eagle 資料夾，並為每個資料夾生成縮圖。

    Returns:
        渲染的 HTML 頁面，顯示所有 Eagle 資料夾及其縮圖。
    """
    # 獲取所有資料夾的列表
    response = EG.EAGLE_get_library_info()
    if response.get("status") != "success":
        abort(500, description=f"Failed to fetch Eagle folders: {response.get('data')}")

    # 獲取資料夾信息
    folders = response.get("data", {}).get("folders", [])
    folder_thumbnails = {}

    # 遍歷每個資料夾，生成縮圖
    for folder in folders:
        folder_id = folder.get("id")
        folder_name = folder.get("name", "Unnamed Folder")
        
        # 使用 Eagle API 獲取該資料夾的圖片列表
        folder_response = EG.EAGLE_list_items(folders=[folder_id])
        if folder_response.get("status") != "success":
            continue  # 忽略有錯誤的資料夾
        
        image_items = folder_response.get("data", [])
        if image_items:
            # 隨機選擇一張圖片作為縮圖
            thumbnail_item = random.choice(image_items)
            image_id = thumbnail_item.get("id")
            image_name = thumbnail_item.get("name", "unknown")
            image_ext = thumbnail_item.get("ext", "jpg")
            thumbnail_path = f"/serve_image/{EG.EAGLE_get_current_library_path()}/images/{image_id}.info/{image_name}.{image_ext}"
        else:
            thumbnail_path = "/static/default_thumbnail.jpg"  # 預設縮圖

        folder_thumbnails[folder_name] = {
            "id": folder_id,
            "thumbnail": thumbnail_path
        }

    # 渲染模板
    title = "All Eagle Folders"
    return render_template("index_eagle_folder.html", title=title, folder_thumbnails=folder_thumbnails)



@app.route('/EAGLE_folder/')
def list_all_eagle_folder():
    """
    列出所有 Eagle 資料夾，並符合 EAGLE API 樣式。
    """
    # 獲取所有資料夾的列表
    response = EG.EAGLE_get_library_info()
    if response.get("status") != "success":
        abort(500, description=f"Failed to fetch Eagle folders: {response.get('data')}")

    # 設定 metadata
    metadata = {
        "name": "All Eagle Folders",
        "category": "collection",
        "tags": ["eagle", "folders"],
        "path": "/EAGLE_folder",
        "thumbnail_route": "/static/default_thumbnail.jpg"
    }

    # 獲取資料夾信息
    folders = response.get("data", {}).get("folders", [])
    data = []

    # 遍歷每個資料夾，生成縮圖
    for folder in folders:
        folder_id = folder.get("id")
        folder_name = folder.get("name", "Unnamed Folder")

        # 使用 Eagle API 獲取該資料夾的圖片列表
        folder_response = EG.EAGLE_list_items(folders=[folder_id])
        if folder_response.get("status") != "success":
            continue  # 忽略有錯誤的資料夾

        image_items = folder_response.get("data", [])
        if image_items:
            # 隨機選擇一張圖片作為縮圖
            thumbnail_item = random.choice(image_items)
            image_id = thumbnail_item.get("id")
            image_name = thumbnail_item.get("name", "unknown")
            image_ext = thumbnail_item.get("ext", "jpg")
            thumbnail_path = f"/serve_image/{EG.EAGLE_get_current_library_path()}/images/{image_id}.info/{image_name}.{image_ext}"
        else:
            thumbnail_path = "/static/default_thumbnail.jpg"

        data.append({
            "name": folder_name,
            "id": folder_id,
            "path": f"/EAGLE_folder/{folder_id}/",
            "thumbnail_route": thumbnail_path
        })

    # 渲染模板
    return render_template("index_eagle_folder_new.html", metadata=metadata, data=data)



##### 先弄一個display一個資料夾的～～～～～～～～～～～～

@app.route('/EAGLE_folder/<eagle_folder_id>/')
def view_eagle_folder(eagle_folder_id):
    # 先能從資料夾列出一個info list，然後view全部的圖片，有thumbnail的就用thumbnail，沒有就用原圖

    """
    顯示指定 Eagle 資料夾 ID 下的所有圖片。

    Args:
        eagle_folder_id (str): Eagle 資料夾的 ID。

    Returns:
        渲染的 HTML 頁面，顯示該資料夾下的所有圖片。
    """
    # 获取当前 Eagle 库的路径
    library_path = EG.EAGLE_get_current_library_path()
    if "Error" in library_path:
        abort(500, description=f"Failed to get library path: {library_path}")

    # 从 Eagle API 获取该文件夹的图片列表
    response = EG.EAGLE_list_items(folders=[eagle_folder_id], 
                                   orderBy="CREATEDATE")
    if response.get('status') == 'error':
        abort(500, description=f"Error fetching images from Eagle folder: {response.get('data')}")

    # 提取图片信息并生成完整路径
    image_items = response.get('data', [])   ###dict    

    image_paths = []
    for item in image_items:
        image_id = item.get('id')
        image_name = item.get('name', 'unknown')
        image_ext = item.get('ext', 'jpg')  # 默认为 jpg
        image_path = os.path.join(library_path, "images", f"{image_id}.info", f"{image_name}.{image_ext}")
        image_paths.append(image_path)
    # print('--------')
    # print(image_paths)   #這邊為止第一個字串都是/的
    # print('--------')
    image_paths.sort()
    # image_paths = image_paths[::-1]
    print(image_paths)

    # 渲染模板，将图片路径传递给前端页面
    
    title = f"Eagle Folder: {eagle_folder_id}"
    title = get_folder_name(df_folders_info, eagle_folder_id)
    return render_template('view_both_eagle.html', title=title, image_paths=image_paths)


@app.route('/EAGLE_tag/<target_tag>/')
def view_images_by_tag(target_tag):
    """
    显示所有带有指定标签的图片。

    Args:
        target_tag (str): 要查询的标签。

    Returns:
        渲染的 HTML 页面，显示所有具有该标签的图片。
    """
    # 获取当前 Eagle 库的路径
    library_path = EG.EAGLE_get_current_library_path()
    if "Error" in library_path:
        abort(500, description=f"Failed to get library path: {library_path}")

    # 从 Eagle API 获取所有带有指定标签的图片
    response = EG.EAGLE_list_items(tags=[target_tag], orderBy="CREATEDATE")
    if response.get('status') == 'error':
        abort(500, description=f"Error fetching images with tag '{target_tag}': {response.get('data')}")

    # 提取图片信息并生成完整路径
    image_items = response.get('data', [])
    image_paths = []
    for item in image_items:
        image_id = item.get('id')
        image_name = item.get('name', 'unknown')
        image_ext = item.get('ext', 'jpg')  # 默认为 jpg
        image_path = os.path.join(library_path, "images", f"{image_id}.info", f"{image_name}.{image_ext}")
        image_paths.append(image_path)

    # 排序图片路径（可选）
    image_paths.sort()

    # 渲染模板，将图片路径传递给前端页面
    title = f"Images with Tag: {target_tag}"
    return render_template('view_both_eagle.html', title=title, image_paths=image_paths)


# 有錯
# @app.route('/EAGLE_folder/<eagle_folder_id>/')
# def view_eagle_folder_new(eagle_folder_id):    
#     """
#     取得 Eagle 指定資料夾內的所有圖片，以符合 EAGLE API 格式
#     """
#     # 調用 Eagle API 獲取該資料夾的圖片列表
#     response = EG.EAGLE_list_items(folders=[folder_path])
#     if response.get("status") != "success":
#         abort(500, description=f"Failed to fetch Eagle images: {response.get('data')}")

#     # 設定 metadata
#     metadata = {
#         "name": folder_path,
#         "category": "folder",
#         "tags": ["grid", "slide", "eagle"],
#         "path": f"/both_eagle/{folder_path}",
#         "thumbnail_route": "/static/default_thumbnail.jpg"  # 預設縮圖
#     }

#     # 取得所有圖片
#     data = []
#     image_items = response.get("data", [])
#     image_items.sort(key=lambda x: x.get("name", ""))  # 按名稱排序

#     for image in image_items:
#         image_id = image.get("id")
#         image_name = image.get("name", "unknown")
#         image_ext = image.get("ext", "jpg")
#         image_path = f"/serve_image/{EG.EAGLE_get_current_library_path()}/images/{image_id}.info/{image_name}.{image_ext}"

#         data.append({
#             "name": image_name,
#             "path": image_path,
#             "thumbnail_route": image_path,  # 假設縮圖與原圖相同
#             "url": image_path
#         })

#     return render_template('view_both_eagle_new.html', metadata=metadata, data=data)

# EAGLE_get_current_library_path()
# /Users/AA/Eagle DB/捕捉美好.library
# /Users/AA/Eagle DB/捕捉美好.library/images/KBRIGT1H7LV6V.info/圖片名稱.圖片ext


# Examples ---------------------------------------------------------------------------------------------------------------
@app.route('/test_arg')
def test_arg():
    df_to_post = [
        {'author': 'Lynn','title': 'Blog Post 1','content': 'First post content','date_posted': 'September 3, 2018'},
        {'author': 'Lydia','title': 'Blog Post 2','content': 'Second post content','date_posted': 'September 6, 2018'}
        ]
    return render_template('test_arg.html', title='All in One', df_to_post=df_to_post)

@app.route('/both_old')
def view_both_default_old():
    IMAGE_FOLDER = os.path.join(index_folder, 'for_opencv')
    image_paths = [os.path.join(IMAGE_FOLDER, f) for f in os.listdir(IMAGE_FOLDER) if f.endswith(('.jpg', '.jpeg', '.png', '.gif'))]
    image_paths.sort()
    title = "Image Viewer"
    print(image_paths)
    return render_template('view_both.html', title=title, image_paths=image_paths)

@app.route('/both')
def view_both_default():
    """
    取得 `index_folder/for_opencv` 內的所有圖片，並符合 EAGLE API 格式
    """
    IMAGE_FOLDER = os.path.join(index_folder, 'for_opencv')
    if not os.path.isdir(IMAGE_FOLDER):
        abort(404)

    # 設定 metadata
    metadata = {
        "name": "for_opencv",
        "category": "folder",
        "tags": ["grid", "slide", "view_both"],
        "path": "/both_old",
        "thumbnail_route": "/static/default_thumbnail.jpg"  # 預設縮圖
    }

    # 獲取所有圖片
    data = []
    image_files = [f for f in os.listdir(IMAGE_FOLDER) if f.endswith(('png', 'jpg', 'jpeg', 'gif'))]
    image_files.sort()

    for image_file in image_files:
        image_path = os.path.join(IMAGE_FOLDER, image_file).replace('\\', '/')
        data.append({
            "name": image_file,
            "path": image_path,
            "thumbnail_route": image_path,  # 假設縮圖與原圖相同
            "url": f"/{image_path}"
        })

    return render_template('view_both_new.html', metadata=metadata, data=data)

@app.route('/grid_old')
def view_grid_default_old():
    IMAGE_FOLDER = os.path.join(index_folder, 'for_opencv')
    # IMAGE_FOLDER = os.path.join(index_folder, folder_path)

    # 获取文件夹中的所有图像文件
    image_files = [f for f in os.listdir(IMAGE_FOLDER) if f.endswith(('png', 'jpg', 'jpeg', 'gif'))]
    image_files.sort()
    image_paths = [os.path.join(IMAGE_FOLDER, f) for f in image_files]
    # print(image_paths)
    return render_template('view_grid.html', title='Grid Image Gallery', image_paths=image_paths)


@app.route('/grid')
def view_grid_default():
    """
    取得 `index_folder/for_opencv` 內的所有圖片，並符合 EAGLE API 格式
    """
    IMAGE_FOLDER = os.path.join(index_folder, 'for_opencv')
    if not os.path.isdir(IMAGE_FOLDER):
        abort(404)

    # 設定 metadata
    metadata = {
        "name": "for_opencv",
        "category": "folder",
        "tags": ["grid", "image"],
        "path": "/grid",
        "thumbnail_route": "/static/default_thumbnail.jpg"  # 預設縮圖
    }

    # 獲取所有圖片
    data = []
    image_files = [f for f in os.listdir(IMAGE_FOLDER) if f.endswith(('png', 'jpg', 'jpeg', 'gif'))]
    image_files.sort()

    for image_file in image_files:
        image_path = os.path.join(IMAGE_FOLDER, image_file).replace('\\', '/')
        data.append({
            "name": image_file,
            "path": image_path,
            "thumbnail_route": image_path,  # 這裡假設縮圖和原圖一致，若有縮圖目錄可以修改
            "url": f"/{image_path}"
        })

    return render_template('view_grid_new.html', metadata=metadata, data=data)


# ---------------------------------------------------------------------------------------------------------------
@app.route('/grid_old/<path:folder_path>/')
def view_grid(folder_path):
    # ex: http://127.0.0.1:5894/grid/img_test2/
    # 注意在開發時會改變相對路徑的使用方法，在模板要多注意
    IMAGE_FOLDER = os.path.join(index_folder, folder_path)
    if not os.path.isdir(IMAGE_FOLDER): abort(404)

    # 获取文件夹中的所有图像文件
    image_files = [f for f in os.listdir(IMAGE_FOLDER) if f.endswith(('png', 'jpg', 'jpeg', 'gif'))]
    image_files.sort()
    image_paths = [os.path.join(IMAGE_FOLDER, f) for f in image_files]

    return render_template('view_grid.html', title='Grid Image Gallery', image_paths=image_paths)

@app.route('/grid/<path:folder_path>/')
def view_grid_new(folder_path):
    """
    取得指定資料夾內的所有圖片，並符合 EAGLE API 格式
    """
    IMAGE_FOLDER = os.path.join(index_folder, folder_path)
    if not os.path.isdir(IMAGE_FOLDER): 
        abort(404)

    # 設定 metadata
    metadata = {
        "name": folder_path,
        "category": "folder",
        "tags": ["grid", "image"],
        "path": f"/grid/{folder_path}",
        "thumbnail_route": "/static/default_thumbnail.jpg"  # 預設縮圖
    }

    # 獲取所有圖片
    data = []
    image_files = [f for f in os.listdir(IMAGE_FOLDER) if f.endswith(('png', 'jpg', 'jpeg', 'gif'))]
    image_files.sort()

    for image_file in image_files:
        image_path = os.path.join(IMAGE_FOLDER, image_file).replace('\\', '/')
        data.append({
            "name": image_file,
            "path": image_path,
            "thumbnail_route": image_path,  # 這裡假設縮圖和原圖一致，若有縮圖目錄可以修改
            "url": f"/{image_path}"
        })

    return render_template('view_grid_new.html', metadata=metadata, data=data)

@app.route('/slide_old/<path:folder_path>/')
def view_slide(folder_path):
    # ex: http://127.0.0.1:5894/slide/img_test2/
    
    IMAGE_FOLDER = os.path.join(index_folder, folder_path)   # 将相对路径转为绝对路径
    if not os.path.isdir(IMAGE_FOLDER): abort(404)
    
    # 读取目录中的图片文件
    image_files = [f for f in os.listdir(IMAGE_FOLDER) if f.endswith(('png', 'jpg', 'jpeg', 'gif'))]
    image_files.sort()
    image_paths = [os.path.join(IMAGE_FOLDER, f) for f in image_files]

    # return render_template('view_slide.html', image_files=image_files, folder_path=folder_path)
    return render_template('view_slide.html', title=folder_path, image_paths=image_paths)

@app.route('/slide/<path:folder_path>/')
def view_slide_new(folder_path):
    """
    取得指定資料夾內的所有圖片，以符合 EAGLE API 格式
    """
    IMAGE_FOLDER = os.path.join(index_folder, folder_path)
    if not os.path.isdir(IMAGE_FOLDER):
        abort(404)

    # 設定 metadata
    metadata = {
        "name": folder_path,
        "category": "folder",
        "tags": ["slide", "comic"],
        "path": f"/slide/{folder_path}",
        "thumbnail_route": "/static/default_thumbnail.jpg"  # 預設縮圖
    }

    # 獲取所有圖片
    data = []
    image_files = [f for f in os.listdir(IMAGE_FOLDER) if f.endswith(('png', 'jpg', 'jpeg', 'gif'))]
    image_files.sort()

    for image_file in image_files:
        image_path = os.path.join(IMAGE_FOLDER, image_file).replace('\\', '/')
        data.append({
            "name": image_file,
            "path": image_path,
            "thumbnail_route": image_path,  # 假設縮圖與原圖相同
            "url": f"/{image_path}"
        })

    return render_template('view_slide_new.html', metadata=metadata, data=data)

@app.route('/both_old/<path:folder_path>/')
def view_both_old(folder_path):
    IMAGE_FOLDER = os.path.join(index_folder, folder_path)
    if not os.path.isdir(IMAGE_FOLDER): abort(404)

    image_paths = [os.path.join(IMAGE_FOLDER, f) for f in os.listdir(IMAGE_FOLDER) if f.endswith(('.jpg', '.jpeg', '.png', '.gif'))]
    image_paths.sort()
    
    # title = "Image Viewer"
    title = folder_path
    return render_template('view_both.html', title=title, image_paths=image_paths)

@app.route('/both/<path:folder_path>/')
def view_both(folder_path):
    """
    取得指定資料夾內的所有圖片，以符合 EAGLE API 格式
    """
    IMAGE_FOLDER = os.path.join(index_folder, folder_path)
    if not os.path.isdir(IMAGE_FOLDER):
        abort(404)

    # 設定 metadata
    metadata = {
        "name": folder_path,
        "category": "folder",
        "tags": ["grid", "slide", "view_both"],
        "path": f"/both/{folder_path}",
        "thumbnail_route": "/static/default_thumbnail.jpg"  # 預設縮圖
    }

    # 獲取所有圖片
    data = []
    image_files = [f for f in os.listdir(IMAGE_FOLDER) if f.endswith(('png', 'jpg', 'jpeg', 'gif'))]
    image_files.sort()

    for image_file in image_files:
        image_path = os.path.join(IMAGE_FOLDER, image_file).replace('\\', '/')
        data.append({
            "name": image_file,
            "path": image_path,
            "thumbnail_route": image_path,  # 假設縮圖與原圖相同
            "url": f"/{image_path}"
        })

    return render_template('view_both_new.html', metadata=metadata, data=data)


# @app.route('/debug/')
# def debug_print():
#     df_folders_info = EG.EAGLE_get_folders_df()
#     print(df_folders_info.shape)
#     print(df_folders_info.columns)
#     df_to_post = [
#         {'author': 'Lynn','title': 'Blog Post 1','content': 'First post content','date_posted': 'September 3, 2018'},
#         {'author': 'Lydia','title': 'Blog Post 2','content': 'Second post content','date_posted': 'September 6, 2018'}
#         ]
#     return render_template('test_arg.html', title='All in One', df_to_post=df_to_post)

if __name__ == "__main__":
    app.run(debug=True, port=5894)











### APIs ------------------------------------------------------

# @app.route('/query_a_folder/<target_index>')
# @cross_origin()
# def query_a_folder(target_index):
    
#     if target_index == '-1':    # home
#         target_name = ''
#         target_list = ['1', '2', '3']
#     else:
#         target = df_id.loc[target_index]
#         target_name = target['name']
#         target_list = target['children_id']
   
#     result = df_id.loc[target_list].reset_index().to_dict('records')
#     return jsonify({'name': target_name, 'children': result})



# @app.route('/get_parents_and_self/<target_index>')
# @cross_origin()
# def get_parents_and_self(target_index):
#     target_list = df_id.loc[target_index]['parents']
#     result = df_id.loc[target_list].reset_index().to_dict('records')
#     return jsonify(result)

# @app.route('/info/<target_index>')
# @cross_origin()
# def info(target_index):
#     result = df_id.loc[target_index].to_dict()
#     return  jsonify(result)