from flask import Flask, render_template, request, redirect, url_for, session, abort
from datetime import datetime
import re
import os

from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Stache, Item, Project, ProjectTask

app = Flask(__name__)

# --- Sessions / security ---
app.config["SECRET_KEY"] = os.environ.get("STACHE_SECRET_KEY", "dev-secret-change-me")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
# app.config["SESSION_COOKIE_SECURE"] = True  # enable later when using HTTPS

# SQLite now, Postgres later
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///stache.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# *** IMPORTANT: register this Flask app with SQLAlchemy ***
db.init_app(app)


# ----- Helpers -----
def is_logged_in():
    """Return True if a user is logged in based on the session."""
    return "user_id" in session


def get_current_user():
    """Return the current User object from the database, or None."""
    user_id = session.get("user_id")
    if not user_id:
        return None
    return User.query.get(user_id)


@app.context_processor
def inject_user():
    """Inject login state and current user info into all templates."""
    return dict(
        logged_in=is_logged_in(),
        current_username=session.get("username"),  # for display in navbar
    )


def slugify(name: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "stache"

    slug = base
    counter = 2
    
    while Stache.query.filter_by(slug=slug).first() is not None:
        slug = f"{base}-{counter}"
        counter += 1

    return slug


# ----- Routes -----
@app.route("/")
def home():
    if not is_logged_in():
        return redirect(url_for("login"))
    return render_template("home.html", active_page="home")


# ---------- Projects ----------
@app.route("/projects")
def projects():
    if not is_logged_in():
        return redirect(url_for("login"))

    user = get_current_user()
    if not user:
        return redirect(url_for("login"))

    status_filter = request.args.get("status", "all")

    query = Project.query.filter_by(user_id=user.id)

    if status_filter == "in-progress":
        query = query.filter(Project.status == "in-progress")
    elif status_filter == "completed":
        query = query.filter(Project.status == "completed")
    elif status_filter == "planning":
        query = query.filter(Project.status == "planning")

    projects = query.order_by(Project.created_at.desc()).all()

    return render_template(
        "projects.html",
        active_page="projects",
        projects=projects,
        status_filter=status_filter,
    )


@app.route("/projects/new", methods=["GET", "POST"])
def new_project():
    if not is_logged_in():
        return redirect(url_for("login"))

    user = get_current_user()
    if not user:
        return redirect(url_for("login"))

    staches = (
        Stache.query
        .filter_by(user_id=user.id)
        .order_by(Stache.name.asc())
        .all()
    )

    error = None

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        stache_id = request.form.get("stache_id")
        status = request.form.get("status") or "in-progress"

        if not name:
            error = "Project name is required."
        elif not stache_id:
            error = "You must select a Stache for this project."

        if error:
            return render_template(
                "project_new.html",
                active_page="projects",
                staches=staches,
                error=error,
            )

        project = Project(
            user_id=user.id,
            stache_id=int(stache_id),
            name=name,
            description=description,
            status=status,
        )
        db.session.add(project)
        db.session.commit()

        return redirect(url_for("project_detail", project_id=project.id))

    return render_template(
        "project_new.html",
        active_page="projects",
        staches=staches,
        error=error,
    )


@app.route("/projects/<int:project_id>")
def project_detail(project_id):
    if not is_logged_in():
        return redirect(url_for("login"))

    user = get_current_user()
    if not user:
        return redirect(url_for("login"))

    project = (
        Project.query
        .filter_by(id=project_id, user_id=user.id)
        .first_or_404()
    )

    tasks = (
        ProjectTask.query
        .filter_by(project_id=project.id)
        .order_by(ProjectTask.created_at.asc())
        .all()
    )

    items = (
        Item.query
        .filter_by(stache_id=project.stache_id)
        .order_by(Item.name.asc())
        .all()
    )

    return render_template(
        "project_detail.html",
        active_page="projects",
        project=project,
        tasks=tasks,
        items=items,
    )

@app.route("/projects/<int:project_id>/edit", methods=["GET", "POST"])
def edit_project(project_id):
    if not is_logged_in():
        return redirect(url_for("login"))

    user = get_current_user()
    if not user:
        return redirect(url_for("login"))

    # Make sure this project belongs to the logged-in user
    project = (
        Project.query
        .filter_by(id=project_id, user_id=user.id)
        .first_or_404()
    )

    # Staches for dropdown 
    staches = (
        Stache.query
        .filter_by(user_id=user.id)
        .order_by(Stache.name.asc())
        .all()
    )

    error = None

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        stache_id = request.form.get("stache_id")
        status = request.form.get("status") or project.status

        if not name:
            error = "Project name is required."
        elif not stache_id:
            error = "You must select a Stache for this project."

        if not error:
            project.name = name
            project.description = description
            project.stache_id = int(stache_id)
            project.status = status
            db.session.commit()
            return redirect(url_for("project_detail", project_id=project.id))

    return render_template(
        "project_edit.html",
        active_page="projects",
        project=project,
        staches=staches,
        error=error,
    )


@app.route("/projects/<int:project_id>/tasks", methods=["POST"])
def add_project_task(project_id):
    if not is_logged_in():
        return redirect(url_for("login"))

    user = get_current_user()
    if not user:
        return redirect(url_for("login"))

    project = (
        Project.query
        .filter_by(id=project_id, user_id=user.id)
        .first_or_404()
    )

    title = request.form.get("title", "").strip()
    item_id = request.form.get("item_id")

    if not title:
        # If no title, just reload project page
        return redirect(url_for("project_detail", project_id=project.id))

    task = ProjectTask(
        project_id=project.id,
        title=title,
        item_id=int(item_id) if item_id else None,
    )
    db.session.add(task)
    db.session.commit()

    return redirect(url_for("project_detail", project_id=project.id))

@app.route("/projects/<int:project_id>/tasks/<int:task_id>/toggle", methods=["POST"])
def toggle_project_task(project_id, task_id):
    if not is_logged_in():
        return redirect(url_for("login"))

    user = get_current_user()
    if not user:
        return redirect(url_for("login"))

    # Make sure this task belongs to a project owned by the current user
    task = (
        ProjectTask.query
        .join(Project)
        .filter(
            ProjectTask.id == task_id,
            ProjectTask.project_id == project_id,
            Project.user_id == user.id,
        )
        .first_or_404()
    )

    # Toggle completion flag 
    task.completed = not bool(task.completed)
    db.session.commit()

    return redirect(url_for("project_detail", project_id=project_id))


@app.route("/projects/<int:project_id>/status", methods=["POST"])
def update_project_status(project_id):
    if not is_logged_in():
        return redirect(url_for("login"))

    user = get_current_user()
    if not user:
        return redirect(url_for("login"))

    project = (
        Project.query
        .filter_by(id=project_id, user_id=user.id)
        .first_or_404()
    )

    new_status = request.form.get("status", "").strip()
    if new_status in ["in-progress", "completed"]:
        project.status = new_status
        db.session.commit()

    return redirect(url_for("project_detail", project_id=project.id))


@app.route("/projects/<int:project_id>/delete", methods=["POST"])
def delete_project(project_id):
    if not is_logged_in():
        return redirect(url_for("login"))

    user = get_current_user()
    if not user:
        return redirect(url_for("login"))

    project = (
        Project.query
        .filter_by(id=project_id, user_id=user.id)
        .first_or_404()
    )

    # Remove tasks first
    for task in project.tasks:
        db.session.delete(task)

    db.session.delete(project)
    db.session.commit()

    return redirect(url_for("projects"))


# ---------- Staches ----------
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
        staches=staches,
    )


