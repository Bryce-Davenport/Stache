from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime

app = Flask(__name__)

def get_demo_staches():
    # Temporary starter data; later this will come from a database
    return [
        {
            "slug": "camping",
            "name": "Camping",
            "description": "Tents, sleeping systems, cook kits, and other backcountry essentials.",
            "item_count": 18,
            "locations": "Gear Closet, Garage Shelf A",
            "tags": ["outdoors", "overnight", "3-season"],
            "created_at": "2025-01-03",
            "updated_at": "2025-02-02",
            "items": [
                {
                    "name": "1P Tent",
                    "category": "Shelter",
                    "location": "Gear Closet",
                    "condition": "Good",
                    "tags": ["3-season", "backpacking"]
                },
                {
                    "name": "Sleeping Pad",
                    "category": "Sleeping",
                    "location": "Gear Closet",
                    "condition": "Like New",
                    "tags": ["insulated"]
                },
                {
                    "name": "Stove Kit",
                    "category": "Cooking",
                    "location": "Garage Shelf A",
                    "condition": "Good",
                    "tags": ["canister", "lightweight"]
                },
            ],
        },
        {
            "slug": "electronics",
            "name": "Electronics",
            "description": "Cables, adapters, chargers, small devices, and troubleshooting gear.",
            "item_count": 32,
            "locations": "Desk Drawer, Tech Bin",
            "tags": ["tech", "everyday", "tools"],
            "created_at": "2025-01-10",
            "updated_at": "2025-01-25",
            "items": [
                {
                    "name": "USB-C Hub",
                    "category": "Adapters",
                    "location": "Desk Drawer",
                    "condition": "Good",
                    "tags": ["usb-c", "travel"]
                },
                {
                    "name": "Portable SSD",
                    "category": "Storage",
                    "location": "Tech Bin",
                    "condition": "Good",
                    "tags": ["backup"]
                },
            ],
        },
        {
            "slug": "books",
            "name": "Books",
            "description": "Physical books worth tracking – reference, tech, and favorite reads.",
            "item_count": 12,
            "locations": "Bookshelf, Nightstand",
            "tags": ["reading", "reference"],
            "created_at": "2024-12-15",
            "updated_at": "2025-01-05",
            "items": [
                {
                    "name": "Networking Fundamentals",
                    "category": "Reference",
                    "location": "Bookshelf",
                    "condition": "Good",
                    "tags": ["networking", "tech"]
                }
            ],
        },
    ]

# -- Development Only --
app.secret_key = "change_this_secret_key_later"
# ----- Helper: check if user is logged in -----
def is_logged_in():
    return "user" in session


@app.context_processor
def inject_user():
    return dict(
        logged_in=is_logged_in(),
        current_user=session.get("user")
    )

# -- Routes --
@app.route("/")
def home():
    if not is_logged_in():
        return redirect(url_for("login"))
    return render_template("home.html", active_page="home")

@app.route("/projects")
def projects():
    if not is_logged_in():
        return redirect(url_for("login"))

    # Temporary in-memory demo data (no database yet)
    demo_projects = [
        {
            "name": "Declutter Hard Drives",
            "status": "In Progress",
            "notes": "Sort loose SSDs and HDDs, label everything.",
            "tasks": [
                "[ ] Gather all loose drives",
                "[ ] Plug into USB dock and check health",
                "[ ] Label with capacity + purpose",
                "[ ] Update Stache entries for each drive",
            ],
        },
        {
            "name": "Dial In Camping Cook Kit",
            "status": "Planning",
            "notes": "Consolidate stoves, pots, and utensils into one bin.",
            "tasks": [
                "[ ] List all stoves and fuel types",
                "[ ] Decide on primary cook kit",
                "[ ] Create 'Camping Kitchen' stache",
                "[ ] Add items and locations",
            ],
        },
    ]

    return render_template(
        "projects.html",
        active_page="projects",
        projects=demo_projects
    )

@app.route("/staches")
def staches():
    if not is_logged_in():
        return redirect(url_for("login"))

    staches = get_demo_staches()

    return render_template(
        "staches.html",
        active_page="staches",
        staches=staches
    )

@app.route("/staches/<stache_slug>")
def stache_detail(stache_slug):
    if not is_logged_in():
        return redirect(url_for("login"))

    staches = get_demo_staches()
    stache = next((s for s in staches if s["slug"] == stache_slug), None)

    if stache is None:
        # For now, a simple 404; later we can make a nice error page
        return "Stache not found", 404

    return render_template(
        "stache_detail.html",
        active_page="staches",
        stache=stache
    )

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        # TEMPORARY: hardcoded user
        # Later this will check a database.
        if username == "bryce" and password == "stache123":
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
    app.run(debug=True, port=8000) # http:127.0.0..1:port
