# server/app.py
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required, get_jwt_identity
)
from datetime import timedelta

db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)

    # Config
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = "dev-change-me"

    # JWT config
    app.config["JWT_SECRET_KEY"] = "dev-jwt-secret-change-me"
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=30)

    # Init extensions
    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    jwt.init_app(app)

    # Import models after extensions are ready
    from .models import User, Note

    @app.get("/health")
    def health():
        return {"ok": True}, 200

    @app.post("/signup")
    def signup():
        data = request.get_json() or {}
        username = (data.get("username") or "").strip()
        password = data.get("password") or ""

        if not username or not password:
            return {"error": "username and password are required"}, 400

        existing = User.query.filter_by(username=username).first()
        if existing:
            return {"error": "username already taken"}, 409

        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        return {"id": user.id, "username": user.username}, 201

    @app.post("/login")
    def login():
        data = request.get_json() or {}
        username = (data.get("username") or "").strip()
        password = data.get("password") or ""

        if not username or not password:
            return {"error": "username and password are required"}, 400

        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            return {"error": "invalid credentials"}, 401

        access_token = create_access_token(identity=str(user.id))
        return {"access_token": access_token}, 200

    @app.get("/me")
    @jwt_required()
    def me():
        uid = int(get_jwt_identity())
        user = User.query.get(uid)
        if not user:
            return {"error": "user not found"}, 404
        return {"id": user.id, "username": user.username}, 200

    # ---- Notes endpoints ----

    @app.post("/notes")
    @jwt_required()
    def create_note():
        data = request.get_json() or {}
        title = (data.get("title") or "").strip()
        content = (data.get("content") or "").strip()
        if not title or not content:
            return {"error": "title and content are required"}, 400

        uid = int(get_jwt_identity())
        note = Note(title=title, content=content, user_id=uid)
        db.session.add(note)
        db.session.commit()
        return {"id": note.id, "title": note.title, "content": note.content}, 201

    @app.get("/notes")
    @jwt_required()
    def list_notes():
        uid = int(get_jwt_identity())
        notes = Note.query.filter_by(user_id=uid).order_by(Note.id.desc()).all()
        return [{"id": n.id, "title": n.title, "content": n.content} for n in notes], 200

    return app

app = create_app()