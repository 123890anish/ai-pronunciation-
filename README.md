# AI-Powered English Pronunciation & Grammar Assessment Web Application

A complete, production-oriented, modular web application built with **Django**, **Python**, **Ollama (Qwen2.5:1.5b)**, and **Whisper Speech-to-Text**.

---

## 🎯 Architecture & Objectives

1. **Secure Multi-User System**: Registration, login, password enforcement, and strict user data isolation.
2. **Audio Capture**: Browser-native `MediaRecorder` recording interface with live timer, preview, and audio upload support (WAV, MP3, M4A, WebM, OGG up to 20MB).
3. **Speech-to-Text Pipeline**: Interchangeable STT component powered by local Whisper.
4. **LLM Grammar Correction**: Local Ollama model (`qwen2.5:1.5b`) with T5 and heuristic fallback modes.
5. **Pedagogical Feedback**: Learner-friendly explanations of grammatical and lexical issues.
6. **Transparent Scoring**: Strictly separates grammar correctness from phoneme-level pronunciation. Displays disclaimer that speech recognition produces text transcripts and does not measure acoustic phoneme precision without acoustic alignment models.
7. **Scoreboard & History**: Progress tracking with Chart.js, assessment records, audio playback, and user data privacy controls.

---

## 📁 Project Structure

```text
pronunciation_assessment/
│
├── manage.py                     # Django administrative entry point
├── requirements.txt              # Production and development dependencies
├── README.md                     # Documentation and execution guide
├── .env                          # Local environment variables (untracked)
├── .env.example                  # Environment configuration template
├── .gitignore                    # Git ignore file
├── test_ollama_connectivity.py   # Standalone Ollama verification script
│
├── config/                       # Project configuration
│   ├── __init__.py
│   ├── settings.py               # Django settings (merged with configure.py)
│   ├── urls.py                   # Global URL routing
│   ├── asgi.py
│   └── wsgi.py
│
├── configure.yaml                # Safe, non-sensitive application settings
├── configure.py                  # Centralized typed configuration loader
├── common.py                     # Reusable text normalization, edit distance & helpers
│
├── llm/                          # LLM integration & prompt templates
│   ├── __init__.py
│   ├── model.py                  # Ollama HTTP API client with timeouts & logging
│   ├── correction.py             # Sentence correction (Ollama, T5, fallback)
│   ├── feedback.py               # Pedagogical learner feedback generator
│   ├── prompts.py                # Structured system & user prompts
│   ├── scoring.py                # Deterministic scoring engine
│   └── exceptions.py             # Custom exceptions
│
├── pipeline/                     # 5-Stage Assessment Pipeline
│   ├── __init__.py
│   ├── audio_pipeline.py         # Stage 1: Validation, storage & normalization
│   ├── transcription_pipeline.py # Stage 2: Speech recognition inference
│   ├── assessment_pipeline.py    # Stage 3: Grammar correction & feedback
│   ├── scoring_pipeline.py       # Stage 4: Transparent scoring calculations
│   └── history_pipeline.py       # Stage 5: User dashboard analytics & progress
│
├── audio/                        # Low-level audio processing
│   ├── __init__.py
│   ├── recorder.py               # User audio storage partitioning
│   ├── processor.py              # WAV normalization via FFmpeg / pydub
│   ├── speech_to_text.py         # Whisper & mock speech recognition
│   └── validators.py             # Audio extension, size & MIME validation
│
├── accounts/                     # Authentication app
│   ├── __init__.py
│   ├── models.py
│   ├── forms.py                  # Registration & login forms
│   ├── views.py                  # Register, login, logout views
│   ├── urls.py
│   └── tests.py                  # Accounts & auth unit tests
│
├── assessments/                  # Assessment app
│   ├── __init__.py
│   ├── models.py                 # Assessment model with audio & score fields
│   ├── forms.py                  # Audio submission form
│   ├── views.py                  # Dashboard, record, result, history, detail
│   ├── urls.py                   # Assessment routes
│   ├── dashboard_urls.py         # Dashboard routes
│   ├── services.py               # Business logic layer
│   ├── admin.py                  # Django admin registration
│   └── tests.py                  # User isolation & assessment tests
│
├── templates/                    # HTML5 / Bootstrap 5 templates
│   ├── base.html                 # Navigation, alerts & footer layout
│   ├── accounts/
│   │   ├── login.html
│   │   └── register.html
│   ├── dashboard/
│   │   └── index.html            # Metrics cards, Chart.js progress & activity
│   └── assessments/
│       ├── record.html           # MediaRecorder microphone & upload tabs
│       ├── result.html           # Scoreboard, comparison & audio playback
│       ├── history.html          # Paginated history table & audio player
│       └── detail.html
│
├── static/
│   ├── css/style.css
│   ├── js/recorder.js            # MediaRecorder controller & timer
│   └── js/dashboard.js
│
├── media/recordings/             # Private user audio storage
│
└── tests/                        # Automated unit tests
    ├── __init__.py
    ├── test_audio.py
    ├── test_llm.py
    └── test_pipeline.py
```

