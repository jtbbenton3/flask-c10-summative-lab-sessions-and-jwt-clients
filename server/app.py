# server/app.py
# Main Flask app factory + routes.

from flask import Flask, request, jsonify, g
from flask_migrate import Migrate
import os
import datetime
import jwt  

from .extensions import db, bcrypt
from .models import User, Note


def create_app(test_config=None):
    app = Flask(__name__)

    #Config
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///app.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret")  # used to sign JWTs
    app.config["JWT_ALGORITHM"] = "HS256"

    if test_config:
        app.config.update(test_config)

    #Init extensions
    db.init_app(app)
    bcrypt.init_app(app)
    Migrate(app, db)

    #JWT helpers
    def encode_token(user_id: int) -> str:
        """Create a JWT access token for the given user id.
        Note: PyJWT 2.x requires 'sub' to be a string.
        """
        now = datetime.datetime.now(datetime.timezone.utc)
        payload = {
            "sub": str(user_id), 
            "iat": int(now.timestamp()),
            "exp": int((now + datetime.timedelta(hours=6)).timestamp()),
        }
        return jwt.encode(payload, app.config["SECRET_KEY"], algorithm=app.config["JWT_ALGORITHM"])

    def decode_token(token: str):
        """Decode a JWT; returns payload dict or None on error."""
        try:
            return jwt.decode(token, app.config["SECRET_KEY"], algorithms=[app.config["JWT_ALGORITHM"]])
        except jwt.PyJWTError:
            return None

    def require_auth(fn):
        """Decorator to enforce Bearer JWT; sets g.current_user."""
        from functools import wraps

        @wraps(fn)
        def wrapper(*args, **kwargs):
            auth = request.headers.get("Authorization", "")
            if not auth.startswith("Bearer "):
                return jsonify({"error": "Missing or invalid Authorization header"}), 401
            token = auth.split(" ", 1)[1]
            data = decode_token(token)
            if not data:
                return jsonify({"error": "Invalid token"}), 401
            try:
                uid = int(data.get("sub"))  
            except (TypeError, ValueError):
                return jsonify({"error": "Invalid token subject"}), 401
            user = User.query.get(uid)
            if not user:
                return jsonify({"error": "User not found"}), 401
            g.current_user = user
            return fn(*args, **kwargs)

        return wrapper

    #Routes 
    @app.get("/health")
    def health():
        """Simple liveness endpoint for tests/monitoring."""
        return jsonify(ok=True), 200

    @app.post("/signup")
    def signup():
        """Create a new user with a unique username."""
        data = request.get_json() or {}
        username = (data.get("username") or "").strip()
        password = data.get("password") or ""

        if not username or not password:
            return jsonify({"error": "username and password required"}), 400

        if User.query.filter_by(username=username).first():
            return jsonify({"error": "username already exists"}), 409

        u = User(username=username)
        u.set_password(password)
        db.session.add(u)
        db.session.commit()

        return jsonify({"id": u.id, "username": u.username}), 201

    @app.post("/login")
    def login():
        """Verify credentials and return a JWT."""
        data = request.get_json() or {}
        username = (data.get("username") or "").strip()
        password = data.get("password") or ""

        if not username or not password:
            return jsonify({"error": "username and password required"}), 400

        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            return jsonify({"error": "invalid credentials"}), 401

        token = encode_token(user.id)
        return jsonify({"access_token": token}), 200

    @app.get("/me")
    @require_auth
    def me():
        """Return info for the current authenticated user."""
        u = g.current_user
        return jsonify({"id": u.id, "username": u.username}), 200

    #Notes CRUD
    @app.post("/notes")
    @require_auth
    def create_note():
        """Create a note for the current user."""
        data = request.get_json() or {}
        title = data.get("title")
        content = data.get("content")
        if not title or not content:
            return jsonify({"error": "title and content required"}), 400
        n = Note(title=title, content=content, user_id=g.current_user.id)
        db.session.add(n)
        db.session.commit()
        return jsonify({"id": n.id, "title": n.title, "content": n.content}), 201

    @app.get("/notes")
    @require_auth
    def list_notes():
        """List notes. If ?page is provided, return a pagination object; otherwise, return a simple list."""
        page = request.args.get("page", type=int)
        per_page = request.args.get("per_page", type=int, default=10)

        q = Note.query.filter_by(user_id=g.current_user.id).order_by(Note.id.asc())

        if page:
            p = q.paginate(page=page, per_page=per_page, error_out=False)
            return jsonify({
                "items": [{"id": n.id, "title": n.title, "content": n.content} for n in p.items],
                "page": p.page,
                "per_page": p.per_page,
                "pages": p.pages,
                "total": p.total,
            }), 200

        items = [{"id": n.id, "title": n.title, "content": n.content} for n in q.all()]
        return jsonify(items), 200

    @app.patch("/notes/<int:note_id>")
    @require_auth
    def update_note(note_id: int):
        """Update a note you own."""
        n = Note.query.get_or_404(note_id)
        if n.user_id != g.current_user.id:
            return jsonify({"error": "forbidden"}), 403
        data = request.get_json() or {}
        if "title" in data:
            n.title = data["title"]
        if "content" in data:
            n.content = data["content"]
        db.session.commit()
        return jsonify({"id": n.id, "title": n.title, "content": n.content}), 200

    @app.delete("/notes/<int:note_id>")
    @require_auth
    def delete_note(note_id: int):
        """Delete a note you own."""
        n = Note.query.get_or_404(note_id)
        if n.user_id != g.current_user.id:
            return jsonify({"error": "forbidden"}), 403
        db.session.delete(n)
        db.session.commit()
        return "", 204

    
    with app.app_context():
        db.create_all()

    return app