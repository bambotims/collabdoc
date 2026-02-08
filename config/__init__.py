"""Django project package for CollabDoc."""

from .celery import app as celery_app

__all__ = ("celery_app",)