@app.route("/staches/new", methods=["GET", "POST"])
def new_stache():
    if not is_logged_in():
        return redirect(url_for("login"))

    user = get_current_user()
    if not user:
        return redirect(url_for("login"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        locations = request.form.get("locations", "").strip()
        tags = request.form.get("tags", "").strip()

        if not name:
            error = "Stache name is required."
            return render_template(
                "staches_new.html",
                error=error,
                active_page="staches",
            )

        tags_csv = ",".join([t.strip() for t in tags.split(",") if t.strip()])
        slug = slugify(name)

        stache = Stache(
            user_id=user.id,
            name=name,
            slug=slug,
            description=description,
            locations=locations,
            tags_csv=tags_csv,
        )

        db.session.add(stache)
        db.session.commit()

        return redirect(url_for("stache_detail", stache_slug=stache.slug))

    # GET → blank form
    return render_template("staches_new.html", active_page="staches")


@app.route("/staches/<stache_slug>")
def stache_detail(stache_slug):
    if not is_logged_in():
        return redirect(url_for("login"))

    user = get_current_user()
    if not user:
        return redirect(url_for("login"))

    # Look up this stache by slug for the current user
    stache = (
        Stache.query
        .filter_by(user_id=user.id, slug=stache_slug)
        .first_or_404()
    )

    # All items that belong to this stache
    items = (
        Item.query
        .filter_by(stache_id=stache.id)
        .order_by(Item.name.asc())
        .all()
    )

    return render_template(
        "stache_detail.html",
        active_page="staches",
        stache=stache,
        items=items,
    )


@app.route("/staches/<stache_slug>/edit", methods=["GET", "POST"])
def edit_stache(stache_slug):
    if not is_logged_in():
        return redirect(url_for("login"))

    user = get_current_user()
    if not user:
        return redirect(url_for("login"))

    # Make sure this stache belongs to the logged-in user
    stache = (
        Stache.query
        .filter_by(user_id=user.id, slug=stache_slug)
        .first_or_404()
    )

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        locations = request.form.get("locations", "").strip()
        tags = request.form.get("tags", "").strip()

        if not name:
            error = "Stache name is required."
            tags_string = tags
            return render_template(
                "stache_edit.html",
                stache=stache,
                tags_string=tags_string,
                error=error,
                active_page="staches",
            )

        # Update fields (keep slug stable so URLs don’t change)
        stache.name = name
        stache.description = description
        stache.locations = locations
        stache.tags_csv = ",".join([t.strip() for t in tags.split(",") if t.strip()])

        db.session.commit()

        return redirect(url_for("stache_detail", stache_slug=stache.slug))

    # GET: pre-fill tags for the form
    tags_string = ", ".join(stache.tags) if getattr(stache, "tags", None) else ""

    return render_template(
        "stache_edit.html",
        stache=stache,
        tags_string=tags_string,
        active_page="staches",
    )


@app.route("/staches/<stache_slug>/delete", methods=["POST"])
def delete_stache(stache_slug):
    if not is_logged_in():
        return redirect(url_for("login"))

    user = get_current_user()
    if not user:
        return redirect(url_for("login"))

    # Make sure the stache belongs to this user
    stache = (
        Stache.query
        .filter_by(user_id=user.id, slug=stache_slug)
        .first_or_404()
    )

    # Delete all items in this stache (safe even if there are none)
    items = Item.query.filter_by(stache_id=stache.id).all()
    for item in items:
        db.session.delete(item)

    # Delete the stache itself
    db.session.delete(stache)
    db.session.commit()

    return redirect(url_for("staches"))


# ---------- Items ----------
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


@app.route("/items/new", methods=["GET", "POST"])
def new_item():
    if not is_logged_in():
        return redirect(url_for("login"))

    user = get_current_user()
    if not user:
        return redirect(url_for("login"))

    # Load staches for dropdown
    staches = Stache.query.filter_by(user_id=user.id).all()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        stache_id = request.form.get("stache_id")
        category = request.form.get("category", "").strip()
        location = request.form.get("location", "").strip()
        condition = request.form.get("condition", "").strip()
        tags = request.form.get("tags", "").strip()

        # Convert comma-separated tags → CSV for storage
        tags_csv = ",".join([t.strip() for t in tags.split(",") if t.strip()])

        # Very basic validation for now
        if not name or not stache_id:
            error = "Item name and stache are required."
            return render_template(
                "items_new.html",
                staches=staches,
                error=error,
                active_page="items",
            )

        # Create item
        new_item_obj = Item(
            name=name,
            stache_id=int(stache_id),
            category=category,
            location=location,
            condition=condition,
            tags_csv=tags_csv,
        )

        db.session.add(new_item_obj)
        db.session.commit()

        return redirect(url_for("items"))

    return render_template(
        "items_new.html",
        staches=staches,
        active_page="items",
    )


@app.route("/items/<int:item_id>")
def item_detail(item_id):
    if not is_logged_in():
        return redirect(url_for("login"))

    user = get_current_user()
    if not user:
        return redirect(url_for("login"))

    # Only allow access to items that belong to this user's staches
    item = (
        Item.query
        .join(Stache)
        .filter(Item.id == item_id, Stache.user_id == user.id)
        .first_or_404()
    )

    return render_template(
        "items_detail.html",
        item=item,
        active_page="items",
    )


@app.route("/items/<int:item_id>/delete", methods=["POST"])
def delete_item(item_id):
    if not is_logged_in():
        return redirect(url_for("login"))

    user = get_current_user()
    if not user:
        return redirect(url_for("login"))

    item = (
        Item.query
        .join(Stache)
        .filter(Item.id == item_id, Stache.user_id == user.id)
        .first_or_404()
    )

    db.session.delete(item)
    db.session.commit()

    return redirect(url_for("items"))


@app.route("/items/<int:item_id>/edit", methods=["GET", "POST"])
def edit_item(item_id):
    if not is_logged_in():
        return redirect(url_for("login"))

    user = get_current_user()
    if not user:
        return redirect(url_for("login"))

    # Make sure this item belongs to a stache owned by the current user
    item = (
        Item.query
        .join(Stache)
        .filter(Item.id == item_id, Stache.user_id == user.id)
        .first_or_404()
    )

    # Staches for dropdown
    staches = Stache.query.filter_by(user_id=user.id).all()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        stache_id = request.form.get("stache_id")
        category = request.form.get("category", "").strip()
        location = request.form.get("location", "").strip()
        condition = request.form.get("condition", "").strip()
        tags = request.form.get("tags", "").strip()

        tags_csv = ",".join([t.strip() for t in tags.split(",") if t.strip()])

        if not name or not stache_id:
            error = "Item name and stache are required."
            return render_template(
                "items_edit.html",
                item=item,
                staches=staches,
                tags_string=tags,
                error=error,
                active_page="items",
            )

        # Apply updates
        item.name = name
        item.stache_id = int(stache_id)
        item.category = category
        item.location = location
        item.condition = condition
        item.tags_csv = tags_csv

        db.session.commit()

        return redirect(url_for("item_detail", item_id=item.id))

    # GET: prefill tags as a comma-separated string
    tags_string = ", ".join(item.tags) if getattr(item, "tags", None) else ""

    return render_template(
        "items_edit.html",
        item=item,
        staches=staches,
        tags_string=tags_string,
        active_page="items",
    )

@app.route("/register", methods=["GET", "POST"])
def register():
    # If already logged in, don't show register page
    if is_logged_in():
        return redirect(url_for("home"))

    error = None

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        # Basic validation
        if not username or not password or not confirm:
            error = "Please fill in all fields."
        elif len(username) < 3 or len(username) > 32:
            error = "Username must be between 3 and 32 characters."
        elif not re.match(r"^[A-Za-z0-9_]+$", username):
            error = "Username can only contain letters, numbers, and underscores."
        elif len(password) < 8:
            error = "Password must be at least 8 characters long."
        elif password != confirm:
            error = "Passwords do not match."
        else:
            # Check if username is already taken
            existing = User.query.filter_by(username=username).first()
            if existing:
                error = "That username is already taken."
            else:
                # Create the new user
                user = User(
                    username=username,
                    password_hash=generate_password_hash(password),
                )
                db.session.add(user)
                db.session.commit()

                # Log them in immediately
                session["user_id"] = user.id
                session["username"] = user.username

                return redirect(url_for("home"))

    return render_template("register.html", error=error)

@app.route("/account/profile")
def account_profile():
    if not is_logged_in():
        return redirect(url_for("login"))

    user = get_current_user()
    if not user:
        return redirect(url_for("login"))

    # Basic stats for this user
    stache_count = Stache.query.filter_by(user_id=user.id).count()
    project_count = Project.query.filter_by(user_id=user.id).count()
    item_count = (
        Item.query
        .join(Stache)
        .filter(Stache.user_id == user.id)
        .count()
    )

    return render_template(
        "account_profile.html",
        active_page="account",
        user=user,
        stache_count=stache_count,
        project_count=project_count,
        item_count=item_count,
    )

@app.route("/account/settings", methods=["GET", "POST"])
def account_settings():
    if not is_logged_in():
        return redirect(url_for("login"))

    user = get_current_user()
    if not user:
        return redirect(url_for("login"))

    error = None
    success = None

    if request.method == "POST":
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        # Basic validation
        if not current_password or not new_password or not confirm_password:
            error = "Please fill in all fields."
        elif not check_password_hash(user.password_hash, current_password):
            error = "Current password is incorrect."
        elif len(new_password) < 8:
            error = "New password must be at least 8 characters long."
        elif new_password != confirm_password:
            error = "New password and confirmation do not match."
        else:
            user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            success = "Your password has been updated."

    return render_template(
        "account_settings.html",
        active_page="account",
        user=user,
        error=error,
        success=success,
    )

@app.route("/account/delete", methods=["GET", "POST"])
def account_delete():
    if not is_logged_in():
        return redirect(url_for("login"))

    user = get_current_user()
    if not user:
        return redirect(url_for("login"))

    error = None

    if request.method == "POST":
        password = request.form.get("password", "")

        # Verify password
        if not check_password_hash(user.password_hash, password):
            error = "Password is incorrect."
        else:
            # --- Delete ALL data associated with this user ---

            # 1) Delete all project tasks for this user's projects
            projects = Project.query.filter_by(user_id=user.id).all()
            for project in projects:
                for task in project.tasks:
                    db.session.delete(task)
                db.session.delete(project)

            # 2) Delete all items + staches
            staches = Stache.query.filter_by(user_id=user.id).all()
            for stache in staches:
                items = Item.query.filter_by(stache_id=stache.id).all()
                for item in items:
                    db.session.delete(item)
                db.session.delete(stache)

            # 3) Finally, delete the user
            db.session.delete(user)
            db.session.commit()

            # 4) Clear session and send them to login
            session.clear()
            return redirect(url_for("login"))

    return render_template(
        "account_delete.html",
        active_page="account",
        error=error,
    )


# ---------- Auth ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            error = "Please enter both username and password."
        else:
            # Look up user by username
            user = User.query.filter_by(username=username).first()

            # Generic error message on failure
            if not user or not user.password_hash:
                error = "Invalid username or password."
            else:
                # Verify the password against the stored hash
                if check_password_hash(user.password_hash, password):
                    # Success: store identity in the session
                    session["user_id"] = user.id
                    session["username"] = user.username
                    return redirect(url_for("home"))
                else:
                    error = "Invalid username or password."

    # GET request or failed POST
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("username", None)
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
