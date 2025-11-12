from flask import Flask, request, jsonify
import time
import logging
from functools import wraps
from collections import defaultdict
import threading
import json
import uuid

app = Flask(__name__)

request_tracker = defaultdict(list)
banned_ips = {}
lock = threading.Lock()

request_limit_per_second = 10
ban_threshold_count = 50
ban_duration_seconds = 300

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('log.txt', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def get_client_ip():
    if request.environ.get('HTTP_X_REAL_IP'):
        return request.environ.get('HTTP_X_REAL_IP')
    if request.environ.get('HTTP_X_FORWARDED_FOR'):
        return request.environ.get('HTTP_X_FORWARDED_FOR').split(',')[0].strip()
    return request.environ.get('REMOTE_ADDR')

def cleanup_old_requests():
    current_time = time.time()
    with lock:
        for ip in list(request_tracker.keys()):
            request_tracker[ip] = [timestamp for timestamp in request_tracker[ip] 
                                 if current_time - timestamp < 60]
            if not request_tracker[ip]:
                del request_tracker[ip]

def is_ip_banned(ip):
    if ip in banned_ips:
        if time.time() - banned_ips[ip] < ban_duration_seconds:
            return True
        else:
            del banned_ips[ip]
    return False

def check_rate_limit(ip):
    current_time = time.time()
    
    with lock:
        request_tracker[ip] = [timestamp for timestamp in request_tracker[ip] 
                             if current_time - timestamp < 1]
        
        if len(request_tracker[ip]) >= request_limit_per_second:
            request_tracker[ip].append(current_time)
            if len(request_tracker[ip]) > ban_threshold_count:
                banned_ips[ip] = current_time
            return False
        
        request_tracker[ip].append(current_time)
        return True

def protect_from_ddos(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_ip = get_client_ip()
        
        if is_ip_banned(client_ip):
            return jsonify({"error": "Access temporarily blocked"}), 429
        
        if not check_rate_limit(client_ip):
            return jsonify({"error": "Rate limit exceeded"}), 429
        
        cleanup_old_requests()
        
        log_complete_request_data(client_ip)
        
        return f(*args, **kwargs)
    return decorated_function

def log_complete_request_data(ip):
    request_id = str(uuid.uuid4())
    current_time = time.time()
    
    request_details = {
        'request_id': request_id,
        'timestamp': current_time,
        'timestamp_human': time.strftime('%Y-%m-%d %H:%M:%S'),
        
        'client_info': {
            'ip_address': ip,
            'remote_addr': request.environ.get('REMOTE_ADDR'),
            'remote_port': request.environ.get('REMOTE_PORT'),
            'server_addr': request.environ.get('SERVER_NAME'),
            'server_port': request.environ.get('SERVER_PORT'),
        },
        
        'request_basic': {
            'method': request.method,
            'url': request.url,
            'path': request.path,
            'full_path': request.full_path,
            'script_root': request.script_root,
            'base_url': request.base_url,
            'url_root': request.url_root,
            'host': request.host,
            'host_url': request.host_url,
            'scheme': request.scheme,
        },
        
        'headers': dict(request.headers),
        
        'query_parameters': {
            'args': dict(request.args),
            'values': dict(request.values),
        },
        
        'data_content': {
            'form_data': dict(request.form),
            'json_data': request.get_json(silent=True) or {},
            'raw_data': request.get_data(as_text=True) if request.get_data() else None,
            'files': list(request.files.keys()) if request.files else [],
        },
        
        'cookies': dict(request.cookies),
        
        'environment': {
            'http_user_agent': request.environ.get('HTTP_USER_AGENT'),
            'http_accept': request.environ.get('HTTP_ACCEPT'),
            'http_accept_language': request.environ.get('HTTP_ACCEPT_LANGUAGE'),
            'http_accept_encoding': request.environ.get('HTTP_ACCEPT_ENCODING'),
            'http_connection': request.environ.get('HTTP_CONNECTION'),
            'http_host': request.environ.get('HTTP_HOST'),
            'http_referer': request.environ.get('HTTP_REFERER'),
            'http_x_forwarded_for': request.environ.get('HTTP_X_FORWARDED_FOR'),
            'http_x_forwarded_proto': request.environ.get('HTTP_X_FORWARDED_PROTO'),
            'http_x_forwarded_host': request.environ.get('HTTP_X_FORWARDED_HOST'),
            'http_x_real_ip': request.environ.get('HTTP_X_REAL_IP'),
            'http_origin': request.environ.get('HTTP_ORIGIN'),
        },
        
        'server_info': {
            'wsgi_version': request.environ.get('wsgi.version'),
            'python_version': request.environ.get('PYTHON_VERSION'),
            'server_software': request.environ.get('SERVER_SOFTWARE'),
            'request_method': request.environ.get('REQUEST_METHOD'),
            'script_name': request.environ.get('SCRIPT_NAME'),
            'content_type': request.environ.get('CONTENT_TYPE'),
            'content_length': request.environ.get('CONTENT_LENGTH'),
        },
        
        'performance': {
            'content_length': request.content_length,
            'content_type': request.content_type,
            'mimetype': request.mimetype,
            'mimetype_params': request.mimetype_params,
        },
        
        'endpoint': {
            'endpoint': request.endpoint,
            'blueprint': request.blueprint,
            'url_rule': str(request.url_rule) if request.url_rule else None,
        },
        
        'authentication': {
            'authorization': request.headers.get('Authorization'),
            'is_secure': request.is_secure,
            'is_json': request.is_json,
        },
        
        'rate_limit_info': {
            'current_requests': len(request_tracker.get(ip, [])),
            'is_banned': ip in banned_ips,
            'banned_until': banned_ips.get(ip)
        }
    }
    
    logger.info(f"COMPLETE_REQUEST_DATA: {json.dumps(request_details, indent=2, default=str)}")

@app.route('/')
@protect_from_ddos
def home():
    return jsonify({
        "message": "Welcome to the fully protected server",
        "your_ip": get_client_ip(),
        "status": "active",
        "timestamp": time.time()
    })

@app.route('/api/data', methods=['GET', 'POST'])
@protect_from_ddos
def api_data():
    if request.method == 'POST':
        return jsonify({
            "received_data": request.get_json(silent=True) or {},
            "method": "POST",
            "timestamp": time.time()
        })
    
    return jsonify({
        "data": "This is protected API data",
        "method": "GET",
        "timestamp": time.time()
    })

@app.route('/api/upload', methods=['POST'])
@protect_from_ddos
def upload_file():
    files_info = []
    for file_key in request.files:
        file = request.files[file_key]
        files_info.append({
            'filename': file.filename,
            'content_type': file.content_type,
            'content_length': len(file.read()),
            'name': file.name
        })
        file.seek(0)
    
    return jsonify({
        "uploaded_files": files_info,
        "form_data": dict(request.form),
        "timestamp": time.time()
    })

@app.route('/status')
@protect_from_ddos
def status():
    with lock:
        active_ips = len(request_tracker)
        banned_count = len(banned_ips)
        total_requests = sum(len(requests) for requests in request_tracker.values())
    
    return jsonify({
        "active_connections": active_ips,
        "banned_ips": banned_count,
        "total_requests_last_minute": total_requests,
        "server_time": time.strftime('%Y-%m-%d %H:%M:%S'),
        "uptime": time.time() - app_start_time
    })

app_start_time = time.time()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
