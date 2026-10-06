from unittest.mock import AsyncMock, MagicMock

import pytest
from app.routes.routes import authentication
from app.exceptions.exceptions import InvalidCredentialsError


@pytest.mark.asyncio
async def test_login_invalid_credentials(monkeypatch):
    service = MagicMock()
    service.login = AsyncMock( side_effect=InvalidCredentialsError("Тест на аутентификацию провален"))
    monkeypatch.setattr("app.routes.routes.check_login_rate_limit", AsyncMock())
    with pytest.raises(Exception) as exc:
        await authentication( email="test@example.com", password="wrong", service=service)
    assert exc.value.status_code == 401
    service.login.assert_awaited_once()