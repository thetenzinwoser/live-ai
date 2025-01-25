from flask_socketio import SocketIO

socketio = SocketIO()

def notify_frontend_update():
    """Notify frontend that new content is available"""
    socketio.emit('content_update') 