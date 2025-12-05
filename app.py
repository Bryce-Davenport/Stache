from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime

from models import db, User, Stache, Item, Project, ProjectTask

app = Flask(__name__)

# SQLite now, Postgres later
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///stache.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# -- Development Only --
app.secret_key = "change_this_secret_key_later"

# Initialize SQLAlchemy with this app
db.init_app(app)


# ----- Helpers -----
def is_logged_in():
    """Return True if a user is logged in based on the session."""
    return "user" in session


def get_current_user():
    """Return the current User object from the database, or None."""
    username = session.get("user")
    if not username:
        return None
    return User.query.filter_by(username=username).first()


@app.context_processor
def inject_user():
    """Inject login state and current user into all templates."""
    return dict(
        logged_in=is_logged_in(),
        current_user=session.get("user")
    )


# ----- Routes -----
@app.route("/")
def home():
    if not is_logged_in():
        return redirect(url_for("login"))
    return render_template("home.html", active_page="home")


@app.route("/projects")
def projects():
    if not is_logged_in():
        return redirect(url_for("login"))

    user = get_current_user()
    if not user:
        return redirect(url_for("login"))

    # Load projects from the database for the logged-in user
    projects = Project.query.filter_by(user_id=user.id).all()

    return render_template(
        "projects.html",
        active_page="projects",
        projects=projects
    )


@app.route("/staches")
def staches():
    if not is_logged_in():
        return redirect(url_for("login"))

    user = get_current_user()
    if not user:
        return redirect(url_for("login"))

    # Load staches from the database for this user
    staches = Stache.query.filter_by(user_id=user.id).all()

    return render_template(
        "staches.html",
        active_page="staches",
        staches=staches
    )


@app.route("/staches/<stache_slug>")
def stache_detail(stache_slug):
    if not is_logged_in():
        return redirect(url_for("login"))

    user = get_current_user()
    if not user:
        return redirect(url_for("login"))

    # Look up this stache by slug for the current user
    stache = Stache.query.filter_by(user_id=user.id, slug=stache_slug).first()

    if stache is None:
        # For now, a simple 404; later we can make a nice error page
        return "Stache not found", 404

    return render_template(
        "stache_detail.html",
        active_page="staches",
        stache=stache
    )

@app.route("/items")
def items():
    if not is_logged_in():
        return redirect(url_for("login"))

    user = get_current_user()
    if not user:
        return redirect(url_for("login"))

    # All items belonging to this user's staches
    items = (
        Item.query
        .join(Stache)
        .filter(Stache.user_id == user.id)
        .all()
    )

    return render_template(
        "items.html",
        active_page="items",
        items=items,
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        # TEMPORARY: hardcoded credentials, but user row is stored in DB
        # Later this will check a database-stored password hash.
        if username == "bryce" and password == "stache123":
            # Ensure a matching User row exists in the database
            user = User.query.filter_by(username=username).first()
            if not user:
                user = User(username=username, password_hash="dev-only")
                db.session.add(user)
                db.session.commit()

            session["user"] = username
            return redirect(url_for("home"))
        else:
            error = "Invalid username or password."

    # GET request or failed POST
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))


if __name__ == "__main__":
    # Requires models.py + seed_dev.py already run to create stache.db
    app.run(debug=True, port=8000)  # http:127.0.0.1:8000
