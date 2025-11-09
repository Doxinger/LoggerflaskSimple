from flask import Flask, request
import datetime

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD'])
def log_ip():
    # Получаем IP-адрес клиента
    client_ip = request.remote_addr
    
    # Получаем текущее время
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Формируем запись для лога
    log_entry = f"{current_time} - IP: {client_ip} - Method: {request.method} - Path: {request.path}\n"
    
    # Записываем в файл
    with open('log.txt', 'a', encoding='utf-8') as f:
        f.write(log_entry)
    
    return f"Request from {client_ip} logged at {current_time}"

@app.route('/<path:path>')
def catch_all(path):
    # Обрабатываем все остальные пути
    return log_ip()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
