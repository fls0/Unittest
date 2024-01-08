from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks, Request, Form
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.repository import users as repository_users
from src.schemas.users import UserCreateSchema, TokenSchema, UserResponseSchema, RequestEmail
from src.services.auth import auth_service
from src.services.email import send_email

router = APIRouter(prefix='/auth', tags=['auth'])
get_refresh_token = HTTPBearer()


@router.post("/signup", response_model=UserResponseSchema, status_code=status.HTTP_201_CREATED)
async def signup(body: UserCreateSchema, db: AsyncSession = Depends(get_db)):
    """
    The signup function creates a new user in the database.
        It takes a UserCreateSchema as input, which is validated by pydantic.
        If the email already exists in the database, it returns an HTTP 409 Conflict error.
        Otherwise, it hashes the password and creates a new user with that information.

    :param body: UserCreateSchema: Validate the request body
    :param bt: BackgroundTasks: Add a task to the background tasks queue
    :param request: Request: Get the base_url of the application
    :param db: AsyncSession: Get the database session
    :return: A dict with the user and a detail message
    :doc-author: Trelent
    """

    exist_user = await repository_users.get_user_by_email(body.email, db)
    if exist_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Email already exists")

    body.password = auth_service.get_password_hash(body.password)
    new_user = await repository_users.create_user(body, db)
    return {"user": new_user, "detail": "User successfully created"}


@router.post("/login", response_model=TokenSchema, status_code=status.HTTP_201_CREATED)
async def login(body: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """
    The login function is used to authenticate a user.
        It takes the username and password from the request body,
        verifies that they are correct, and returns an access token.

    :param body: OAuth2PasswordRequestForm: Validate the request body
    :param db: AsyncSession: Get the database session from the dependency injection container
    :param cache: Cache: Get the cache from the dependency injection container
    :return: A token
    :doc-author: Trelent
    """

    user = await repository_users.get_user_by_email(body.username, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email")
    if not auth_service.verify_password(body.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password")
    access_token = await auth_service.create_access_token(data={"sub": user.email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": user.email})
    await repository_users.update_token(user, refresh_token, db)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.get('/refresh_token', response_model=TokenSchema)
async def refresh_token(credentials: HTTPAuthorizationCredentials = Depends(get_refresh_token),
                        db: AsyncSession = Depends(get_db)):
    """
    The refresh_token function is used to refresh the access token.
    It takes in a refresh token and returns a new access token.
    The function first decodes the refresh_token to get the email of the user who owns it, then checks if that user exists in our database.
    If not, we raise an HTTPException with status code 401 (UNAUTHORIZED).
    If they do exist, we create a new access_token and refresh_token for them using auth_service's create functions.
    We update their tokens in our database by calling repository users' update function with their current user object and new tokens

    :param credentials: HTTPAuthorizationCredentials: Get the credentials from the request header
    :param db: AsyncSession: Get the database session
    :param cache: Cache: Get the cache from the dependency injection container
    :return: A new access_token and refresh_token
    :doc-author: Trelent
    """
    token = credentials.credentials
    email = await auth_service.decode_refresh_token(token)
    user = await repository_users.get_user_by_email(email, db)
    if user.refresh_token != token:
        await repository_users.update_token(user, None, db)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    access_token = await auth_service.create_access_token(data={"sub": email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": email})
    await repository_users.update_token(user, refresh_token, db)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.get('/confirmed_email/{token}')
async def confirmed_email(token: str, db: AsyncSession = Depends(get_db)):
    """
    The confirmed_email function is used to confirm a user's email address.
        It takes the token from the URL and uses it to get the user's email address.
        Then, it checks if that user exists in our database and if they have already confirmed their email.
        If not, then we update their record in our database with a confirmation of their email.

    :param token: str: Get the token from the url
    :param db: AsyncSession: Get the database session from the dependency
    :param cache: Cache: Get the cache from the dependency injection container
    :return: A message that the email has been confirmed
    :doc-author: Trelent
    """
    email = await auth_service.get_email_from_token(token)
    user = await repository_users.get_user_by_email(email, db)
    print(user)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error")
    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    await repository_users.confirmed_email(email, db)
    return {"message": "Email confirmed"}


@router.post('/request_email')
async def request_email(body: RequestEmail, bt: BackgroundTasks, request: Request,
                        db: AsyncSession = Depends(get_db)):
    """
    The request_email function is used to send an email confirmation link to the user's email address.
    The function takes in a RequestEmail object, which contains the user's email address. The function then checks if
    the user exists and if they have already confirmed their account. If not, it sends them an email with a confirmation link.

    :param body: RequestEmail: Validate the request body
    :param bt: BackgroundTasks: Add a task to the background tasks queue
    :param request: Request: Get the base url of the request
    :param db: AsyncSession: Get the database session
    :param cache: Cache: Get the cache from the dependency injection container
    :return: A message
    :doc-author: Trelent
    """
    user = await repository_users.get_user_by_email(body.email, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email")
    if user.confirmed:
        return {"message": "Your email is already confirmed"}

    bt.add_task(send_email, user.email, user.username, str(request.base_url),
                header_msg='Email confirmation', template_name='verify_email.html')
    return {"message": "Check your email for confirmation."}