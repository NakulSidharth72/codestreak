from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import razorpay
from datetime import date
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'codestreak_super_secret_key'

# SQLite Config
DATABASE = 'codestreak.db'

# ================= PROFILE PICTURE UPLOAD CONFIG =================
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Make sure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db():
    conn = sqlite3.connect(DATABASE, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    return conn

import json

def check_achievements(user_id):
    """Check and unlock achievements based on the user's current state."""
    conn = get_db()
    cur = conn.cursor()
    
    # Get current user state
    cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cur.fetchone()
    
    if not user:
        cur.close()
        conn.close()
        return []
    
    # Get completed lesson count
    cur.execute("SELECT COUNT(*) as count FROM progress WHERE user_id = ? AND status = 'completed'", (user_id,))
    completed_count = cur.fetchone()['count']
    
    # Get total lessons
    cur.execute("SELECT COUNT(*) as count FROM lessons")
    total_lessons = cur.fetchone()['count']
    
    # Parse current unlocked achievements
    try:
        unlocked = json.loads(user['achievements'] or '[]')
    except:
        unlocked = []
    
    # Define the achievement rules
    achievements_to_check = {
        'first_signal': completed_count >= 1,
        'five_crowns': completed_count >= 5,
        'royal_scholar': completed_count >= total_lessons,
        'seven_fires': user['streak'] >= 7,
        'treasury': user['total_points'] >= 100,
        'gold_tier': user['rank'] in ['Gold', 'Platinum'],
    }
    
    # Unlock new achievements
    newly_unlocked = []
    for key, condition in achievements_to_check.items():
        if condition and key not in unlocked:
            unlocked.append(key)
            newly_unlocked.append(key)
    
    # Save to DB
    if newly_unlocked:
        cur.execute("UPDATE users SET achievements = ? WHERE id = ?", 
                    (json.dumps(unlocked), user_id))
        conn.commit()
    
    cur.close()
    conn.close()
    return newly_unlocked


def update_user_rank(user_id):
    """Update the user's rank based on their total points."""
    conn = get_db()
    cur = conn.cursor()
    
    # Get current total XP
    cur.execute("SELECT total_points FROM users WHERE id = ?", (user_id,))
    user = cur.fetchone()
    
    if not user:
        cur.close()
        conn.close()
        return None
    
    xp = user['total_points']
    
    # Determine rank based on XP
    if xp >= 450:
        new_rank = 'Platinum'
    elif xp >= 300:
        new_rank = 'Gold'
    elif xp >= 100:
        new_rank = 'Silver'
    else:
        new_rank = 'Bronze'
    
    # Update the rank
    cur.execute("UPDATE users SET `rank` = ? WHERE id = ?", (new_rank, user_id))
    conn.commit()
    cur.close()
    conn.close()
    return new_rank

# Razorpay Config
RAZORPAY_KEY_ID = "rzp_test_xxxx"
RAZORPAY_KEY_SECRET = "your_razorpay_secret"
razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

# --- HELPER FUNCTION: Update Streak ---
def update_streak(user_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT streak, streak_charge, created_at FROM users WHERE id = ?", (user_id,))
    user = cur.fetchone()
    
    today = date.today()
    created = user['created_at']
    if created:
        if isinstance(created, str):
            last_active = date.fromisoformat(created[:10])
        else:
            last_active = created.date() if hasattr(created, 'date') else today
    else:
        last_active = today
    
    if (today - last_active).days == 1:
        new_streak = user['streak'] + 1
    elif (today - last_active).days > 1:
        if user['streak_charge'] > 0:
            new_streak = user['streak']
        else:
            new_streak = 0
    else:
        new_streak = user['streak']
    
    cur.execute("UPDATE users SET streak = ?, created_at = CURRENT_TIMESTAMP WHERE id = ?", (new_streak, user_id))
    conn.commit()
    cur.close()
    conn.close()
    return new_streak

# --- ROUTES ---

@app.route('/')
def landing():
    conn = get_db()
    cur = conn.cursor()
    
    # --- Calculate real stats ---
    
    # 1. Total users
    cur.execute("SELECT COUNT(*) as count FROM users")
    total_users = cur.fetchone()['count'] or 1  # avoid division by zero
    
    # 2. Users who completed at least 1 lesson
    cur.execute("""
        SELECT COUNT(DISTINCT user_id) as count 
        FROM progress 
        WHERE status = 'completed'
    """)
    active_users = cur.fetchone()['count']
    
    # 3. Users with streak >= 2 (retention)
    cur.execute("SELECT COUNT(*) as count FROM users WHERE streak >= 2")
    retained_users = cur.fetchone()['count']
    
    # 4. Total XP earned across all users
    cur.execute("SELECT COALESCE(SUM(total_points), 0) as total FROM users")
    total_xp = cur.fetchone()['total']
    
    # 5. Total lessons completed
    cur.execute("SELECT COUNT(*) as count FROM progress WHERE status = 'completed'")
    total_completions = cur.fetchone()['count']
    
    cur.close()
    conn.close()
    
    # Calculate percentages
    lesson_completion_pct = round((active_users / total_users) * 100) if total_users > 0 else 0
    retention_pct = round((retained_users / total_users) * 100) if total_users > 0 else 0
    
    # Average XP per completion (capped at 100% for the bar)
    avg_xp = round(total_xp / total_completions) if total_completions > 0 else 0
    avg_xp_pct = min(100, avg_xp)  # cap at 100 for display
    
    stats = {
        'lesson_completion': lesson_completion_pct,
        'retention': retention_pct,
        'avg_xp': avg_xp,
        'avg_xp_pct': avg_xp_pct,
        'total_users': total_users,
        'active_users': active_users,
        'total_xp': total_xp,
    }
    
    return render_template('landing.html', stats=stats)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        security_question = request.form['security_question']
        security_answer = request.form['security_answer'].lower().strip()
        
        hashed_password = generate_password_hash(password)
        hashed_answer = generate_password_hash(security_answer)
        
        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO users (username, email, password_hash, security_question, security_answer) VALUES (?, ?, ?, ?, ?)", 
                (username, email, hashed_password, security_question, hashed_answer)
            )
            conn.commit()
            flash('Account created! Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            conn.rollback()
            flash('Username or Email already exists!', 'danger')
        finally:
            cur.close()
            conn.close()
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cur.fetchone()
        cur.close()
        conn.close()
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    update_streak(session['user_id'])
    update_user_rank(session['user_id'])
    check_achievements(session['user_id'])
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
    user = cur.fetchone()
    
    cur.execute("SELECT * FROM lessons ORDER BY order_index ASC")
    lessons = cur.fetchall()
    
    cur.close()
    conn.close()
    return render_template('dashboard.html', user=user, lessons=lessons)

@app.route('/lessons')
def lessons():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM lessons ORDER BY order_index ASC")
    lessons = cur.fetchall()
    cur.close()
    conn.close()
    
    return render_template('lessons.html', lessons=lessons)

@app.route('/lesson/<int:lesson_id>')
def lesson(lesson_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM lessons WHERE id = ?", (lesson_id,))
    lesson = cur.fetchone()
    cur.close()
    conn.close()
    
    if not lesson:
        flash('Lesson not found', 'danger')
        return redirect(url_for('dashboard'))
    
    return render_template('lesson.html', lesson=lesson)

@app.route('/complete_lesson/<int:lesson_id>', methods=['POST'])
def complete_lesson(lesson_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get the lesson info and the user's answer
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM lessons WHERE id = ?", (lesson_id,))
    lesson = cur.fetchone()
    
    user_answer = request.form.get('answer')  # e.g., 'B', 'C', etc.
    
    if lesson:
        if user_answer and user_answer.upper() == lesson['correct_option']:
            xp = lesson['points']
            cur.execute("UPDATE users SET total_points = total_points + ?, weekly_points = weekly_points + ? WHERE id = ?", 
                        (xp, xp, session['user_id']))
            cur.execute("SELECT id FROM progress WHERE user_id = ? AND lesson_id = ?", 
                        (session['user_id'], lesson_id))
            existing = cur.fetchone()
            if existing:
                cur.execute("UPDATE progress SET status = 'completed', score = ? WHERE id = ?", 
                            (xp, existing['id']))
            else:
                cur.execute("INSERT INTO progress (user_id, lesson_id, status, score) VALUES (?, ?, 'completed', ?)", 
                            (session['user_id'], lesson_id, xp))
            conn.commit()
            # After awarding XP and committing:
            update_user_rank(session['user_id'])
            check_achievements(session['user_id'])  
            flash(f'🎉 Correct! You earned {xp} XP!', 'success')
            
            # Redirect to the NEXT lesson if it exists
            next_lesson_id = lesson['next_lesson_id']   
            if next_lesson_id is not None:
                return redirect(url_for('lesson', lesson_id=next_lesson_id))
            else:
                # If no next lesson, go to dashboard
                return redirect(url_for('dashboard'))
        else:
            flash('❌ Incorrect answer. Go back and review the lesson.', 'danger')
    
    cur.close()
    conn.close()
    return redirect(url_for('lesson', lesson_id=lesson_id))

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
    user = cur.fetchone()
    cur.close()
    conn.close()
    
    return render_template('settings.html', user=user)

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Make sure achievements and rank are up to date
    update_user_rank(session['user_id'])
    check_achievements(session['user_id'])
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
    user = cur.fetchone()
    
    # Count completed lessons
    cur.execute("""
        SELECT COUNT(*) as count 
        FROM progress 
        WHERE user_id = ? AND status = 'completed'
    """, (session['user_id'],))
    completed_lessons = cur.fetchone()['count']
    
    # Total lessons
    cur.execute("SELECT COUNT(*) as count FROM lessons")
    total_lessons = cur.fetchone()['count']
    
    # Recent activity (last 5 completed lessons)
    cur.execute("""
        SELECT p.completed_at, l.title, p.score
        FROM progress p
        JOIN lessons l ON p.lesson_id = l.id
        WHERE p.user_id = ? AND p.status = 'completed'
        ORDER BY p.completed_at DESC
        LIMIT 5
    """, (session['user_id'],))
    recent_activity = cur.fetchall()
    
    # Streak calendar (last 30 days)
    cur.execute("""
        SELECT DATE(completed_at) as day
        FROM progress
        WHERE user_id = ? AND status = 'completed'
        AND completed_at >= datetime('now', '-30 days')
        GROUP BY DATE(completed_at)
    """, (session['user_id'],))
    active_days = [str(row['day'])[:10] for row in cur.fetchall()]
    
    # Build calendar data
    from datetime import date, timedelta
    today = date.today()
    calendar_days = []
    for i in range(29, -1, -1):
        d = today - timedelta(days=i)
        calendar_days.append({
            'date': d.strftime('%Y-%m-%d'),
            'day_num': d.day,
            'active': d.strftime('%Y-%m-%d') in active_days,
        })
    
    cur.close()
    conn.close()
    
    # Parse achievements
    try:
        unlocked = json.loads(user['achievements'] or '[]')
    except:
        unlocked = []
    
    # Full achievement list
    all_achievements = [
        {'id': 'first_signal', 'title': 'First Signal', 'icon': '01', 'tone': '#3FA9F5'},
        {'id': 'five_crowns', 'title': 'Five Crowns', 'icon': '05', 'tone': '#F5B942'},
        {'id': 'royal_scholar', 'title': 'Royal Scholar', 'icon': '★', 'tone': '#B888E8'},
        {'id': 'seven_fires', 'title': 'Seven Fires', 'icon': '🔥', 'tone': '#F5893D'},
        {'id': 'treasury', 'title': 'Treasury', 'icon': '💰', 'tone': '#F5B942'},
        {'id': 'gold_tier', 'title': 'Gold Tier', 'icon': '👑', 'tone': '#F5B942'},
    ]
    for ach in all_achievements:
        ach['unlocked'] = ach['id'] in unlocked
    
    return render_template(
        'profile.html',
        user=user,
        completed_lessons=completed_lessons,
        total_lessons=total_lessons,
        unlocked_count=len(unlocked),
        recent_activity=recent_activity,
        calendar_days=calendar_days,
        achievements=all_achievements,
    )


@app.route('/update_bio', methods=['POST'])
def update_bio():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    bio = request.form.get('bio', '').strip()[:300]
    learning_goal = request.form.get('learning_goal', '').strip()[:100]
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET bio = ?, learning_goal = ? WHERE id = ?",
        (bio, learning_goal, session['user_id'])
    )
    conn.commit()
    cur.close()
    conn.close()
    
    flash('Profile updated!', 'success')
    return redirect(url_for('profile'))

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    username = request.form['username']
    email = request.form['email']
    
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE users SET username = ?, email = ? WHERE id = ?", 
                    (username, email, session['user_id']))
        conn.commit()
        flash('Profile updated successfully!', 'success')
    except:
        conn.rollback()
        flash('Username or Email already taken!', 'danger')
    finally:
        cur.close()
        conn.close()
    
    return redirect(url_for('settings'))

@app.route('/leaderboard')
def leaderboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db()
    cur = conn.cursor()
    
    update_user_rank(session['user_id'])
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, username, weekly_points, `rank`, profile_picture
        FROM users 
        ORDER BY weekly_points DESC 
        LIMIT 20
    """)
    users = cur.fetchall()
    cur.close()
    conn.close()
    
    return render_template('leaderboard.html', users=users)

@app.route('/payment', methods=['GET', 'POST'])
def payment():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # DEMO MODE: Simulate a successful payment without Razorpay
        conn = get_db()
        cur = conn.cursor()
        cur.execute("UPDATE users SET premium = 1 WHERE id = ?", (session['user_id'],))
        conn.commit()
        cur.close()
        conn.close()
        
        flash('💎 Welcome to Premium! Enjoy advanced features.', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('payment.html')

@app.route('/payment/success', methods=['POST'])
def payment_success():
    razorpay_order_id = session.get('razorpay_order_id')
    razorpay_payment_id = request.form.get('razorpay_payment_id')
    razorpay_signature = request.form.get('razorpay_signature')
    
    params_dict = {
        'razorpay_order_id': razorpay_order_id,
        'razorpay_payment_id': razorpay_payment_id,
        'razorpay_signature': razorpay_signature
    }
    
    try:
        razorpay_client.utility.verify_payment_signature(params_dict)
        conn = get_db()
        cur = conn.cursor()
        cur.execute("UPDATE users SET premium = 1 WHERE id = ?", (session['user_id'],))
        cur.execute("INSERT INTO payments (user_id, amount, payment_status, transaction_id) VALUES (?, 500, 'success', ?)", 
                    (session['user_id'], razorpay_payment_id))
        conn.commit()
        cur.close()
        conn.close()
        flash('Payment Successful! You are now a Premium member!', 'success')
        return redirect(url_for('dashboard'))
    except:
        flash('Payment verification failed', 'danger')
        return redirect(url_for('payment'))

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('landing'))

# ================= PASSWORD RESET =================

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cur.fetchone()
        cur.close()
        conn.close()
        
        if not user:
            flash('No account found with that email.', 'danger')
            return redirect(url_for('forgot_password'))
        
        # Store the email in session so the next step knows who's resetting
        session['reset_email'] = email
        return redirect(url_for('security_question'))
    
    return render_template('forgot_password.html')


@app.route('/security_question', methods=['GET', 'POST'])
def security_question():
    email = session.get('reset_email')
    if not email:
        flash('Please start the password reset process again.', 'danger')
        return redirect(url_for('forgot_password'))
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('forgot_password'))
    
    if request.method == 'POST':
        answer = request.form['security_answer'].lower().strip()
        
        if check_password_hash(user['security_answer'], answer):
            session['reset_verified'] = True
            return redirect(url_for('reset_password'))
        else:
            flash('Incorrect answer. Try again.', 'danger')
    
    return render_template('security_question.html', question=user['security_question'])


@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if not session.get('reset_verified'):
        flash('Please verify your identity first.', 'danger')
        return redirect(url_for('forgot_password'))
    
    if request.method == 'POST':
        new_password = request.form['new_password']
        hashed = generate_password_hash(new_password)
        
        conn = get_db()
        cur = conn.cursor()
        cur.execute("UPDATE users SET password_hash = ? WHERE email = ?", 
                    (hashed, session['reset_email']))
        conn.commit()
        cur.close()
        conn.close()
        
        # Clear the reset session flags
        session.pop('reset_email', None)
        session.pop('reset_verified', None)
        
        flash('✅ Password reset successfully! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('reset_password.html')

@app.route('/achievements')
def achievements():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Make sure achievements and rank are up to date
    update_user_rank(session['user_id'])
    check_achievements(session['user_id'])
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],))
    user = cur.fetchone()
    cur.close()
    conn.close()
    
    # Parse the user's unlocked achievements
    try:
        unlocked = json.loads(user['achievements'] or '[]')
    except:
        unlocked = []
    
    # Define the full list of achievements with metadata
    all_achievements = [
        {
            'id': 'first_signal',
            'title': 'First Signal',
            'description': 'Complete your first lesson',
            'icon': '01',
            'tone': '#3FA9F5'
        },
        {
            'id': 'five_crowns',
            'title': 'Five Crowns',
            'description': 'Complete five lessons',
            'icon': '05',
            'tone': '#F5B942'
        },
        {
            'id': 'royal_scholar',
            'title': 'Royal Scholar',
            'description': 'Complete all lessons',
            'icon': '★',
            'tone': '#B888E8'
        },
        {
            'id': 'seven_fires',
            'title': 'Seven Fires',
            'description': 'Hold a 7-day streak',
            'icon': '🔥',
            'tone': '#F5893D'
        },
        {
            'id': 'treasury',
            'title': 'Treasury',
            'description': 'Bank more than 100 XP',
            'icon': '💰',
            'tone': '#F5B942'
        },
        {
            'id': 'gold_tier',
            'title': 'Gold Tier',
            'description': 'Reach the Gold leaderboard tier',
            'icon': '👑',
            'tone': '#F5B942'
        },
    ]
    
    # Add unlocked status to each
    for ach in all_achievements:
        ach['unlocked'] = ach['id'] in unlocked
    
    return render_template('achievements.html', user=user, achievements=all_achievements)

# ================= PROFILE PICTURE UPLOAD =================
@app.route('/upload_profile_picture', methods=['POST'])
def upload_profile_picture():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if 'profile_picture' not in request.files:
        flash('No file selected.', 'danger')
        return redirect(url_for('profile'))
    
    file = request.files['profile_picture']
    
    if file.filename == '':
        flash('No file selected.', 'danger')
        return redirect(url_for('profile'))
    
    if file and allowed_file(file.filename):
        # Generate a unique filename
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"user_{session['user_id']}.{ext}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Delete old picture if it exists (with different extension)
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT profile_picture FROM users WHERE id = ?", (session['user_id'],))
        old = cur.fetchone()
        
        if old and old['profile_picture']:
            old_path = os.path.join(app.config['UPLOAD_FOLDER'], old['profile_picture'])
            if os.path.exists(old_path) and old['profile_picture'] != filename:
                try:
                    os.remove(old_path)
                except:
                    pass
        
        # Save the new file
        file.save(filepath)
        
        # Update the database
        cur.execute("UPDATE users SET profile_picture = ? WHERE id = ?",
                    (filename, session['user_id']))
        conn.commit()
        cur.close()
        conn.close()
        
        flash('✅ Profile picture updated!', 'success')
    else:
        flash('Invalid file type. Please upload a PNG, JPG, GIF, or WEBP.', 'danger')
    
    return redirect(url_for('profile'))


@app.route('/remove_profile_picture', methods=['POST'])
def remove_profile_picture():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT profile_picture FROM users WHERE id = ?", (session['user_id'],))
    user = cur.fetchone()
    
    if user and user['profile_picture']:
        old_path = os.path.join(app.config['UPLOAD_FOLDER'], user['profile_picture'])
        if os.path.exists(old_path):
            try:
                os.remove(old_path)
            except:
                pass
        
        cur.execute("UPDATE users SET profile_picture = NULL WHERE id = ?", (session['user_id'],))
        conn.commit()
        flash('Profile picture removed.', 'info')
    
    cur.close()
    conn.close()
    return redirect(url_for('profile'))

# ================= ERROR HANDLERS =================

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
    