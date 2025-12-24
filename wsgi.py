import eventlet

eventlet.monkey_patch()

from app import create_app

app, socketio = create_app()
