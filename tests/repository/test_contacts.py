import unittest
from datetime import date, timedelta
from unittest.mock import MagicMock, AsyncMock, Mock

from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Contact, User
from src.schemas.contacts import ContactCreateSchema, ContactUpdateSchema
from src.repository.contacts import (
    create_contact,
    get_contacts,
    get_contact,
    update_contact,
    delete_contact,
    search_contacts,
    get_birthdays
)


class TestAsyncTodo(unittest.IsolatedAsyncioTestCase):

    def setUp(self) -> None:
        self.user = User(id=1, username='test_user', password="qwerty", confirmed=True)
        self.session = AsyncMock(spec=AsyncSession)

    async def test_get_contacts(self):
        limit = 10
        offset = 0
        contacts = [
            Contact(id=1,
                    first_name='test1',
                    last_name='test1',
                    email='test1@ua.ua',
                    phone_number='+380123456789',
                    user=self.user),
            Contact(id=2,
                    first_name='test2',
                    last_name='test2',
                    email='test2@ua.ua',
                    phone_number='+380123456789',
                    user=self.user)
        ]
        mocked_contacts = MagicMock()
        mocked_contacts.scalars.return_value.all.return_value = contacts
        self.session.execute.return_value = mocked_contacts
        result = await get_contacts(limit, offset, self.session, self.user)
        self.assertEqual(result, contacts)

    async def test_get_contact(self):
        contact = Contact(id=1,
                          first_name='test1',
                          last_name='test1',
                          email='test1@ya.ua',
                          phone_number='+380123456789',
                          user=self.user)

        mocked_contact = MagicMock()
        mocked_contact.scalar_one_or_none.return_value = contact
        self.session.execute.return_value = mocked_contact
        result = await get_contact(contact.id, self.session, self.user)

        self.assertEqual(result, contact)

    async def test_create_contact(self):
        body = ContactCreateSchema(first_name='test1',
                                   last_name='test1',
                                   email='test1@ya.ua',
                                   phone_number='+380123456789')
        result = await create_contact(body, self.session, self.user)

        self.session.commit.assert_called_once()
        self.assertIsInstance(result, Contact)
        self.assertEqual(result.first_name, body.first_name)
        self.assertEqual(result.last_name, body.last_name)
        self.assertEqual(result.email, body.email)
        self.assertEqual(result.phone_number, body.phone_number)

    async def test_update_contact(self):
        body = ContactUpdateSchema(first_name='test_updated',
                                   last_name='test_updated',
                                   email='test_updated@ya.ua',
                                   phone_number='+380987654321')
        mocked_contact = MagicMock()
        mocked_contact.scalar_one_or_none.return_value = Contact(id=1, **body.model_dump(exclude_unset=True),
                                                                 user=self.user)
        self.session.execute.return_value = mocked_contact
        result = await update_contact(1, body, self.session, self.user)

        self.session.commit.assert_called_once()
        self.assertIsInstance(result, Contact)
        self.assertEqual(result.first_name, body.first_name)
        self.assertEqual(result.last_name, body.last_name)
        self.assertEqual(result.email, body.email)
        self.assertEqual(result.phone_number, body.phone_number)

    async def test_delete_contact(self):
        contact = Contact(id=1,
                          first_name='test1',
                          last_name='test1',
                          email='test1@ya.ua',
                          phone_number='+380123456789',
                          user=self.user)
        mocked_contact = MagicMock()
        mocked_contact.scalar_one_or_none.return_value = contact
        self.session.execute.return_value = mocked_contact
        result = await delete_contact(1, self.session, self.user)

        self.session.delete.assert_called_once()
        self.session.commit.assert_called_once()
        self.assertIsInstance(result, Contact)

    async def test_search_contacts(self):
        search_text = "test"
        limit = 10
        offset = 0

        contact1 = Contact(id=1, first_name="test1", last_name="test1", email="test1@ya.ua", user=self.user)
        contact2 = Contact(id=2, last_name="test2", email="test2@ya.ua", user=self.user)
        contact3 = Contact(id=3, first_name="other", last_name="other", email="other@ya.ua", user=self.user)
        self.session.add_all([contact1, contact2, contact3])
        await self.session.commit()

        # Configure mocks to return a list of contacts containing only two contacts
        matching_contacts = [contact1, contact2]
        mocked_contacts = MagicMock()
        mocked_contacts.scalars.return_value.all.return_value = matching_contacts
        self.session.execute.return_value = mocked_contacts

        result = await search_contacts(search_text, limit, offset, self.session, self.user)

        self.assertEqual(result, matching_contacts)
        self.assertNotIn(contact3, result)

    async def test_get_birthdays(self):
        delta_days = 3
        limit = 10
        offset = 0

        today = date.today()
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)
        after_tomorrow = tomorrow + timedelta(days=1)
        contact1 = Contact(id=1, first_name="test1", last_name="test1", birthday=yesterday.isoformat(), user=self.user)
        contact2 = Contact(id=2, last_name="test2", email="test2@ya.ua", birthday=tomorrow.isoformat(), user=self.user)
        contact3 = Contact(id=3, last_name="other", email="other@ya.ua", birthday=after_tomorrow.isoformat(),
                           user=self.user)
        self.session.add_all([contact1, contact2, contact3])
        await self.session.commit()

        # Configure mocks to return a list of contacts containing only two contacts
        matching_contacts = [contact2, contact3]
        mocked_contacts = MagicMock()
        mocked_contacts.scalars.return_value.all.return_value = matching_contacts
        self.session.execute.return_value = mocked_contacts

        result = await get_birthdays(delta_days, limit, offset, self.session, self.user)

        self.assertEqual(result, matching_contacts)
        self.assertNotIn(contact1, result)