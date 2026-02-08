import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def user_factory(db):
    user_model = get_user_model()

    def create_user(username: str, password: str = "pass12345"):
        return user_model.objects.create_user(username=username, password=password, email=f"{username}@example.com")

    return create_user
