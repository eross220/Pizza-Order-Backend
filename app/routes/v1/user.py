# standard library imports
from typing import List, Union

# third-party imports
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy import func, literal
from fastapi.responses import Response

# local imports
from app.db.database.session import get_session
from app.services.oauth2 import get_current_user
from app.docs.openapi.routes.user import(
    register_responses,
    login_responses,
    logout_responses,
    forgot_password_responses,
    reset_password_responses,
    refresh_token_responses,
    me_responses,
)
from app.tools.generic import check_password
from app.db.schemas.user import (
    RegisterationRequest,
    UserLoginRequest,
    UserTokenRequest,
    BaseUserModel,
    BaseEmailModel,
    UserResetPasswordRequest
)
from app.db.schemas.base import BaseResponse
from app.db.schemas.user import UserTokenResponse, UserBasicOut, UserFullResponse
from app.db.models.user import User, ActivationStatus, Role
from app.tools import constants
from app.services.encoder import hash_secret, TokenType
from app.db.models.blacklisted_token import BlacklistedToken
from app.services.oauth2 import oauth2_scheme
from app.services.mailer import Mailer

router = APIRouter()


def generate_tokens(user: User) -> dict:
    """
    Generate tokens for a user.
    :param user: The user to generate tokens for.
    :type user: User
    :return: The tokens.
    :rtype: dict
    """
    access_token = user.encode_jwt(token_type=TokenType.AUTHENTICATION)
    refresh_token = user.encode_jwt(token_type=TokenType.REFRESH)
    return {"access_token": access_token, "refresh_token": refresh_token}


@router.post(
    "/register", responses=register_responses(), status_code=status.HTTP_201_CREATED
)
def register(
    data: RegisterationRequest,
    response: Response,
    session: Session = Depends(get_session)
)-> BaseResponse:
    """
    Register a new user.
    :param data: The data to use for registration.
    :type data: CredentialsRequest
    :param disabled: The disabled route dependency.
    :type disabled: None
    :param response: The response object to use. Used set the status code.
    :type response: Response
    :param session: The database session to use.
    :type session: Session
    :return: The response.
    :rtype: BaseResponse
    """
    try:
        # check if user already exists
        user = User.get_by_email(session=session, email=data.email)
        if user:
            response.status_code = status.HTTP_409_CONFLICT
            return BaseResponse(message=constants.USER_ALREADY_EXISTS, status=1)
    
        if data.password == None:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(message=constants.PASSWORD_NOT_SET, status=1)
        # validate password
        validate_error = check_password(data.password)
        if validate_error:
            response.status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
            return BaseResponse(message=validate_error, status=1)

        user = User(
            email=data.email,
            secret_hash=hash_secret(data.password),
            first_name=data.first_name,
            last_name=data.last_name,
            gender = data.gender,
            phone_number = data.phone_number,
            identiy_number = data.identity_number,
            address = data.address,
            is_verified_email=False,
            role=Role.USER,
            activation_status=ActivationStatus.DEACTIVATED,
        )
        session.add(user)
        session.commit()

        mailer = Mailer( 
            "Istanbul, Turkey", "en", "AdaletGPT", "auth@adaletgpt.com"
        )
        token = user.encode_single_use_jws(TokenType.ACTIVATION)
        mailer.send_template_email(
            "user_activation",
            user.email,
            f"{user.first_name} {user.last_name}",
            {"token": token, "template":"action_email"}
        )
        return BaseResponse(
            message=constants.USER_REGISTRATION_SUCCESSFUL, status=0
        )
    
    except Exception as e:

        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return BaseResponse(message=constants.USER_REGISTRATION_FAILED, status=1)

@router.post("/login", responses=login_responses())
def login(
    data: UserLoginRequest,
    response: Response,
    session: Session = Depends(get_session)
) -> Union[BaseResponse, UserTokenResponse]:
    """
    Login a user.
    :param data: The data to use for login.
    :type data: UserLoginRequest
    :param response: The response object to use. Used set the status code.
    :type response: Response
    :param session: The database session to use.
    :type session: Session
    :return: The response.
    :rtype: AuthResponse
    """
    try:
        user = User.get_by_email(session=session, email=data.email)
        if not user:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(message=constants.UNKNOWN_USER, status=1)
        
        if user.activation_status != ActivationStatus.ACTIVE:
            response.status_code = status.HTTP_403_FORBIDDEN
            return BaseResponse(message=constants.NON_VALIDATED_USER, status=1)
        
        is_valid_password = user.verify_secret(data.password)
        if not is_valid_password:
            response.status_code = status.HTTP_403_FORBIDDEN
            return BaseResponse(message=constants.INVALID_CREDENTIALS, status=1)
        
        # gnerate access and refresh tokens
        tokens = generate_tokens(user)
        user_basic_data = UserBasicOut(
            id=user.id,
            email=user.email,
            role=user.role,
            activation_status=user.activation_status,
            first_name=user.first_name,
            last_name=user.last_name,
            gender=user.gender,
            phone_number=user.phone_number,
            identiy_number=user.identiy_number,
            address=user.address,
        )
        return UserTokenResponse(
            access_token= tokens.get("access_token"),
            user = user_basic_data,
            message=constants.LOGIN_SUCCESSFUL,
            refresh_token=tokens.get("refresh_token"),
            status=0
        )


    except Exception as e:
        response.status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        return BaseResponse(message=constants.LOGIN_FAILED, status=1)

