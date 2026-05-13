def test_create_user(user_repo):
    new_user = user_repo.create_user("username", "email@mail.ru", "1234")
    assert new_user.username == "username"
    assert new_user.email == "email@mail.ru"

def test_get_by_username(user_repo):
    user = user_repo.create_user("username", "email@mail.ru", "1234")
    found_user = user_repo.get_by_username("username")
    assert user.id == found_user.id

def test_get_by_username_noExists(user_repo):
    found_user = user_repo.get_by_username("username")
    assert found_user is None