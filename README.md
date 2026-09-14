# 🎮 CodeStreak — Gamified Programming Learning Platform

A modern, full-stack web application that teaches Python through **gamified lessons**, **daily streaks**, **XP rewards**, and **weekly leaderboards** — built with Flask, MySQL, and a premium dark theme.

---

## 📖 Overview

**CodeStreak** turns learning to code into a habit-building game. Learners progress through structured lessons, earn XP for correct answers, maintain daily streaks, and compete on a weekly leaderboard. The platform includes **interactive quizzes**, **achievements**, **password reset**, and a **Razorpay payment integration** for premium plans.

Built by **Nakul Sidarth, Harish, and Srivatsa** as a final-year CS project.

---

## ✨ Features

### 🎓 Learning Platform
- **Structured Curriculum:** 9 lessons across 3 levels (Basics → Intermediate → Advanced)
- **Interactive Quizzes:** Multiple-choice questions at the end of each lesson
- **Auto-Advance:** Complete a lesson correctly → move to the next automatically
- **Rich Content:** Code snippets, explanations, and examples in every lesson

### 🎮 Gamification
- **XP System:** Earn 15+ XP per correct answer
- **Daily Streaks:** Grow your streak by completing at least 1 lesson per day
- **Recovery Charges:** One charge saves a single missed day; earned every 7-day milestone
- **4-Tier Ranking:** Bronze → Silver → Gold → Platinum
- **Weekly Leaderboard:** Compete with other learners; resets every Monday
- **Achievements:** 6 unlockable badges based on real progress

### 🔐 Authentication & Security
- **Secure Registration:** Bcrypt password hashing (via Werkzeug)
- **Login System:** Session-based authentication
- **Password Reset:** Security-question flow with 3-step verification
- **Parameterized SQL:** All queries use safe placeholders to prevent SQL injection
- **Custom Error Pages:** Beautiful 404 and 500 pages

### 💎 User Experience
- **Premium Dark Theme:** Azure Blue + Amber Gold + Emerald accents
- **Toast Notifications:** All feedback appears as animated toasts
- **Glow Cursor:** Subtle glowing cursor effect on the landing page
- **Parallax Scroll:** Cinematic scroll-scrubbing animations
- **3D Rotating Cubes:** CSS 3D platform overview
- **Penguin Mascot:** Friendly character with typewriter speech bubbles
- **Responsive Design:** Works on desktop, tablet, and mobile

### 💳 Payment Integration
- **Razorpay (Test Mode):** Secure payment framework for Pro/Teams plans
- **Premium User Flag:** Database tracks which users are premium

---

## 🛠️ Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Frontend** | HTML5, CSS3, Vanilla JavaScript, Jinja2 Templates |
| **Backend** | Python 3, Flask |
| **Database** | MySQL |
| **Authentication** | Flask Sessions, Werkzeug Password Hashing |
| **Payments** | Razorpay (Test Mode) |
| **Fonts** | Playfair Display, Poppins, Orbitron |

---

## 📁 Project Structure

---

## 🗄️ Database Schema

### `users` table
| Column | Type | Description |
| :--- | :--- | :--- |
| id | INT PK | User ID |
| username | VARCHAR(50) | Unique username |
| email | VARCHAR(100) | Unique email |
| password_hash | VARCHAR(255) | Bcrypt-hashed password |
| security_question | VARCHAR(255) | For password reset |
| security_answer | VARCHAR(255) | Hashed answer |
| streak | INT | Current day streak |
| streak_charge | INT | Available recovery charges |
| total_points | INT | Lifetime XP |
| weekly_points | INT | Weekly XP (resets Monday) |
| rank | VARCHAR(20) | Bronze / Silver / Gold / Platinum |
| premium | BOOLEAN | Premium membership flag |
| achievements | VARCHAR(500) | JSON array of unlocked badges |
| created_at | TIMESTAMP | Account creation |

### `lessons` table
| Column | Type | Description |
| :--- | :--- | :--- |
| id | INT PK | Lesson ID |
| title | VARCHAR(100) | Lesson name |
| level | VARCHAR(20) | Beginner / Intermediate / Advanced |
| points | INT | XP awarded |
| difficulty | VARCHAR(10) | Easy / Medium / Hard |
| content | TEXT | Code snippet |
| explanation | TEXT | Long-form teaching content |
| question | TEXT | Quiz question |
| option_a, option_b, option_c | VARCHAR(255) | Multiple choice options |
| correct_option | VARCHAR(1) | 'A', 'B', or 'C' |
| next_lesson_id | INT | Auto-advance target |
| order_index | INT | Display order |

### `progress` table
| Column | Type | Description |
| :--- | :--- | :--- |
| id | INT PK | Progress entry ID |
| user_id | INT FK | References users.id |
| lesson_id | INT FK | References lessons.id |
| status | VARCHAR(20) | 'in_progress' or 'completed' |
| score | INT | XP earned |
| completed_at | TIMESTAMP | Completion time |

### `payments` table
| Column | Type | Description |
| :--- | :--- | :--- |
| id | INT PK | Payment ID |
| user_id | INT FK | References users.id |
| amount | DECIMAL(10,2) | Payment amount |
| payment_status | VARCHAR(20) | pending / success / failed |
| transaction_id | VARCHAR(100) | Razorpay transaction ID |
| created_at | TIMESTAMP | Payment timestamp |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- MySQL 8.0+
- pip (Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd codestreak
   