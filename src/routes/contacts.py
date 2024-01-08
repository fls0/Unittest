from fastapi import APIRouter, HTTPException, Depends, status, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.repository import contacts as repositories_contacts
from src.schemas.contacts import ContactCreateSchema, ContactUpdateSchema, ContactResponseSchema

router = APIRouter(prefix='/contacts', tags=['contacts'])


@router.get("/", response_model=list[ContactResponseSchema])
async def get_contacts(limit: int = Query(10, ge=10, le=500),
                       offset: int = Query(0, ge=0),
                       db: AsyncSession = Depends(get_db)):
    """
    The get_contacts function returns a list of contacts.

    :param limit: int: Limit the number of contacts returned
    :param ge: Specify the minimum value of the parameter
    :param le: Specify the maximum value of the limit parameter
    :param offset: int: Specify the offset of the contacts to be returned
    :param ge: Specify the minimum value that can be accepted
    :param db: AsyncSession: Pass the database session to the function
    :param current_user: User: Get the current user from the database
    :return: A list of contacts, which is a list of dictionaries
    :doc-author: Trelent
    """
    contacts = await repositories_contacts.get_contacts(limit, offset, db)
    return contacts


@router.get("/{contact_id}", response_model=ContactResponseSchema)
async def get_contact(contact_id: int, db: AsyncSession = Depends(get_db)):
    """
    The get_contact function is a GET request that returns the contact with the given ID.
    If no such contact exists, it raises an HTTPException with status code 404 and detail &quot;NOT FOUND&quot;.


    :param contact_id: int: Get the contact id from the url
    :param db: AsyncSession: Get the database session
    :param current_user: User: Get the current user
    :return: A contact object, which is defined in models
    :doc-author: Trelent
    """
    contact = await repositories_contacts.get_contact(contact_id, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NOT FOUND")
    return contact


@router.post("/", response_model=ContactResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_contact(body: ContactCreateSchema, db: AsyncSession = Depends(get_db)):
    """
    The create_contact function creates a new contact in the database.

    :param body: ContactCreateSchema: Validate the request body
    :param db: AsyncSession: Pass the database session to the function
    :param current_user: User: Get the current user from the auth_service
    :return: The contact that was created
    :doc-author: Trelent
    """
    contact = await repositories_contacts.create_contact(body, db)
    return contact


@router.put("/{contact_id}", response_model=ContactResponseSchema, status_code=status.HTTP_200_OK)
async def update_contact(body: ContactUpdateSchema, contact_id: int, db: AsyncSession = Depends(get_db)):
    """
    The update_contact function updates a contact in the database.
        The function takes an id of the contact to be updated, and a body containing
        all fields that are to be updated.

    :param body: ContactUpdateSchema: Validate the request body
    :param contact_id: int: Get the contact id from the url
    :param db: AsyncSession: Pass the database session to the repository
    :param current_user: User: Get the user that is currently logged in
    :return: A contact object
    :doc-author: Trelent
    """
    contact = await repositories_contacts.update_contact(contact_id, body, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NOT FOUND")
    return contact


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(contact_id: int, db: AsyncSession = Depends(get_db)):
    """
    The delete_contact function deletes a contact from the database.
    Args:
        contact_id (int): The id of the contact to be deleted.
        db (AsyncSession, optional): The database session. Defaults to Depends(get_db).
        current_user (User, optional): The current user. Defaults to Depends(get_current_user).

    :param contact_id: int: Identify the contact to be deleted
    :param db: AsyncSession: Pass the database session to the function
    :param current_user: User: Get the current user from the database
    :return: The contact that was deleted
    :doc-author: Trelent
    """
    contact = await repositories_contacts.delete_contact(contact_id, db)
    return contact


@router.get("/search/{search_text}", response_model=list[ContactResponseSchema])
async def search_contacts(search_text: str,
                          limit: int = Query(10, ge=10, le=500),
                          offset: int = Query(0, ge=0),
                          db: AsyncSession = Depends(get_db)):
    """
    The search_contacts function searches for contacts in the database.
        It takes a search_text parameter, which is used to find contacts that match it.
        The limit and offset parameters are used to paginate the results of this query.

    :param search_text: str: Search for contacts that have a name or email address
    :param limit: int: Limit the number of contacts returned
    :param ge: Set a minimum value for the limit parameter
    :param le: Limit the number of contacts returned
    :param offset: int: Specify the number of records to skip before returning results
    :param ge: Specify the minimum value of the limit parameter
    :param db: AsyncSession: Get the database session
    :param current_user: User: Get the user id of the current user
    :return: A list of contacts
    :doc-author: Trelent
    """
    if len(search_text) < 3:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Search text must be at least 3 characters long")
    contacts = await repositories_contacts.search_contacts(search_text, limit, offset, db)
    if len(contacts) == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NOT FOUND")
    return contacts


@router.get("/birthdays/{days}", response_model=list[ContactResponseSchema])
async def get_birthdays(days: int,
                        limit: int = Query(10, ge=10, le=500),
                        offset: int = Query(0, ge=0),
                        db: AsyncSession = Depends(get_db)):
    """
    The get_birthdays function returns a list of contacts that have birthdays within the next days. The function
    takes in an integer, days, which is used to determine how many days from now we want to search for birthdays. The
    function also takes in two optional parameters: limit and offset. These are used for pagination purposes and
    allow us to specify how many results we want returned at once as well as where in the result set we would like
    our results returned from.

    :param days: int: Specify the number of days in the future to search for birthdays
    :param limit: int: Limit the number of contacts returned
    :param ge: Set a minimum value for the parameter
    :param le: Limit the number of results returned
    :param offset: int: Skip the first n contacts
    :param ge: Specify that the value of limit must be greater than or equal to 10
    :param db: AsyncSession: Get the database session
    :param current_user: User: Get the current user from the auth_service
    :return: A list of contacts that have a birthday within the specified number of days
    :doc-author: Trelent
    """
    if days <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Days must be positive")
    contacts = await repositories_contacts.get_birthdays(days, limit, offset, db)
    if len(contacts) == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NOT FOUND")
    return contacts