from datetime import date, timedelta

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.operators import or_

from src.database.models import Contact
from src.schemas.contacts import ContactCreateSchema, ContactUpdateSchema


async def get_contacts(limit: int, offset: int, db: AsyncSession):
    """
    The get_contacts function returns a list of contacts for the user.

    :param limit: int: Limit the number of contacts returned
    :param offset: int: Specify how many contacts to skip before returning the results
    :param db: AsyncSession: Pass the database session to the function
    :param user: User: Get the user id from the user object
    :return: A list of contacts
    :doc-author: Trelent
    """
    stmt = select(Contact).offset(offset).limit(limit)
    contacts = await db.execute(stmt)
    return contacts.scalars().all()


async def get_contact(contact_id: int, db: AsyncSession):
    """
    The get_contact function returns a contact from the database.

    :param contact_id: int: Filter the query by id
    :param db: AsyncSession: Pass the database session to the function
    :param user: User: Ensure that the user is only able to get contacts they own
    :return: A contact object or none
    :doc-author: Trelent
    """
    stmt = select(Contact).filter_by(id=contact_id)
    contact = await db.execute(stmt)
    return contact.scalar_one_or_none()


async def create_contact(body: ContactCreateSchema, db: AsyncSession):
    """
    The create_contact function creates a new contact in the database.

    :param body: ContactCreateSchema: Validate the request body
    :param db: AsyncSession: Pass the database session to the function
    :param user: User: Get the user id from the token
    :return: A contact object
    :doc-author: Trelent
    """
    contact = Contact(**body.model_dump(exclude_unset=True))
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact


async def update_contact(contact_id: int, body: ContactUpdateSchema, db: AsyncSession):
    """
    The update_contact function updates a contact in the database.

    :param contact_id: int: Specify the contact we want to update
    :param body: ContactUpdateSchema: Validate the request body
    :param db: AsyncSession: Pass in the database session
    :param user: User: Ensure that the user is authorized to update the contact
    :return: The updated contact
    :doc-author: Trelent
    """
    stmt = select(Contact).filter_by(id=contact_id)
    contact = await db.execute(stmt)
    contact = contact.scalar_one_or_none()

    if contact is not None:
        for field, value in body.model_dump(exclude_unset=True).items():
            setattr(contact, field, value)

        await db.merge(contact)
        await db.commit()
        await db.refresh(contact)

    return contact


async def delete_contact(contact_id: int, db: AsyncSession):
    """
    The delete_contact function deletes a contact from the database.

    :param contact_id: int: Specify the id of the contact to delete
    :param db: AsyncSession: Pass in the database session
    :param user: User: Identify the user who is making the request
    :return: The deleted contact
    :doc-author: Trelent
    """
    stmt = select(Contact).filter_by(id=contact_id)
    contact = await db.execute(stmt)
    contact = contact.scalar_one_or_none()

    if contact is not None:
        await db.delete(contact)
        await db.commit()

    return contact


async def search_contacts(search_text: str,
                          limit: int,
                          offset: int,
                          db: AsyncSession):
    stmt = select(Contact).filter(
        or_(
            func.lower(Contact.email).ilike(f"%{search_text.lower()}%"),
            or_(
                func.lower(Contact.first_name).ilike(f"%{search_text.lower()}%"),
                func.lower(Contact.last_name).ilike(f"%{search_text.lower()}%")
            )
        )
    )
    """
    The search_contacts function searches the contacts table for a user's contacts.
    It takes in search_text, limit, offset and db as parameters. It returns a list of
    contacts that match the search criteria.

    :param search_text: str: Search the database for contacts that have a first name, last name or email address
    :param limit: int: Limit the number of contacts returned
    :param offset: int: Specify the number of records to skip
    :param db: AsyncSession: Pass the database session to the function
    :param user: User: Get the user id from the user object
    :return: A list of contact objects
    :doc-author: Trelent
    """
    stmt = stmt.limit(limit).offset(offset)
    contacts = await db.execute(stmt)
    return contacts.scalars().all()


async def get_birthdays(days: int, limit: int, offset: int, db: AsyncSession):
    """
    The get_birthdays function returns a list of contacts whose birthdays are within the specified number of days.

    :param days: int: Specify the number of days to look ahead
    :param limit: int: Limit the number of results returned
    :param offset: int: Specify the offset of the query
    :param db: AsyncSession: Pass the database session to the function
    :param user: User: Filter the contacts by user
    :return: A list of contacts that have birthdays in the next few days
    :doc-author: Trelent
    """
    today = date.today()
    end_date = today + timedelta(days=days)

    stmt = select(Contact).filter(
        func.date_part('month', Contact.birthday) >= today.month,
        func.date_part('month', Contact.birthday) <= end_date.month,
        func.date_part('day', Contact.birthday) >= today.day,
        func.date_part('day', Contact.birthday) <= end_date.day
    ).order_by(Contact.birthday)

    stmt = stmt.limit(limit).offset(offset)
    contacts = await db.execute(stmt)
    return contacts.scalars().all()