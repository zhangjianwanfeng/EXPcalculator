from flask import Flask, send_from_directory, request
from pathlib import Path
from threading import RLock
from datetime import datetime
import socket
import os
import logging
from services.google_sheets import GoogleSheetsService

# 配置日志
logging.basicConfig(level=logging.INFO)

BASE_DIR = Path(__file__).resolve().parent
CSV_FILE = BASE_DIR / '1.csv'
COUNTER_FILE = BASE_DIR / 'counter.txt'
LOG_FILE = BASE_DIR / 'visit_log.txt'

app = Flask(__name__, static_folder='static', static_url_path='/static')
_lock = RLock()

# 初始化Google Sheets服务
sheets_service = GoogleSheetsService()

def _ensure(path: Path, default: str = ''):
    if not path.exists():
        path.write_text(default, encoding='utf-8')

_ensure(CSV_FILE, 'Lv,EXP\n98,10000\n99,15000\n100,20000\n')
_ensure(COUNTER_FILE, '0')
_ensure(LOG_FILE)

def _today():
    return datetime.now().strftime('%Y-%m-%d')

def _atomic_update(path: Path, update_fn):
    with _lock:
        text = path.read_text(encoding='utf-8')
        new_text = update_fn(text)
        path.write_text(new_text, encoding='utf-8')

def get_real_ip():
    """获取真实用户IP地址，处理代理服务器情况"""
    # 检查各种可能的IP头
    ip_headers = [
        'X-Forwarded-For',
        'X-Real-IP', 
        'X-Client-IP',
        'CF-Connecting-IP',  # Cloudflare
        'X-Forwarded',
        'Forwarded-For',
        'Forwarded'
    ]
    
    for header in ip_headers:
        ip = request.headers.get(header)
        if ip:
            # 如果是逗号分隔的多个IP，取第一个
            if ',' in ip:
                ip = ip.split(',')[0].strip()
            # 验证IP格式
            if ip and ip != 'unknown' and not ip.startswith('127.') and not ip.startswith('10.') and not ip.startswith('192.168.'):
                logging.info(f"从 {header} 获取到真实IP: {ip}")
                return ip
    
    # 如果没有找到，使用remote_addr
    ip = request.remote_addr
    logging.info(f"使用remote_addr作为IP: {ip}")
    return ip

@app.route('/')
def index():
    # 获取访问者信息
    ip_address = get_real_ip()
    user_agent = request.headers.get('User-Agent', '')
    
    # 记录到Google Sheets
    sheets_service.log_visit(ip_address, user_agent)
    
    # 更新本地计数器
    _atomic_update(COUNTER_FILE, lambda x: str(int(x or '0') + 1))
    _atomic_update(LOG_FILE, lambda x: x + f"{_today()} | {ip_address} | {user_agent}\n")
    
    return send_from_directory('.', 'index.html')

@app.route('/1.csv')
def get_csv_direct():
    return send_from_directory('.', '1.csv')

@app.route('/data')
def get_csv():
    return send_from_directory('.', '1.csv')

@app.route('/save-csv', methods=['POST'])
def save_csv():
    try:
        csv_data = request.get_data(as_text=True)
        CSV_FILE.write_text(csv_data, encoding='utf-8')
        return 'OK', 200
    except Exception as e:
        return str(e), 500

@app.route('/visit-count')
def get_visit_count():
    try:
        stats = sheets_service.get_visit_stats()
        return str(stats['total'])
    except:
        # 如果Google Sheets不可用，回退到本地文件
        count = COUNTER_FILE.read_text(encoding='utf-8').strip()
        return count or '0'

@app.route('/visit-count-today')
def get_today_count():
    try:
        stats = sheets_service.get_visit_stats()
        return str(stats['today'])
    except:
        # 回退到本地计算
        today = _today()
        lines = LOG_FILE.read_text(encoding='utf-8').splitlines()
        today_count = sum(1 for line in lines if line.startswith(today))
        return str(today_count)

@app.route('/logs')
def view_logs():
    if not LOG_FILE.exists():
        return "没有记录"
    lines = LOG_FILE.read_text(encoding='utf-8').splitlines()
    html = "<h2>访问记录</h2><table border='1' cellpadding='5'><tr><th>日期</th><th>IP</th><th>User-Agent</th></tr>"
    for line in lines:
        parts = line.split(" | ")
        if len(parts) == 3:
            date, ip, ua = parts
            html += f"<tr><td>{date}</td><td>{ip}</td><td>{ua}</td></tr>"
    html += "</table>"
    return html

@app.route('/debug-headers')
def debug_headers():
    """调试路由：查看所有请求头信息"""
    html = "<h2>请求头信息</h2><table border='1' cellpadding='5'><tr><th>Header</th><th>Value</th></tr>"
    
    # 显示所有请求头
    for header, value in request.headers.items():
        html += f"<tr><td>{header}</td><td>{value}</td></tr>"
    
    # 显示IP相关信息
    html += f"<tr><td>remote_addr</td><td>{request.remote_addr}</td></tr>"
    html += f"<tr><td>real_ip (calculated)</td><td>{get_real_ip()}</td></tr>"
    
    html += "</table>"
    return html

if __name__ == '__main__':
    # 获取端口，支持Vercel等平台
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
