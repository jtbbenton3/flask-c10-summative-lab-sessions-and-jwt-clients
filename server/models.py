# All database models live here.
from sqlalchemy import func
from .extensions import db, bcrypt

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

    notes = db.relationship(
        "Note",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan",
    )

    def set_password(self, raw_password: str):
        """Hash and store the password."""
        self.password_hash = bcrypt.generate_password_hash(raw_password).decode("utf-8")

    def check_password(self, raw_password: str) -> bool:
        """Compare a raw password to the stored hash."""
        return bcrypt.check_password_hash(self.password_hash, raw_password)

    def __repr__(self):
        return f"<User {self.id} {self.username}>"

class Note(db.Model):
    __tablename__ = "notes"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), server_onupdate=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    def __repr__(self):
        return f"<Note {self.id} title={self.title!r} user_id={self.user_id}>"