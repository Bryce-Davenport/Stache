# Stache – Linux Beta Setup Guide (All-In-One File)
Everything needed to run the Stache beta locally on a Linux machine.

---

## 1. Install Required Software

You’ll need **Python 3** and **Git**. Use your distro’s package manager.

### 1.1 Example for Ubuntu / Debian

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git
```

### 1.2 Verify installs

```bash
python3 --version
git --version
```

You should see Python 3.x and a Git version number.

---

## 2. Download Stache

Pick a folder where you keep projects, then:

```bash
git clone https://github.com/Bryce-Davenport/STACHE.git stache
cd stache
```

---

## 3. Create a Virtual Environment

Inside the `stache` folder:

```bash
python3 -m venv venv
source venv/bin/activate
```

Your prompt should now start with:

```bash
(venv)
```

---

## 4. Install Dependencies

Install everything from `requirements.txt`:

```bash
pip install -r requirements.txt
```

If `requirements.txt` does not exist yet, create it using the contents in **Section 9** below.

If you see no errors, you’re good.

---

## 5. Set the Secret Key

Set an environment variable for the Flask secret key:

```bash
export STACHE_SECRET_KEY="some_random_secret_value"
```

Example:

```bash
export STACHE_SECRET_KEY="48ca1acd982b4e3420050f3b920d0cb8f54e3f6b4adef"
```

(This is used to sign login sessions.)

---

## 6. Run Stache with Gunicorn

Still inside the project folder with the venv active:

```bash
gunicorn --bind 127.0.0.1:8000 app:app
```

If everything works, you’ll see logs like:

```text
[INFO] Starting gunicorn...
[INFO] Listening at: http://127.0.0.1:8000
```

Open your browser and go to:

```text
http://127.0.0.1:8000
```

The Stache app should load.

---

## 7. Stopping the App

Press:

```text
Ctrl + C
```

in the terminal running gunicorn.

---

## 8. Restarting Later

Any time you want to use Stache again:

```bash
cd path/to/stache
source venv/bin/activate
export STACHE_SECRET_KEY="some_random_secret_value"
gunicorn --bind 127.0.0.1:8000 app:app
```

---

## 9. Requirements (Full `requirements.txt` Contents)

Create a file named **`requirements.txt`** in the project root with the following contents:

```text
Flask==3.0.0
Werkzeug==3.0.1
itsdangerous==2.1.2
click==8.1.7
Jinja2==3.1.3
MarkupSafe==2.1.3
blinker==1.7.0

Flask-SQLAlchemy==3.0.5
SQLAlchemy==2.0.25

# For password hashing
passlib==1.7.4

# WSGI servers
gunicorn==21.2.0
waitress==2.1.2
```

Then install:

```bash
pip install -r requirements.txt
```

---

## 10. Logging In / Creating Accounts

Once the app is running:

1. Visit `http://127.0.0.1:8000`
2. Click **Create account**
3. Choose a username and password
4. Start using Stache

Each account’s data is isolated to that user.

---

## 11. Troubleshooting

### Missing packages
Run:

```bash
pip install -r requirements.txt
```

### Secret key issues
Make sure you exported `STACHE_SECRET_KEY` **in the same terminal** before running gunicorn.

### Port already in use
Use a different port:

```bash
gunicorn --bind 127.0.0.1:5000 app:app
```

Then visit: `http://127.0.0.1:5000`

---

You’re ready to beta-test Stache on Linux. 🎒
