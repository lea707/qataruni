import pytest

from app import app as flask_app
from contextlib import contextmanager
from flask import appcontext_pushed, request
from types import SimpleNamespace


@pytest.fixture
def app():
    return flask_app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def request_context(app):
    # Provide a request context automatically for tests that access flask.request
    with app.test_request_context('/'):
        yield


