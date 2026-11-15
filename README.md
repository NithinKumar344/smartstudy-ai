# Smart Student Timetable Generator

A responsive student study-planner web app built with Python Flask, SQLite, HTML, CSS and JavaScript.

## Features
- Save student study preferences and exam details
- Add subjects with difficulty and priority ratings
- Generate a weekly timetable using a weighted scheduling algorithm
- Mark study sessions complete and track progress
- Get rule-based personalized study recommendations
- Data is stored locally in SQLite

## Run on a laptop / desktop

1. Install Python 3.10 or newer.
2. Open a terminal in this project folder.
3. Create and activate a virtual environment (recommended):
   - Windows: `py -m venv venv` then `venv\\Scripts\\activate`
   - macOS/Linux: `python3 -m venv venv` then `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Start the app: `python app.py`
6. Open `http://127.0.0.1:5000` in your browser.

## Run on Android using Termux
1. Install Termux from its official F-Droid/GitHub source.
2. In Termux run:
   `pkg update && pkg install python`
3. Move/extract this project into a folder accessible to Termux.
4. Enter the project folder and run:
   `pip install -r requirements.txt`
   `python app.py`
5. Open `http://127.0.0.1:5000` in your phone browser.

## Project structure
```
smart_student_timetable/
  app.py
  requirements.txt
  README.md
  templates/
    index.html
  static/
    style.css
    app.js
```

## Notes for your project report
The recommendation engine is currently rule-based, not a trained machine-learning model or external generative-AI service. In your viva, describe it accurately as an intelligent scheduling and recommendation system. You can later connect an AI API for natural-language tutoring or richer study recommendations.
