from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime
import re


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

def slugify(name: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "stache"

    slug = base
    counter = 2
    # If you ever want per-user uniqueness, also filter by user_id here.
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
                active_page="items"
            )

        # Create item
        new_item = Item(
            name=name,
            stache_id=int(stache_id),
            category=category,
            location=location,
            condition=condition,
            tags_csv=tags_csv,
        )

        db.session.add(new_item)
        db.session.commit()

        return redirect(url_for("items"))

    return render_template(
        "items_new.html",
        staches=staches,
        active_page="items"
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
