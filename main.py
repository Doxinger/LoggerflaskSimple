from flask import Flask, request
import datetime

app = Flask(__name__)

def get_client_ip():
    """Получает реальный IP-адрес клиента, учитывая прокси"""
    if request.headers.get('X-Forwarded-For'):
        # Берем первый IP из списка и убираем порт если есть
        ip_with_port = request.headers.get('X-Forwarded-For').split(',')[0].strip()
        client_ip = ip_with_port.split(':')[0]
    elif request.headers.get('X-Real-IP'):
        ip_with_port = request.headers.get('X-Real-IP')
        client_ip = ip_with_port.split(':')[0]
    else:
        client_ip = request.remote_addr.split(':')[0]
    
    return client_ip

@app.route('/', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD'])
def log_ip():
    # Получаем реальный IP-адрес
    client_ip = get_client_ip()
    
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
    return log_ip()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 
