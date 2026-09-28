import sqlite3

conn = sqlite3.connect('codestreak.db')
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cur.fetchall()]
conn.close()

print("Tables in database:")
for t in tables:
    print(f"  - {t}")
    