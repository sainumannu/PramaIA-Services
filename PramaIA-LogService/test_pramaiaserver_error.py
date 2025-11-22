#!/usr/bin/env python
import sqlite3

# Test specifico per PramaIAServer + Error
conn = sqlite3.connect('logs/log_database.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("=== TEST PramaIAServer + Error ===")

# Conta i log error per PramaIAServer
cursor.execute('SELECT COUNT(*) as count FROM logs WHERE project = ? AND level = ?', ('PramaIAServer', 'error'))
count = cursor.fetchone()[0]
print(f'Log error per PramaIAServer: {count}')

# Mostra alcuni esempi
cursor.execute('SELECT id, timestamp, level, message FROM logs WHERE project = ? AND level = ? LIMIT 5', ('PramaIAServer', 'error'))
results = cursor.fetchall()
print('Risultati:')
for r in results:
    print(f'  {r[1]} - {r[2]} - {r[3][:60]}...')

# Test anche con la query che usiamo nel codice (con esclusione lifecycle)
print("\nCon esclusione lifecycle:")
cursor.execute('SELECT COUNT(*) as count FROM logs WHERE project = ? AND level = ? AND level NOT IN (?, ?)', ('PramaIAServer', 'error', 'lifecycle', 'LIFECYCLE'))
count_filtered = cursor.fetchone()[0]
print(f'Log error per PramaIAServer (filtrato): {count_filtered}')

conn.close()