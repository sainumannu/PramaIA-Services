import sqlite3, os, sys
from datetime import datetime, timedelta
DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs', 'log_database.db')
print('DB path:', DB)
if not os.path.exists(DB):
    print('DB_NOT_FOUND')
    sys.exit(0)
print('DB mtime:', datetime.fromtimestamp(os.path.getmtime(DB)).isoformat())
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
c = conn.cursor()
try:
    row = c.execute('SELECT COUNT(*) as cnt FROM logs').fetchone()
    print('total_logs:', row['cnt'])
except Exception as e:
    print('total_logs: ERROR', e)

try:
    row = c.execute('SELECT timestamp FROM logs ORDER BY timestamp DESC LIMIT 1').fetchone()
    print('latest_log_timestamp:', row['timestamp'] if row else None)
except Exception as e:
    print('latest_log_timestamp: ERROR', e)

# count logs in last 24 hours
try:
    since = (datetime.now() - timedelta(days=1)).isoformat()
    row = c.execute('SELECT COUNT(*) as cnt FROM logs WHERE timestamp >= ?', (since,)).fetchone()
    print('logs_last_24h:', row['cnt'])
except Exception as e:
    print('logs_last_24h: ERROR', e)

print('\nLast 10 logs:')
try:
    rows = c.execute('SELECT id,timestamp,project,level,message FROM logs ORDER BY timestamp DESC LIMIT 10').fetchall()
    for r in rows:
        print(r['timestamp'], r['project'], r['level'], r['message'][:120])
    if not rows:
        print('[no rows]')
except Exception as e:
    print('sample error', e)

conn.close()
