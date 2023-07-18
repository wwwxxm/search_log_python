from flask import Flask, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret!"
socketio = SocketIO(app)


@app.route("/")
def index():
    return "123456"


@socketio.on("connect")
def test_connect(auth):
    emit("my response", {"data": "Connected"})


@socketio.on("disconnect")
def test_disconnect():
    print("Client disconnected")


@socketio.on("message")
def handle_message(data):
    print("received message: " + data)


if __name__ == "__main__":
    socketio.run(app, debug=True)
