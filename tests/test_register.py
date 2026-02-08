import pytest
from django.contrib.auth import get_user_model


User = get_user_model()


@pytest.mark.django_db
def test_register_creates_user_and_logs_in(api_client):
    response = api_client.post(
        "/api/auth/register",
        {
            "username": "new_user",
            "email": "new_user@example.com",
            "password": "pass12345",
            "password_confirm": "pass12345",
        },
        format="json",
    )

    assert response.status_code == 201
    assert User.objects.filter(username="new_user").exists()

    me_response = api_client.get("/api/auth/me")
    assert me_response.status_code == 200
    assert me_response.data["username"] == "new_user"


@pytest.mark.django_db
def test_register_rejects_duplicate_username(api_client, user_factory):
    user_factory("existing")
    response = api_client.post(
        "/api/auth/register",
        {
            "username": "existing",
            "email": "another@example.com",
            "password": "pass12345",
            "password_confirm": "pass12345",
        },
        format="json",
    )

    assert response.status_code == 400
    assert "username" in response.data