@router.get("/me", responses=me_responses())
def me(
    response: Response, user: User = Depends(get_current_user)
) -> Union[UserFullResponse, BaseResponse]:
    """
    Get the current user.
    :param response: The response object to use. Used set the status code.
    :type response: Response
    :param user: The current user.
    :type user: User
    :return: The response.
    :rtype: AuthResponse
    """
    try:
        # Get environment information
        user_basic_data = UserBasicOut(
            id=user.id,
            email=user.email,
            role=user.role,
            activation_status=user.activation_status,
            first_name=user.first_name,
            last_name=user.last_name,
            gender=user.gender,
            phone_number=user.phone_number,
            identiy_number=user.identiy_number,
            address=user.address,
        )
        return UserFullResponse(
            user=user_basic_data,
            message=constants.USER_LOAD_SUCCESSFUL,
            status=0,
        )

    except Exception as e:
        response.status_code = status.HTTP_403_FORBIDDEN
        return BaseResponse(message=constants.LOGIN_FAILED, status=1)

@router.post("/logout", responses=logout_responses())
def logout(
    response: Response,
    session: Session = Depends(get_session),
    token: str = Depends(oauth2_scheme),
) -> BaseResponse:
    """
    Logout a user.
    :param response: The response object to use. Used set the status code.
    :type response: Response
    :param session: The database session to use.
    :type session: Session
    :param token: The access token to use.
    :type token: str
    :return: The response.
    :rtype: AuthResponse
    """
    # add the token to the blacklist
    try:
        blacklisted_token = BlacklistedToken(token=token)
        session.add(blacklisted_token)
        session.commit()
        return BaseResponse(message="Logout successful", status=0)
    except Exception as e:
        print(e)
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return BaseResponse(message="Logout failed", status=1)

@router.post("/activate")
def activate_user(
    data: UserTokenRequest,
    response: Response,
    session: Session = Depends(get_session),
) -> Union[BaseResponse, UserTokenResponse]:
    """
    Activate a user.
    :param data: The data to use for activation.
    :type data: UserTokenRequest
    :param response: The response object to use. Used set the status code.
    :type response: Response
    :param session: The database session to use.
    :type session: Session
    :return: The response.
    :rtype: AuthResponse
    """
    try:
        token = data.token
        if not token:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(message=constants.INVALID_ACTIVATION_TOKEN, status=1)
        decoded_token = User.decode_single_use_jws(session, token, TokenType.ACTIVATION)
        is_valid_token = decoded_token.get("status") == 0
        if not is_valid_token:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(message=decoded_token.get("message"), status=1)
        
        user: User = decoded_token.get("user")
        if user.activation_status == ActivationStatus.ACTIVE:
            response.status_code = status.HTTP_403_FORBIDDEN
            return BaseResponse(message=constants.USER_ALREADY_ACTIVATED, status=1)

        user.is_verified_email = True
        user.activation_status = ActivationStatus.ACTIVE

        session.add(user)
        session.commit()
        session.refresh(user)

        tokens = generate_tokens(user)

        user_basic_data = UserBasicOut(
            id=user.id,
            email=user.email,
            role=user.role,
            activation_status=user.activation_status,
            first_name=user.first_name,
            last_name=user.last_name,
            gender=user.gender,
            phone_number=user.phone_number,
            identiy_number=user.identiy_number,
            address=user.address,
        )
        
        return UserTokenResponse(
            access_token=tokens.get("access_token"),
            data=user_basic_data,
            message=constants.USER_ACTIVATION_SUCCESSFUL,
            refresh_token=tokens.get("refresh_token"),
            status=0,
        )

    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return BaseResponse(message=constants.USER_ACTIVATION_FAILED, status=1)


