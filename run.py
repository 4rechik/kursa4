from waitress import serve
from app import app  # Импортируем экземпляр Flask приложения из app.py

if __name__ == '__main__':
    serve(app, host='127.0.0.1', port=8000)