from flask import Flask
from routes import register_routes, register_routes_debug

app = Flask(__name__)

# 註冊所有路由
register_routes(app)
register_routes_debug(app)

if __name__ == "__main__":
    app.run(debug=True, port=5894)