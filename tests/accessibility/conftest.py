"""Pytest conftest for accessibility tests with Playwright."""

import os

import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--base-url",
        action="store",
        default=os.environ.get("BASE_URL", "http://localhost:8000"),
        help="Base URL of the running application",
    )


@pytest.fixture(scope="session")
def base_url(request):
    return request.config.getoption("--base-url")
