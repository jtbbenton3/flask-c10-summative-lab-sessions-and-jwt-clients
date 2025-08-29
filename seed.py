# Root-level seed script used in your commands.
from faker import Faker
from server.app import create_app
from server.extensions import db
from server.models import User, Note

def run():
    app = create_app()
    with app.app_context():
        print("Recreating database...")
        db.drop_all()
        db.create_all()

        fake = Faker()

        usernames = ["alice", "bob", "charlie", "diana"]
        users = []
        for name in usernames:
            u = User(username=name)
            u.set_password("password")  
            db.session.add(u)
            users.append(u)
        db.session.commit()

        for u in users:
            for _ in range(3):
                n = Note(
                    title=fake.sentence(nb_words=3),
                    content=fake.paragraph(nb_sentences=2),
                    user_id=u.id,
                )
                db.session.add(n)
        db.session.commit()

        print(f"Seeded {len(users)} users and {Note.query.count()} notes.")

if __name__ == "__main__":
    run()