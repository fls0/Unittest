import unittest
from unittest.mock import patch, AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas.users import UserCreateSchema

from src.database.models import User
from src.repository.users import (
    get_user_by_email,
    create_user,
    update_token,
)

class TestAsyncUser(unittest.IsolatedAsyncioTestCase):

    def setUp(self) -> None:
        self.session = AsyncMock(spec=AsyncSession)
        self.user = User(username="test_user", email="test_user@gmail.com", password="test1234")

    async def test_start_cache(self, mock_cache):
        self.mock_redis_cache = mock_cache
        self.assertIsInstance(self.mock_redis_cache)

    async def test_get_user_by_email(self):
        mocked_user = MagicMock()
        mocked_user.scalar_one_or_none.return_value = self.user
        self.session.execute.return_value = mocked_user

        user = await get_user_by_email(self.user.email, self.session)
        self.assertEqual(user.email, self.user.email)

    async def test_create_user(self):
        body = UserCreateSchema(username=self.user.username,
                                email=self.user.email,
                                password=self.user.password)

        user = await create_user(body, self.session)

        self.assertIsInstance(user, User)
        self.assertEqual(user.email, body.email)
        self.assertEqual(user.username, body.username)
        self.assertIn("https://www.gravatar.com/avatar/", user.avatar)

        self.session.add.assert_called_once_with(user)
        self.session.commit.assert_called_once()

    async def test_update_token(self):
        self.user.refresh_token = "test_token"
        await update_token(self.user, "test_token", self.session)

        self.session.commit.assert_called_once()
        self.assertEqual(self.user.refresh_token, "test_token")