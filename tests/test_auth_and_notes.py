# tests/test_auth_and_notes.py



def test_health_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.get_json() == {"ok": True}


def test_signup_login_me_flow(client, login_token, auth_headers):
    
    token = login_token("alice", "pw123")
    assert isinstance(token, str) and len(token) > 10

    
    r = client.get("/me", headers=auth_headers(token))
    assert r.status_code == 200
    me = r.get_json()
    assert me["username"] == "alice"
    assert isinstance(me["id"], int)


def test_signup_duplicate_username_conflict(signup):
    r1 = signup("dupe", "x")
    assert r1.status_code in (201, 409)

    r2 = signup("dupe", "y")
    assert r2.status_code == 409
    assert "already" in r2.get_json()["error"]


def test_notes_requires_auth(client):
    
    r_post = client.post("/notes", json={"title": "t", "content": "c"})
    assert r_post.status_code in (401, 422)

    r_get = client.get("/notes")
    assert r_get.status_code in (401, 422)


def test_notes_create_and_list(client, signup, login_token, auth_headers):
    
    signup("bob", "pw")
    token = login_token("bob", "pw")

    # create a note
    r = client.post(
        "/notes",
        json={"title": "First Note", "content": "hello"},
        headers=auth_headers(token),
    )
    assert r.status_code == 201
    note = r.get_json()
    assert note["title"] == "First Note"
    assert note["content"] == "hello"
    assert isinstance(note["id"], int)

    # list notes
    r = client.get("/notes", headers=auth_headers(token))
    assert r.status_code == 200
    notes = r.get_json()
    assert isinstance(notes, list)
    assert any(n["title"] == "First Note" and n["content"] == "hello" for n in notes)