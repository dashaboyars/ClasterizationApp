def test_get_or_create_systemUser_noExists(systemUser_service):
    user = systemUser_service.get_or_create_system_user()
    assert user is not None
    assert user.username == "system_user"
    assert user.email == "system_user@mail.ru"
    assert user.password_hash == "system_hash"

def test_get_or_create_systemUser_exists(systemUser_service):
    user = systemUser_service.get_or_create_system_user()
    new_user = systemUser_service.get_or_create_system_user()

    assert new_user is not None
    assert user.id == new_user.id
