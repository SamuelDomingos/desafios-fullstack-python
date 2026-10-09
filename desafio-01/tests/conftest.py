from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import pytest

from app.config import Settings


class FakeBrowser:
    @asynccontextmanager
    async def new_page(self) -> AsyncIterator[object]:
        yield object()


@pytest.fixture
def settings() -> Settings:
    return Settings(headless=True, max_concurrency=1)


@pytest.fixture
def fake_browser() -> FakeBrowser:
    return FakeBrowser()
