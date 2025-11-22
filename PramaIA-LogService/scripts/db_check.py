import sqlite3, os, sys
DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs', 'log_database.db')
if not os.path.exists(DB):
    print('DB_NOT_FOUND', DB)
    sys.exit(0)
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
c = conn.cursor()
try:
    total = c.execute('SELECT COUNT(*) as cnt FROM logs').fetchone()['cnt']
    print('logs_count:', total)
except Exception as e:
    print('logs_count: ERROR', e)
try:
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='compressed_logs'")
    if c.fetchone():
        comp = c.execute('SELECT COUNT(*) as cnt FROM compressed_logs').fetchone()['cnt']
        print('compressed_logs_count:', comp)
    else:
        print('compressed_logs: MISSING')
except Exception as e:
    print('compressed_logs_count: ERROR', e)

print('\nSample logs (up to 10):')
try:
    rows = c.execute('SELECT id,timestamp,project,level,message FROM logs LIMIT 10').fetchall()
    for row in rows:
        print(row['id'], row['timestamp'], row['project'], row['level'], (row['message'][:80] if row['message'] else ''))
    if not rows:
        print('[no rows]')
except Exception as e:
    print('sample logs error', e)

print('\nSample compressed_logs (up to 10):')
try:
    rows = c.execute('SELECT log_id,archive_path,compressed_at FROM compressed_logs LIMIT 10').fetchall()
    for row in rows:
        print(row['log_id'], row['archive_path'], row['compressed_at'])
    if not rows:
        print('[no rows or table missing]')
except Exception as e:
    print('sample compressed_logs error or table missing', e)

conn.close()
