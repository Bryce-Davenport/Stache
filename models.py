# models.py
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    # For now we'll store a placeholder; later you can store a real hash
    password_hash = db.Column(db.String(255), nullable=False, default="dev-only")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Stache(db.Model):
    __tablename__ = "staches"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    name = db.Column(db.String(120), nullable=False)
    slug = db.Column(db.String(120), nullable=False, unique=True)
    description = db.Column(db.Text)
    locations = db.Column(db.String(255))
    tags_csv = db.Column(db.String(255)) 

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    user = db.relationship("User", backref=db.backref("staches", lazy=True))
    items = db.relationship("Item", backref="stache", lazy=True)

    @property
    def tags(self):
        if not self.tags_csv:
            return []
        return [t.strip() for t in self.tags_csv.split(",")]

    @property
    def item_count(self):
        return len(self.items)


class Item(db.Model):
    __tablename__ = "items"

    id = db.Column(db.Integer, primary_key=True)
    stache_id = db.Column(db.Integer, db.ForeignKey("staches.id"), nullable=False)

    name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(80))
    location = db.Column(db.String(120))
    condition = db.Column(db.String(80))
    tags_csv = db.Column(db.String(255))
    notes = db.Column(db.Text)

    @property
    def tags(self):
        if not self.tags_csv:
            return []
        return [t.strip() for t in self.tags_csv.split(",")]


class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)

    # mark as real foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    stache_id = db.Column(db.Integer, db.ForeignKey("staches.id"), nullable=False)

    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default="in-progress")  # 'in-progress' or 'completed'

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # relationships
    user = db.relationship("User", backref="projects")
    stache = db.relationship("Stache", backref="projects")

    tasks = db.relationship(
        "ProjectTask",
        backref="project",
        cascade="all, delete-orphan",
    )


class ProjectTask(db.Model):
    __tablename__ = "project_tasks"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)

    # correct table name here:
    item_id = db.Column(db.Integer, db.ForeignKey("items.id"), nullable=True)

    description = db.Column(db.String(255), nullable=False)
    completed = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    item = db.relationship("Item", backref="project_tasks")
