def test_pages_require_login(client):
    for path in ("/", "/collection", "/profile", "/create"):
        response = client.get(path)
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]


def test_register_then_access_home(client):
    response = client.post("/register", data={"username": "newbie", "password": "secret123"})
    assert response.status_code == 302
    assert client.get("/").status_code == 200


def test_register_rejects_duplicate_case_insensitive(client, make_user):
    make_user("Alice")
    response = client.post("/register", data={"username": "alice", "password": "secret123"})
    assert response.status_code == 200
    assert "déjà pris" in response.get_data(as_text=True)


def test_register_rejects_unsafe_username_and_short_password(client):
    bad_name = client.post("/register", data={"username": "x');alert(1);//", "password": "secret123"})
    assert "ne peut contenir" in bad_name.get_data(as_text=True)
    short_pw = client.post("/register", data={"username": "valid", "password": "123"})
    assert "au moins" in short_pw.get_data(as_text=True)


def test_login_and_logout(client, make_user, login):
    make_user()
    assert login("alice", "wrong").status_code == 200
    assert login().status_code == 302
    assert client.get("/").status_code == 200
    client.get("/logout")
    assert client.get("/").status_code == 302
