"""
Creates a fresh codestreak.db with all tables.
Run this once if the app says 'no such table'.
"""
import sqlite3
import os

# Delete old db if it exists
if os.path.exists('codestreak.db'):
    os.remove('codestreak.db')
    print("Deleted old codestreak.db")

conn = sqlite3.connect('codestreak.db')
cur = conn.cursor()

# Create all 4 tables
cur.executescript("""
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    security_question TEXT,
    security_answer TEXT,
    streak INTEGER DEFAULT 0,
    streak_charge INTEGER DEFAULT 1,
    total_points INTEGER DEFAULT 0,
    weekly_points INTEGER DEFAULT 0,
    rank TEXT DEFAULT 'Bronze',
    premium INTEGER DEFAULT 0,
    achievements TEXT DEFAULT '[]',
    profile_picture TEXT,
    bio TEXT DEFAULT '',
    learning_goal TEXT DEFAULT 'Learning Python',
    avatar_emoji TEXT DEFAULT '🐉',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE lessons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    level TEXT NOT NULL,
    points INTEGER NOT NULL,
    difficulty TEXT NOT NULL,
    content TEXT,
    explanation TEXT,
    question TEXT,
    option_a TEXT,
    option_b TEXT,
    option_c TEXT,
    correct_option TEXT,
    next_lesson_id INTEGER,
    order_index INTEGER
);

CREATE TABLE progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    lesson_id INTEGER,
    status TEXT DEFAULT 'in_progress',
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    score INTEGER DEFAULT 0
);

CREATE TABLE payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    amount REAL NOT NULL,
    payment_status TEXT DEFAULT 'pending',
    transaction_id TEXT UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")

conn.commit()
print("✅ Tables created")

# Copy data from MySQL
import pymysql

mysql_conn = pymysql.connect(
    host='localhost',
    user='root',
    password='root',      # <-- CHANGE IF DIFFERENT
    db='codestreak',
    cursorclass=pymysql.cursors.DictCursor
)
mysql_cur = mysql_conn.cursor()

for table in ['users', 'lessons', 'progress', 'payments']:
    mysql_cur.execute(f"SELECT * FROM {table}")
    rows = mysql_cur.fetchall()
    
    if not rows:
        print(f"  (no rows in {table})")
        continue
    
    cols = list(rows[0].keys())
    placeholders = ','.join(['?'] * len(cols))
    col_names = ','.join(cols)
    
    count = 0
    for row in rows:
        values = [row[c] for c in cols]
        try:
            cur.execute(f"INSERT INTO {table} ({col_names}) VALUES ({placeholders})", values)
            count += 1
        except Exception as e:
            print(f"  Skipped: {e}")
    
    print(f"  Copied {count} rows to {table}")

conn.commit()
conn.close()
mysql_conn.close()

# Verify
conn = sqlite3.connect('codestreak.db')
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
print("\nTables in codestreak.db:", [r[0] for r in cur.fetchall()])
cur.execute("SELECT COUNT(*) FROM users")
print("Users in db:", cur.fetchone()[0])
conn.close()

print(f"\n✅ Fix complete! codestreak.db size: {os.path.getsize('codestreak.db')/1024:.1f} KB")
