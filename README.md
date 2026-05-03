# EarlyDetect — Early Symptom Detection Platform

A Flask-based multi-modal health screening platform using voice, reaction time tests, and questionnaires to flag early disease indicators.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the app
python app.py

# 3. Open in browser
# http://localhost:5000
```

---

## Project Structure

```
early_symptom_platform/
├── app.py                   # Flask routes + API endpoints
├── requirements.txt
├── modules/
│   ├── questionnaire.py     # Scores 15-question lifestyle survey
│   ├── reaction_time.py     # Evaluates tap-test response speed
│   ├── voice_analysis.py    # Analyses pitch, energy, speech rate
│   └── risk_engine.py       # Combines all scores → disease risk profile
└── templates/
    ├── base.html            # Shared layout + dark theme
    ├── index.html           # Landing page
    ├── screening.html       # Multi-step screening (Q + RT + Voice)
    └── results.html         # Personalised risk report
```

---

## API Endpoints

| Method | Endpoint              | Description                              |
|--------|-----------------------|------------------------------------------|
| POST   | `/api/questionnaire`  | Submit questionnaire answers             |
| POST   | `/api/reaction-time`  | Submit reaction time trial list (ms)     |
| POST   | `/api/voice-analysis` | Submit voice feature data                |
| POST   | `/api/compute-risk`   | Combine all scores → disease risk profile|

### Example: Reaction Time

```bash
curl -X POST http://localhost:5000/api/reaction-time \
  -H "Content-Type: application/json" \
  -d '{"times": [240, 265, 310, 280, 295, 260, 305, 270]}'
```

### Example: Questionnaire

```bash
curl -X POST http://localhost:5000/api/questionnaire \
  -H "Content-Type: application/json" \
  -d '{"sleep_hours":5,"sleep_quality":2,"mood_low":"yes","anxiety_level":4,"stress_level":4,"exercise":1}'
```

---

## Diseases Screened

| Disease                    | Modules Used                       |
|----------------------------|------------------------------------|
| Mental Health (Depression) | Questionnaire + Voice              |
| Neurological (Parkinson's) | Questionnaire + Reaction Time + Voice |
| Metabolic (Diabetes Risk)  | Questionnaire                      |
| Cardiovascular (HTN Risk)  | Questionnaire + Voice              |
| Sleep Disorders            | Questionnaire + Reaction Time      |

---

## Extending to Real APIs

### Voice (replace `voice_analysis.py`)
- **AssemblyAI** — `pip install assemblyai`
- **Azure Cognitive Speech** — `pip install azure-cognitiveservices-speech`
- **Hume AI** — REST API for prosodic emotion

### Facial Expression (add new module)
- **DeepFace** — `pip install deepface`
- **Azure Face API**
- Webcam frame → `/api/facial-analysis` endpoint

---

## Disclaimer

This platform is a **screening tool only**. It does not provide medical diagnoses.
Always consult a qualified healthcare professional for any health concerns.
