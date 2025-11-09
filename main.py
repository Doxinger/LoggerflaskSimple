from flask import Flask, request
import datetime

app = Flask(__name__)

def get_client_ip():
    """Получает реальный IP-адрес клиента, учитывая прокси"""
    # Проверяем стандартные заголовки прокси
    if request.headers.get('X-Forwarded-For'):
        # Берем первый IP из списка (реальный клиент)
        client_ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        client_ip = request.headers.get('X-Real-IP')
    else:
        # Fallback на стандартный метод
        client_ip = request.remote_addr
    
    return client_ip

@app.route('/', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD'])
def log_ip():
    # Получаем реальный IP-адрес
    client_ip = get_client_ip()
    
    # Получаем текущее время
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Собираем дополнительную информацию
    headers_info = ""
    for header in ['X-Forwarded-For', 'X-Real-IP', 'X-Forwarded-Proto', 'Via']:
        if request.headers.get(header):
            headers_info += f" | {header}: {request.headers.get(header)}"
    
    # Формируем запись для лога
    log_entry = (f"{current_time} - Real IP: {client_ip} - Remote Addr: {request.remote_addr} "
                 f"- Method: {request.method} - Path: {request.path}{headers_info}\n")
    
    # Записываем в файл
    with open('log.txt', 'a', encoding='utf-8') as f:
        f.write(log_entry)
    
    # Выводим всю информацию для отладки
    debug_info = f"""
    <h3>IP Information:</h3>
    <b>Real IP:</b> {client_ip}<br>
    <b>Remote Addr:</b> {request.remote_addr}<br>
    <b>Method:</b> {request.method}<br>
    <b>Path:</b> {request.path}<br>
    <h3>Headers:</h3>
    """
    
    for header, value in request.headers:
        debug_info += f"<b>{header}:</b> {value}<br>"
    
    return f"Request from {client_ip} logged at {current_time}<br><br>" + debug_info

@app.route('/<path:path>')
def catch_all(path):
    # Обрабатываем все остальные пути
    return log_ip()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
