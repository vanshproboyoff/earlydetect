from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from datetime import datetime

from database import (
    init_db,
    create_user,
    verify_user,
    save_screening,
    get_screenings
)

from modules.questionnaire import evaluate_questionnaire
from modules.reaction_time import evaluate_reaction_time
from modules.voice_analysis import analyze_voice_features
from modules.risk_engine import compute_risk_profile
from modules.facial_analysis import analyze_face


app = Flask(__name__)

app.secret_key = "esp-secret-key-change-in-production"

# Initialize database
init_db()


# =========================
# REGISTER
# =========================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not name or not username or not password:
            return render_template(
                "register.html",
                error="Please fill in all fields."
            )

        if len(password) < 6:
            return render_template(
                "register.html",
                error="Password must be at least 6 characters."
            )

        if create_user(name, username, password):

            user = verify_user(username, password)

            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["name"] = user["name"]

            return redirect(url_for("index"))

        return render_template(
            "register.html",
            error="Username already exists."
        )

    return render_template("register.html")


# =========================
# LOGIN
# =========================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = verify_user(username, password)

        if user:

            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["name"] = user["name"]

            return redirect(url_for("index"))

        return render_template(
            "login.html",
            error="Invalid username or password."
        )

    return render_template("login.html")


# =========================
# LOGOUT
# =========================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# =========================
# HOME
# =========================

@app.route("/")
def index():

    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template(
        "index.html",
        name=session.get("name", "User"),
        username=session.get("username", "")
    )


# =========================
# SCREENING
# =========================

@app.route("/screening")
def screening():

    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template(
        "screening.html",
        name=session.get("name", "User"),
        username=session.get("username", "")
    )


# =========================
# RESULTS
# =========================

@app.route("/results")
def results():

    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template(
        "results.html",
        name=session.get("name", "User"),
        username=session.get("username", "")
    )


# =========================
# HISTORY
# =========================

@app.route("/history")
def history():

    if "user_id" not in session:
        return redirect(url_for("login"))

    screenings = get_screenings(session["user_id"])

    return render_template(
        "history.html",
        screenings=screenings,
        name=session.get("name", "User"),
        username=session.get("username", "")
    )


# =========================
# QUESTIONNAIRE API
# =========================

@app.route("/api/questionnaire", methods=["POST"])
def api_questionnaire():

    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    result = evaluate_questionnaire(data)

    return jsonify(result)


# =========================
# REACTION TIME API
# =========================

@app.route("/api/reaction-time", methods=["POST"])
def api_reaction_time():

    data = request.get_json()

    if not data or "times" not in data:
        return jsonify({"error": "No reaction times provided"}), 400

    result = evaluate_reaction_time(data["times"])

    return jsonify(result)


# =========================
# VOICE API
# =========================

@app.route("/api/voice-analysis", methods=["POST"])
def api_voice_analysis():

    data = request.get_json()

    if not data:
        return jsonify({"error": "No voice data provided"}), 400

    result = analyze_voice_features(data)

    return jsonify(result)


# =========================
# FACIAL API
# =========================

@app.route("/api/facial-analysis", methods=["POST"])
def api_facial_analysis():

    data = request.get_json()

    if not data or "image" not in data:
        return jsonify({"error": "No image provided"}), 400

    result = analyze_face(data["image"])

    return jsonify(result)


# =========================
# COMPUTE RISK
# =========================

@app.route("/api/compute-risk", methods=["POST"])
def api_compute_risk():

    if "user_id" not in session:
        return jsonify({"error": "Login required"}), 401

    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    result = compute_risk_profile(data)

    # Save screening to logged-in user's history
    save_screening(
        session["user_id"],
        result,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

    return jsonify(result)


# =========================
# RUN
# =========================

if __name__ == "__main__":
    app.run(debug=True, port=5000)