---

## 🚀 Step-by-Step Local Setup Instructions

### Step 1: Create and Activate a Virtual Environment

```bash
# On macOS / Linux:
python3 -m venv .venv
source .venv/bin/activate

# On Windows:
python -m venv .venv
.venv\Scripts\activate
```

### Step 2: Install System & Python Dependencies

Make sure **FFmpeg** is installed on your system (required for audio conversion and Whisper):
- **Ubuntu/Debian**: `sudo apt update && sudo apt install -y ffmpeg`
- **macOS (Homebrew)**: `brew install ffmpeg`
- **Windows (Chocolatey)**: `choco install ffmpeg`

Install the Python dependencies:
```bash
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables

Copy the provided example file:
```bash
cp .env.example .env
```

Review or modify `.env`:
- `DJANGO_SECRET_KEY`: Set a secure unique random key.
- `OLLAMA_URL`: Default is `http://localhost:11434/api/generate`.
- `OLLAMA_MODEL`: Default is `qwen2.5:1.5b`.
- `SPEECH_RECOGNITION_PROVIDER`: `whisper` (or `mock` for testing without audio models).
- `GRAMMAR_CORRECTION_PROVIDER`: `ollama` (or `rule_based`).

### Step 4: Install and Start Ollama

1. Download and install Ollama from [https://ollama.ai](https://ollama.ai).
2. Start the daemon in a separate terminal:
   ```bash
   ollama serve
   ```
3. Pull the required model:
   ```bash
   ollama pull qwen2.5:1.5b
   ```
4. Verify Ollama connectivity:
   ```bash
   python test_ollama_connectivity.py
   ```

### Step 5: Initialize the Database

Run migrations to set up SQLite (or PostgreSQL if configured):
```bash
python manage.py makemigrations accounts assessments
python manage.py migrate
```

### Step 6: Create an Administrator

```bash
python manage.py createsuperuser
```

### Step 7: Run Automated Unit Tests

Execute the unit test suite (runs with mocked external calls so a live LLM is not mandatory for CI/tests):
```bash
python manage.py test
```

### Step 8: Start the Development Server

```bash
python manage.py runserver
```

Open your browser at:
👉 **http://127.0.0.1:8000**

---

## 🔒 Security & Data Privacy

1. **CSRF Protection**: All form submissions and AJAX requests validate Django CSRF tokens.
2. **User Isolation**: All assessment records and audio recordings are strictly filtered by `user=request.user`. A user attempting to access another user's assessment ID receives a `404 Not Found`.
3. **Data Deletion**: Users can delete individual assessment records and audio recordings directly from the History page.
4. **Input Sanitization**: File uploads enforce MIME type validation, file extension whitelisting, and strict size caps (default 20MB).

---

## 💡 Troubleshooting

- **Ollama Connection Refused**:
  Run `ollama serve` and check `curl http://localhost:11434/api/tags`.
- **Whisper Out of Memory**:
  By default, `WHISPER_MODEL=base` is configured in `.env`, using ~1GB VRAM/RAM. On resource-constrained devices, set `WHISPER_MODEL=tiny`.
- **Microphone Blocked in Browser**:
  Modern browsers require HTTPS or `localhost` to allow `navigator.mediaDevices.getUserMedia`. Ensure you access the app via `http://localhost:8000` or `http://127.0.0.1:8000`.
