from flask import Flask, request, jsonify, render_template
import sqlite3
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'lilbrain_api_key'
conn = sqlite3.connect('lilbrain.db', check_same_thread=False)
cursor = conn.cursor()

# ✅ Home route (for Render to load homepage)
@app.route("/")
def home():
    return render_template("home.html")

# ✅ Chatbot logic
def smartie_response(message):
    message = message.lower()
    if "powerhouse" in message and "cell" in message:
        return "The mitochondrion is the powerhouse of the cell!"
    elif "pi" in message:
        return "Pi is about 3.14159... and it never ends. Like your curiosity!"
    else:
        return "That's a great question! I'll get smarter just like you."

# ✅ API routes
@app.route('/api/leaderboard', methods=['GET'])
def leaderboard():
    cursor.execute("SELECT username, xp, streak FROM users ORDER BY xp DESC")
    data = [{"username": r[0], "xp": r[1], "streak": r[2]} for r in cursor.fetchall()]
    return jsonify(data)

@app.route('/api/quiz/start', methods=['POST'])
def start_quiz():
    payload = request.get_json()
    username = payload.get("username")
    category = payload.get("category")
    cursor.execute("SELECT age_group FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    if not row:
        return jsonify({"error": "User not found"}), 404
    age_group = row[0]
    cursor.execute("""
        SELECT id, question_text, option_a, option_b, option_c, option_d
        FROM questions
        WHERE category = ? AND age_group = ?
        LIMIT 5
    """, (category, age_group))
    rows = cursor.fetchall()
    return jsonify([{
        "id": r[0],
        "question": r[1],
        "options": {"A": r[2], "B": r[3], "C": r[4], "D": r[5]}
    } for r in rows])

@app.route('/api/quiz/submit', methods=['POST'])
def submit_quiz():
    payload = request.get_json()
    username = payload.get("username")
    answers = payload.get("answers", {})
    score = 0
    for qid, ans in answers.items():
        cursor.execute("SELECT correct_answer FROM questions WHERE id = ?", (qid,))
        correct = cursor.fetchone()
        if correct and correct[0].upper() == ans.upper():
            score += 10
    cursor.execute("SELECT xp, streak FROM users WHERE username = ?", (username,))
    xp, streak = cursor.fetchone()
    full_score = len(answers) * 10
    new_xp = xp + score
    new_streak = streak + 1 if score == full_score else 0
    cursor.execute("UPDATE users SET xp = ?, streak = ? WHERE username = ?", (new_xp, new_streak, username))
    conn.commit()
    if score == 0:
        reaction = "Oops! Time to recharge that lil brain!"
    elif score < full_score:
        reaction = "Not bad! You’re warming up!"
    else:
        reaction = "Brainiac alert! You crushed it!"
    return jsonify({"score": score, "new_xp": new_xp, "streak": new_streak, "reaction": reaction})

@app.route('/api/chatbot', methods=['POST'])
def chatbot():
    payload = request.get_json()
    username = payload.get("username")
    message = payload.get("message")
    cursor.execute("SELECT is_premium FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    if not row:
        return jsonify({"error": "User not found"}), 404
    if not row[0]:
        return jsonify({"error": "Premium required"}), 403
    return jsonify({"user": message, "smartie": smartie_response(message)})

@app.route('/api/admin/questions', methods=['GET'])
def list_questions():
    cursor.execute("SELECT id, category, question_text, correct_answer, age_group FROM questions")
    q = cursor.fetchall()
    return jsonify([{
        "id": r[0], "category": r[1], "question": r[2],
        "answer": r[3], "age_group": r[4]
    } for r in q])

# ✅ Run Flask using the PORT Render provides
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
