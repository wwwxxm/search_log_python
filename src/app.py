import time
from flask import Flask, request
# from flask_socketio import SocketIO
from search_log import run_search, get_results


name_space = '/test'  # 名称空间，写对才能通信


app = Flask(__name__)
# socketio = SocketIO(app)
# socketio.init_app(app, cors_allowed_origins='*')
# socketio.async_mode = 'eventlet'


@app.route('/')
def index():
    return {'time': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}


@app.route('/search', methods=['GET'])
def search():
    keywords = request.args.get('q')
    keywords = list(filter(None, keywords.split(' ')))
    run_search(keywords=keywords, logPath='logs/test.log')

    return {'keywords': keywords}


# # 建立连接
# @socketio.on('connect', namespace=name_space)
# def handle_connect():
#     print('@@@@@@@@@@@@@@handle_connect')
#     socketio.send('WebSocket Connected')

# # 断开连接


# @socketio.on('disconnect', namespace=name_space)
# def handle_disconnect():
#     print('@@@@@@@@@@@@@@handle_disconnect')
#     socketio.send('WebSocket Disconnected')

# # 收到消息


# @socketio.on('message', namespace=name_space)
# def handle_message():
#     print('@@@@@@@@@@@@@@handle_message')


@app.route('/get', methods=['GET'])
def get_result():
    return get_results()


if __name__ == '__main__':
    app.run(debug=True)
