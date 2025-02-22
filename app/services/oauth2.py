from fastapi import Depends, HTTPException, Request, status, Header
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database.session import get_session
from app.log_config import configure_logging
from app.db.models import User
from app.tools import constants
from app.db.models.user import ActivationStatus

# Configure logging
logger = configure_logging()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login", auto_error=False)


def raise_auth_exception(detail: str, status_code: int = status.HTTP_401_UNAUTHORIZED):
    raise HTTPException(
        detail={"message": detail, "status": 1},
        headers={"WWW-Authenticate": "Bearer"},
        status_code=status_code,
    )



def get_current_user(
    request: Request,
    session: Session = Depends(get_session),
    token: str = Depends(oauth2_scheme),
) -> User:
    """
    Get the current user from the database.
    :param request: The request object.
    :type request: Request
    :param session: The database session.
    :type session: Session
    :param token: The authentication token.
    :type token: str
    :param api_key: The api key for the authentication token.
    :type api_key: str
    :return: The user object.
    :rtype: User
    """
    # decode token with session as context manager
    # decode the token and check blacklisted status
    payload = User.decode_jwt(session=session, token=token)

    if isinstance(payload, str):
        # raise credentials exception
        raise_auth_exception(payload)

    # get the user id
    user_id = payload.get("sub")

    # check if the user id is present
    if not user_id:
        # raise credentials exception
        raise_auth_exception(constants.INVALID_ACCESS_TOKEN)

    # get the user
    user = session.execute(select(User).filter(User.id == user_id)).unique().scalar_one_or_none()

    # check if the user is present
    if not user:
        # raise credentials exception
        raise_auth_exception(constants.UNKNOWN_USER)

    # check if the user is active
    if user.activation_status != ActivationStatus.ACTIVE:
        # raise credentials exception
        raise_auth_exception(constants.USER_NOT_ACTIVE, status.HTTP_403_FORBIDDEN)

    request.state.user = user.serialize()

    # return the user
    return user
