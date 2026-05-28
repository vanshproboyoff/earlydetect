from flask import Flask, render_template, request, jsonify, session
import uuid
import json
from modules.questionnaire import evaluate_questionnaire
from modules.reaction_time import evaluate_reaction_time
from modules.voice_analysis import analyze_voice_features
from modules.risk_engine import compute_risk_profile
from modules.facial_analysis import analyze_face

app = Flask(__name__)
app.secret_key = "esp-secret-key-change-in-production"

@app.route("/")
def index():
    session["user_id"] = str(uuid.uuid4())
    return render_template("index.html")

@app.route("/screening")
def screening():
    return render_template("screening.html")

@app.route("/results")
def results():
    return render_template("results.html")

@app.route("/api/questionnaire", methods=["POST"])
def api_questionnaire():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    result = evaluate_questionnaire(data)
    return jsonify(result)

@app.route("/api/reaction-time", methods=["POST"])
def api_reaction_time():
    data = request.get_json()
    if not data or "times" not in data:
        return jsonify({"error": "No reaction times provided"}), 400
    result = evaluate_reaction_time(data["times"])
    return jsonify(result)

@app.route("/api/voice-analysis", methods=["POST"])
def api_voice_analysis():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No voice data provided"}), 400
    result = analyze_voice_features(data)
    return jsonify(result)

@app.route("/api/facial-analysis", methods=["POST"])
def api_facial_analysis():
    data = request.get_json()
    if not data or "image" not in data:
        return jsonify({"error": "No image provided"}), 400
    result = analyze_face(data["image"])
    return jsonify(result)

@app.route("/api/compute-risk", methods=["POST"])
def api_compute_risk():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    result = compute_risk_profile(data)
    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True, port=5000)