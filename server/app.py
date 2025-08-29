# server/app.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)

    # DB config
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = "dev-change-me"

    # init extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # import models 
    import server.models  

    @app.get("/health")
    def health():
        return {"ok": True}, 200

    return app


app = create_app()