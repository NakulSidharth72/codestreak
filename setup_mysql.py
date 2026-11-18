import mysql.connector

# YOUR CLEVER CLOUD CREDENTIALS
DB_HOST = "b7ftkwpts6cy6kinbhuh-mysql.services.clever-cloud.com"
DB_USER = "u2g68lxr9lc8dmsp"
DB_PASSWORD = "53xY05DlDk80j1kFsdYQ"
DB_NAME = "b7ftkwpts6cy6kinbhuh"

print("Connecting to Clever Cloud MySQL...")

try:
    conn = mysql.connector.connect(
        host=DB_HOST, 
        user=DB_USER, 
        password=DB_PASSWORD, 
        database=DB_NAME
    )
    cur = conn.cursor()

    # Dropping tables just in case the previous run partially created them
    cur.execute("DROP TABLE IF EXISTS admin_logs, messages, activity, follows, payments, progress, lessons, users")

    # List of all tables to create based on your app.py
    tables = [
        """CREATE TABLE users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(255) UNIQUE NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            security_question VARCHAR(255),
            security_answer VARCHAR(255),
            streak INT DEFAULT 0,
            streak_charge INT DEFAULT 1,
            total_points INT DEFAULT 0,
            weekly_points INT DEFAULT 0,
            `rank` VARCHAR(50) DEFAULT 'Bronze',
            premium INT DEFAULT 0,
            achievements TEXT,
            profile_picture VARCHAR(255),
            bio TEXT,
            learning_goal VARCHAR(255) DEFAULT 'Learning Python',
            avatar_emoji VARCHAR(50) DEFAULT '🐉',
            is_active BOOLEAN DEFAULT 1,
            is_admin BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) DEFAULT CHARSET=utf8mb4""",
        """CREATE TABLE lessons (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            level VARCHAR(50) NOT NULL,
            points INT NOT NULL,
            difficulty VARCHAR(50) NOT NULL,
            content TEXT,
            explanation TEXT,
            question TEXT,
            option_a TEXT,
            option_b TEXT,
            option_c TEXT,
            correct_option VARCHAR(10),
            next_lesson_id INT,
            order_index INT
        ) DEFAULT CHARSET=utf8mb4""",
        """CREATE TABLE progress (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            lesson_id INT,
            status VARCHAR(50) DEFAULT 'in_progress',
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            score INT DEFAULT 0
        ) DEFAULT CHARSET=utf8mb4""",
        """CREATE TABLE payments (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            amount REAL NOT NULL,
            payment_status VARCHAR(50) DEFAULT 'pending',
            transaction_id VARCHAR(255) UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) DEFAULT CHARSET=utf8mb4""",
        """CREATE TABLE follows (
            id INT AUTO_INCREMENT PRIMARY KEY,
            follower_id INT NOT NULL,
            following_id INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(follower_id, following_id)
        ) DEFAULT CHARSET=utf8mb4""",
        """CREATE TABLE activity (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            action VARCHAR(255) NOT NULL,
            description TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) DEFAULT CHARSET=utf8mb4""",
        """CREATE TABLE messages (
            id INT AUTO_INCREMENT PRIMARY KEY,
            sender_id INT NOT NULL,
            receiver_id INT NOT NULL,
            content TEXT NOT NULL,
            is_read INT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) DEFAULT CHARSET=utf8mb4""",
        """CREATE TABLE admin_logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            admin_id INT,
            action VARCHAR(255),
            target_user_id INT,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) DEFAULT CHARSET=utf8mb4"""
    ]

    # Execute the creation queries
    for t in tables:
        cur.execute(t)

    conn.commit()
    cur.close()
    conn.close()
    
    print("✅ All tables created successfully in Clever Cloud MySQL!")

except Exception as e:
    print(f"❌ Error: {e}")
    