from datetime import datetime
from app import app
from models import db, User, Stache, Item, Project, ProjectTask

with app.app_context():
    db.drop_all()
    db.create_all()

    # User
    bryce = User(username="bryce", password_hash="dev-only")
    db.session.add(bryce)
    db.session.commit()

    # --- Stache: Camping ---
    camping = Stache(
        user_id=bryce.id,
        name="Camping",
        slug="camping",
        description="Tents, sleeping systems, cook kits, and other backcountry essentials.",
        locations="Gear Closet, Garage Shelf A",
        tags_csv="outdoors, overnight, 3-season",
    )
    db.session.add(camping)
    db.session.commit()

    db.session.add_all([
        Item(
            stache_id=camping.id,
            name="1P Tent",
            category="Shelter",
            location="Gear Closet",
            condition="Good",
            tags_csv="3-season, backpacking",
        ),
        Item(
            stache_id=camping.id,
            name="Sleeping Pad",
            category="Sleeping",
            location="Gear Closet",
            condition="Like New",
            tags_csv="insulated",
        ),
        Item(
            stache_id=camping.id,
            name="Stove Kit",
            category="Cooking",
            location="Garage Shelf A",
            condition="Good",
            tags_csv="canister, lightweight",
        ),
    ])

    # --- Stache: Electronics ---
    electronics = Stache(
        user_id=bryce.id,
        name="Electronics",
        slug="electronics",
        description="Cables, adapters, chargers, small devices, and troubleshooting gear.",
        locations="Desk Drawer, Tech Bin",
        tags_csv="tech, everyday, tools",
    )
    db.session.add(electronics)
    db.session.commit()

    db.session.add_all([
        Item(
            stache_id=electronics.id,
            name="USB-C Hub",
            category="Adapters",
            location="Desk Drawer",
            condition="Good",
            tags_csv="usb-c, travel",
        ),
        Item(
            stache_id=electronics.id,
            name="Portable SSD",
            category="Storage",
            location="Tech Bin",
            condition="Good",
            tags_csv="backup",
        ),
    ])

    # --- Stache: Books ---
    books = Stache(
        user_id=bryce.id,
        name="Books",
        slug="books",
        description="Physical books worth tracking – reference, tech, and favorite reads.",
        locations="Bookshelf, Nightstand",
        tags_csv="reading, reference",
    )
    db.session.add(books)
    db.session.commit()

    db.session.add(
        Item(
            stache_id=books.id,
            name="Networking Fundamentals",
            category="Reference",
            location="Bookshelf",
            condition="Good",
            tags_csv="networking, tech",
        )
    )

        # --- Project 1: Declutter Hard Drives ---
    declutter = Project(
        user_id=bryce.id,
        stache_id=electronics.id,  # link to Electronics stache
        name="Declutter Hard Drives",
        description="Sort loose SSDs and HDDs, label everything.",
        status="in-progress",  # matches filter values
    )
    db.session.add(declutter)
    db.session.commit()

    db.session.add_all([
        ProjectTask(project_id=declutter.id, description="Gather all loose drives"),
        ProjectTask(project_id=declutter.id, description="Plug into USB dock and check health"),
        ProjectTask(project_id=declutter.id, description="Label with capacity + purpose"),
        ProjectTask(project_id=declutter.id, description="Update Stache entries for each drive"),
    ])

    # --- Project 2: Dial In Camping Cook Kit ---
    camping_project = Project(
        user_id=bryce.id,
        stache_id=camping.id,  # link to Camping stache
        name="Dial In Camping Cook Kit",
        description="Consolidate stoves, pots, and utensils into one bin.",
        status="in-progress",  # also shows under “In progress”
    )
    db.session.add(camping_project)
    db.session.commit()

    db.session.add_all([
        ProjectTask(project_id=camping_project.id, description="List all stoves and fuel types"),
        ProjectTask(project_id=camping_project.id, description="Decide on primary cook kit"),
        ProjectTask(project_id=camping_project.id, description="Create 'Camping Kitchen' stache"),
        ProjectTask(project_id=camping_project.id, description="Add items and locations"),
    ])


    db.session.commit()
    print("Dev database seeded with demo data.")
