from flask import Flask, send_from_directory, request
from pathlib import Path
from threading import RLock
from datetime import datetime
import socket
import os

BASE_DIR = Path(__file__).resolve().parent
CSV_FILE = BASE_DIR / '1.csv'
COUNTER_FILE = BASE_DIR / 'counter.txt'
LOG_FILE = BASE_DIR / 'visit_log.txt'

app = Flask(__name__, static_folder='static', static_url_path='/static')
_lock = RLock()

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

@app.route('/')
def index():
    _atomic_update(COUNTER_FILE, lambda x: str(int(x or '0') + 1))
    _atomic_update(LOG_FILE, lambda x: x + f"{_today()} | {request.remote_addr} | {request.headers.get('User-Agent')}\n")
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
        count = COUNTER_FILE.read_text(encoding='utf-8').strip()
        return count or '0'
    except:
        return '0'

@app.route('/visit-count-today')
def get_today_count():
    try:
        today = _today()
        lines = LOG_FILE.read_text(encoding='utf-8').splitlines()
        today_count = sum(1 for line in lines if line.startswith(today))
        return str(today_count)
    except:
        return '0'

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


if __name__ == '__main__':
    # 获取端口，支持Vercel等平台
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
