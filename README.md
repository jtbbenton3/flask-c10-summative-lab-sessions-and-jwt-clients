# Productivity API (Flask + JWT)

Secure Flask backend with full authentication and a user-owned resource (**Notes**).  
Implements **JWT auth**, **CRUD** for notes, **route protection**, and **pagination**.

## Stack
- Flask 2.2.x, Flask-SQLAlchemy 3.x, Flask-Migrate 4.x
- Flask-Bcrypt for password hashing
- PyJWT for JSON Web Tokens
- Pytest for tests
- SQLite for local dev

## Quick Start
```bash
pipenv install
pipenv shell

# Migrations (optional if using db.create_all in dev)
flask --app server.app:create_app db init
flask --app server.app:create_app db migrate -m "init schema"
flask --app server.app:create_app db upgrade

# Seed demo data
python seed.py

# Run server
flask --app server.app:create_app run
# -> http://127.0.0.1:5000