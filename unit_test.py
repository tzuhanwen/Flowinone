import os
from flask import Flask, render_template, send_from_directory, abort

app = Flask(__name__)

@app.route('/')
def index():
    ### 新版使用路徑
    IMAGE_FOLDER = 'static/img_test2'
    # 读取文件夹中的图片文件
    image_files = [f for f in os.listdir(IMAGE_FOLDER) if f.endswith(('png', 'jpg', 'jpeg', 'gif'))]
    image_files.sort()  # 你可以根据需要调整排序方式

    # 生成每个图片的完整路径
    image_paths = [os.path.join(IMAGE_FOLDER, f) for f in image_files]

    return render_template('view_slide.html', image_paths=image_paths)

# @app.route('/<path:folder_path>/')
# def singla_page_read(folder_path):
#     # ex: http://127.0.0.1:5893/img_test2/
#     # 注意在開發時會改變相對路徑的使用方法，在模板要多注意

#     # 将相对路径转为绝对路径
#     IMAGE_FOLDER = os.path.join('static', folder_path)
    
#     # 检查目录是否存在
#     if not os.path.isdir(IMAGE_FOLDER):
#         abort(404)
    
#     # 读取目录中的图片文件
#     image_files = [f for f in os.listdir(IMAGE_FOLDER) if f.endswith(('png', 'jpg', 'jpeg', 'gif'))]
#     image_files.sort()  # 你可以根据需要调整排序方式
    
#     image_paths = [os.path.join(IMAGE_FOLDER, f) for f in image_files]

#     # return render_template('view_slide.html', image_files=image_files, folder_path=folder_path)
#     return render_template('view_slide.html', image_paths=image_paths)







# @app.route('/image/<filename>')
# def image(filename):
#     IMAGE_FOLDER = 'static/img_test2'
#     return send_from_directory(IMAGE_FOLDER, filename)

# @app.route('/')
# def index():
#     # 原版多次request
#     IMAGE_FOLDER = 'static/img_test2'
#     # 讀取資料夾中的圖片文件
#     image_files = [f for f in os.listdir(IMAGE_FOLDER) if f.endswith(('png', 'jpg', 'jpeg', 'gif'))]
#     image_files.sort()  # 你可以根據需要調整排序方式
#     return render_template('view_slide.html', image_files=image_files)

# <h1>漫畫標題</h1>
# {% for image in image_files %}
#     原版需要API多次request
#     <img src="{{ url_for('image', filename=image) }}" alt="Comic Image">
# {% endfor %}

if __name__ == '__main__':
    app.run(debug=True, port=5893)