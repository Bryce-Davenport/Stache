# Stache – Windows Beta Setup Guide (All-In-One File)
Everything needed to run the Stache beta locally on Windows.

## 1. Install Required Software

### 1.1 Install Python 3
Download for Windows: https://www.python.org/downloads/windows/

Check “Add Python to PATH”, then verify:

```
python --version
```

### 1.2 Install Git
Download Git for Windows: https://git-scm.com/download/win

Verify:
```
git --version
```

## 2. Download Stache

```
git clone https://github.com/Bryce-Davenport/STACHE.git stache
cd stache
```

## 3. Create a Virtual Environment

```
python -m venv venv
venv\Scripts\activate
```

## 4. Install Dependencies

```
pip install -r requirements.txt
pip install waitress
```

## 5. Set the Secret Key

```
set STACHE_SECRET_KEY=some_random_secret
```

## 6. Run the App

```
waitress-serve --host=127.0.0.1 --port=8000 app:app
```

Go to: http://127.0.0.1:8000

## 7. Requirements.txt (copy into file)

```
Flask==3.0.0
Werkzeug==3.0.1
itsdangerous==2.1.2
click==8.1.7
Jinja2==3.1.3
MarkupSafe==2.1.3
blinker==1.7.0
Flask-SQLAlchemy==3.0.5
SQLAlchemy==2.0.25
passlib==1.7.4
waitress==2.1.2
```

## 8. Optional run_stache.bat

```
@echo off
cd %~dp0
call venv\Scripts\activate
set STACHE_SECRET_KEY=local_dev_secret
waitress-serve --host=127.0.0.1 --port=8000 app:app
```
