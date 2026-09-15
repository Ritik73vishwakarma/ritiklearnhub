# Ritik LearnHub

Full-stack Flask + SQLite college learning portal.

## Features
- Ritik branding
- Login/logout
- Admin dashboard
- Student users with generated unique passwords
- Course add/delete
- YouTube course videos
- AI Assistant using OpenAI Responses API
- SQLite database
- Responsive frontend

## Run on Windows

### 1. Create/activate virtual environment (recommended)
```powershell
python -m venv .venv
.venv\Scripts\activate
```

### 2. Install packages
```powershell
pip install -r requirements.txt
```

### 3. Set API key
PowerShell:
```powershell
$env:OPENAI_API_KEY="YOUR_API_KEY"
$env:FLASK_SECRET_KEY="make-a-long-random-secret"
```

Optional model:
```powershell
$env:OPENAI_MODEL="gpt-5.6-luna"
```

### 4. Start
```powershell
python app.py
```

Open:
http://127.0.0.1:5000

## First admin login
Username: ritik
Password: Ritik@1234

For production, change the admin password and Flask secret before deployment.

## How to create students
Login as ritik -> Users -> enter username -> Create User.
The app generates a random password and shows it in the success message. Give that password to the student securely.

## How to add courses
Login as ritik -> Courses -> add title, description and YouTube URL.

The database file `learnhub.db` is created automatically on first run.
