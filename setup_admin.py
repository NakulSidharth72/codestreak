import sqlite3

# Connect to your database
conn = sqlite3.connect('codestreak.db')
cur = conn.cursor()

print("Starting database upgrade...")

# 1. Admin Audit Log Table
cur.execute('''
CREATE TABLE IF NOT EXISTS admin_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    admin_id INTEGER,
    action TEXT,
    target_user_id INTEGER,
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

# 2. System Settings Table
cur.execute('''
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
)
''')

# 3. Feedback / Report Queue
cur.execute('''
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    lesson_id INTEGER,
    issue_description TEXT,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

# 4. Add is_active to users
try:
    cur.execute("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT 1")
    print("Column 'is_active' added to users.")
except Exception as e:
    print("Column 'is_active' already exists.")

# 5. Add is_admin to users (THIS WAS MISSING!)
try:
    cur.execute("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0")
    print("Column 'is_admin' added to users.")
except Exception as e:
    print("Column 'is_admin' already exists.")

# 6. Make YOUR account the admin
# IMPORTANT: Change 'Nakul' to your exact username!
cur.execute("UPDATE users SET is_admin = 1 WHERE username = ?", ('Nakul',))
conn.commit()
print("Admin privileges granted to Nakul.")

cur.close()
conn.close()
print("Database upgrade complete!")
