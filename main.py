from flask import Flask, request
import datetime

app = Flask(__name__)

def get_client_ip():
    """Получает реальный IP через ngrok/локальный прокси"""
    # Основные заголовки которые используют ngrok и подобные сервисы
    if request.headers.get('X-Forwarded-For'):
        # Берем первый IP из списка (реальный клиентский IP)
        real_ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()
        return real_ip
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    else:
        # Локальный запрос (без прокси)
        return request.remote_addr

@app.route('/')
def home():
    client_ip = get_client_ip()
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Логируем
    log_entry = f"{current_time} - IP: {client_ip} - Method: {request.method} - Path: {request.path}\n"
    
    with open('log.txt', 'a', encoding='utf-8') as f:
        f.write(log_entry)
    
    # Простой ответ
    return f"""
    <h1>IP Logger</h1>
    <p><b>Your IP:</b> {client_ip}</p>
    <p><b>Time:</b> {current_time}</p>
    <p><b>URL:</b> {request.url}</p>
    <hr>
    <p>This IP has been logged to log.txt</p>
    """

@app.route('/<path:path>')
def catch_all(path):
    return home()

if __name__ == '__main__':
    print("Starting Flask server on http://localhost:5000")
    print("Use ngrok: ngrok http 5000")
    print("Then share the ngrok URL to collect IPs")
    app.run(host='0.0.0.0', port=5000, debug=False) 