@router.post("/forgot-password", responses=forgot_password_responses())
def forgot_password(
    data: BaseEmailModel, response: Response, session: Session = Depends(get_session)
) -> BaseResponse:
    """
    Forgot password.
    :param data: The data to use for forgot password.
    :type data: BaseAuthModel
    :param response: The response object to use. Used set the status code.
    :type response: Response
    :param session: The database session to use.
    :type session: Session
    :return: The response.
    :rtype: BaseResponse
    """
    try:
        user = User.get_by_email(data.email, session)
        if not user:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(message=constants.UNKNOWN_USER, status=1)
        
        if user.activation_status != ActivationStatus.ACTIVE:
            # send activation email if user is not active
            mailer = Mailer( 
                "Istanbul, Turkey", "en", "AdaletGPT", "auth@adaletgpt.com"
            )
            token = user.encode_single_use_jws(TokenType.ACTIVATION)
            mailer.send_template_email(
                "user_activation",
                user.email,
                f"{user.first_name} {user.last_name}",
                {"token": token, "template": "action_email"},
            )
        # Send email to user with reset password link:
        else:
            password_reset_token = user.encode_single_use_jws(TokenType.PASSWORD_RESET)
            mailer = Mailer( 
                "Istanbul, Turkey ", "en", "AdaletGPT", "auth@adaletgpt.com"
            )
            mailer.send_template_email(
                "reset_password",
                user.email,
                f"{user.first_name} {user.last_name}",
                {"token": password_reset_token, "template": "action_email"},
            )
        return BaseResponse(message=constants.PASSWORD_RESET_EMAIL_SENT, status=0)
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return BaseResponse(message=constants.PASSWORD_RESET_EMAIL_FAILED, status=1)

@router.post("/reset-password", responses=reset_password_responses())
def reset_password(
    data: UserResetPasswordRequest,
    response: Response,
    session: Session = Depends(get_session),
) -> BaseResponse:
    """
    Reset password.
    :param data: The data to use for reset password.
    :type data: ResetPasswordRequest
    :param response: The response object to use. Used set the status code.
    :type response: Response
    :param session: The database session to use.
    :type session: Session
    :return: The response.
    :rtype: BaseResponse
    """
    try:
        # check if password is empty
        if data.password == None:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(message=constants.PASSWORD_NOT_SET, status=1)
        # validate password
        validate_error = check_password(data.password)
        if validate_error:
            response.status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
            return BaseResponse(message=validate_error, status=1)
        
        # check if token is blacklisted
        blacklisted_token = session.execute(
            select(BlacklistedToken).where(BlacklistedToken.token == data.token)
        ).unique().scalar_one_or_none()

        if blacklisted_token:
            response.status_code = status.HTTP_401_UNAUTHORIZED
            return BaseResponse(message=constants.INVALID_RESET_TOKEN, status=1)

        decoded_token = User.decode_single_use_jws(
            session, data.token, TokenType.PASSWORD_RESET
        )
        if decoded_token.get("status") != 0:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(message=decoded_token.get("message"), status=1)

        user: User = decoded_token.get("user")
        user.hash_secret(data.password)

        # blacklist the old token
        blacklisted_token = BlacklistedToken(token=data.token, user_id=user.id)
        session.add(blacklisted_token)

        session.add(user)
        session.commit()
        return BaseResponse(message=constants.PASSWORD_RESET_SUCCESSFUL, status=0)
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return BaseResponse(message=constants.PASSWORD_RESET_FAILED, status=1)


@router.post("/token/refresh", responses=refresh_token_responses())
def refresh(
    data: UserTokenRequest, response: Response, session: Session = Depends(get_session)
) -> Union[BaseResponse, UserTokenResponse]:
    """
    Refresh a user's token.
    :param data: The data to use to refresh the token.
    :type data: UserTokenRequest
    :param response: The response object to use. Used set the status code.
    :type response: Response
    :param session: The database session to use.
    :type session: Session
    :return: The response.
    :rtype: AuthResponse
    """
    try:
        # get auth token from the request header
        token = data.token

        # check if token is blacklisted
        blacklisted_token = session.execute(
            select(BlacklistedToken).where(BlacklistedToken.token == token)
        ).unique().scalar_one_or_none()

        if blacklisted_token:
            response.status_code = status.HTTP_401_UNAUTHORIZED
            return BaseResponse(message=constants.INVALID_REFRESH_TOKEN, status=1)

        # get user from token
        decoded_token = User.decode_single_use_jws(session, token, TokenType.REFRESH)
        is_valid_token = decoded_token.get("status") == 0

        if not is_valid_token:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return BaseResponse(message=decoded_token.get("message"), status=1)

        user: User = decoded_token.get("user")

        # blacklist the old token
        blacklisted_token = BlacklistedToken(token=token, user_id=user.id)
        session.add(blacklisted_token)
        session.commit()

        # generate access and refresh tokens
        tokens = generate_tokens(user)

        return UserTokenResponse(
            access_token=tokens.get("access_token"),
            data=user,
            message=constants.TOKEN_REFRESH_SUCCESSFUL,
            refresh_token=tokens.get("refresh_token"),
            status=0,
        )
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return BaseResponse(message=constants.TOKEN_REFRESH_FAILED, status=1)
