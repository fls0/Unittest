from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from libgravatar import Gravatar

from src.database.models import User
from src.schemas.users import UserCreateSchema


async def get_user_by_email(email: str, db: AsyncSession):
    """
    The get_user_by_email function takes in an email and a database session,
    and returns the user with that email. If no such user exists, it returns None.

    :param email: str: Specify the email of the user we want to retrieve
    :param db: AsyncSession: Pass the database connection to the function
    :param cache: Redis: Get the user from the cache
    :return: A user object or none if there is no matching email
    :doc-author: Trelent
    """
    stmt = select(User).filter_by(email=email)
    user = await db.execute(stmt)
    return user.scalar_one_or_none()


async def create_user(body: UserCreateSchema, db: AsyncSession):
    """
    The create_user function creates a new user in the database.

    :param body: UserCreateSchema: Validate the request body
    :param db: AsyncSession: Pass in the database session
    :param cache: Redis: Store the user in the cache
    :return: A user object
    :doc-author: Trelent
    """
    avatar = None
    try:
        g = Gravatar(body.email)
        avatar = g.get_image()
    except Exception as err:
        print(err)
    user = User(**body.model_dump(exclude_unset=True, avatar=avatar))
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def update_token(user: User, token: str | None, db: AsyncSession):
    """
    The update_token function updates the refresh token for a user.

    :param user: User: Specify the user object that is being updated
    :param token: str | None: Set the refresh token of a user
    :param db: AsyncSession: Pass the database session to the function
    :param cache: Redis: Store the user in the cache
    :return: The user object
    :doc-author: Trelent
    """
    user.refresh_token = token
    await db.commit()
    await db.refresh(user)


async def confirmed_email(email: str, db: AsyncSession) -> None:
    """
    The confirmed_email function is used to set the confirmed field of a user's account to True.
    This function is called when a user clicks on the link in their confirmation email.


    :param email: str: Get the user by email
    :param db: AsyncSession: Pass in the database session
    :param cache: Redis: Store the user in the cache
    :return: None
    :doc-author: Trelent
    """
    user = await get_user_by_email(email, db)
    user.confirmed = True
    await db.commit()


async def update_avatar(email, url: str, db: AsyncSession) -> User:
    """
    The update_avatar function updates the avatar of a user.

    :param email: str: Find the user in the database
    :param src_url: str: Update the avatar of a user
    :param db: AsyncSession: Pass the database session to the function
    :param cache: Redis: Store the user in the cache
    :return: The user object with the updated avatar
    :doc-author: Trelent
    """
    user = await get_user_by_email(email, db)
    user.avatar = url
    db.commit()
    return user
