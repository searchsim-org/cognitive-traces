from app.db.repositories.users import upsert_by_github_id


def test_upsert_creates_then_updates(db_session):
    claims = {"github_id": 42, "github_login": "ada", "name": "Ada", "email": "a@x", "avatar_url": "http://a"}
    u1 = upsert_by_github_id(db_session, claims)
    db_session.commit()
    assert u1.github_id == 42
    assert u1.github_login == "ada"

    claims2 = {**claims, "name": "Ada L.", "avatar_url": "http://b"}
    u2 = upsert_by_github_id(db_session, claims2)
    db_session.commit()

    assert u1.id == u2.id
    assert u2.name == "Ada L."
    assert u2.avatar_url == "http://b"
