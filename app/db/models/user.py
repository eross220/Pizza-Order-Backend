from enum import StrEnum
from datetime import datetime, timedelta, timezone
import jwt
from sqlalchemy import (
    Column,
    String,
    DateTime,
    Boolean,
    func,
    select
)
from uuid import UUID
from typing import Union, Any, Sequence
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import relationship, mapped_column, Mapped, Session
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from app.db.database.base_class import Base, Serializable
from app.config.config import settings
from app.log_config import configure_logging
from app.services.encoder import hash_secret, is_valid_secret, TokenType
from app.db.models.blacklisted_token import BlacklistedToken
from app.errors.exceptions import EncodingError


logger = configure_logging()


class Gender(StrEnum):
    MALE = 'Male'
    FEMALE = 'Female'
    OTHER = 'Other'

class Role(StrEnum):
    ADMIN = "ADMIN"
    USER = "USER"

class ActivationStatus(StrEnum):
    ACTIVE = "ACTIVE"
    DEACTIVATED = "DEACTIVATED"
    PENDING = "PENDING"
    RESET = "RESET"

class User(Base, Serializable):
    __tablename__ = "users"
    
    # account identifiers
    email: Mapped[str] = mapped_column(
        String(320), index=True, unique=True, nullable=False
    )
    # account security
    secret_hash: Mapped[str] = mapped_column(String(250), nullable=True)
    # personal information
    first_name: Mapped[str] = mapped_column(String(250), nullable=False)
    last_name: Mapped[str] = mapped_column(String(250), nullable=False)
    gender: Mapped[Gender] = mapped_column(ENUM(Gender), nullable= True) 
    phone_number: Mapped[str] = mapped_column(String(200), nullable= True)
    identiy_number: Mapped[str] = mapped_column(String(200), nullable= True)
    address: Mapped[str] = mapped_column(String(250), nullable= True)
    # account validation
    is_verified_email: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # account status & permissions
    role: Mapped[Role] = mapped_column(ENUM(Role), nullable=False)
    activation_status: Mapped[ActivationStatus] = mapped_column(
        ENUM(ActivationStatus), nullable=False
    )

    # cases = relationship(
    #     "Case", back_populates="users", lazy = "joined"
    # )

    @classmethod
    def count(cls, session: Session) -> int:
        """
        Counts the number of users in the database.
        :param session: The database session.
        :type session: Session
        :return: The number of users in the database.
        :rtype: int
        """
        return session.execute(func.count(cls.id)).scalar()

    @classmethod
    def get_ids(cls, session: Session, offset: int, limit: int) -> Sequence[UUID]:
        """
        Gets all users in the database.
        :param session: The database session.
        :type session: Session
        :param offset: The offset of the query.
        :type offset: int
        :param limit: The limit of the query.
        :type limit: int
        :return: The users.
        """
        return (
            session.execute(select(cls.id).offset(offset).limit(limit)).scalars().all()
        )

    @classmethod
    def get_users_by_ids(
        cls, ids: Sequence[UUID], session: Session
    ) -> Sequence["User"]:
        """
        Gets all users by their ids.
        :param ids: The ids of the users to be retrieved.
        :type ids: Sequence[UUID]
        :param session: The database session.
        :type session: Session
        :return: The users.
        """
        return session.execute(select(cls).where(cls.id.in_(ids))).scalars().all()

    @classmethod
    def get_by_email(cls, email: str, session: Session) -> "User":
        """
        Gets a user by email.
        :param email: The user's email address.
        :type email: str
        :param session: The database session.
        :type session: Session
        :return: The user.
        :rtype: User
        """
        return session.execute(
            select(cls).where(cls.email == email)
        ).unique().scalar_one_or_none()

    def full_name(self) -> str:
        names = []
        if self.first_name:
            names.append(self.first_name)
        if self.last_name:
            names.append(self.last_name)
        return " ".join(names)

    def encode_jwt(self, token_type:TokenType) -> str:
        try:
            if(token_type==TokenType.AUTHENTICATION):     
                expires_delta = datetime.now() + timedelta(
                    minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
                )
                secret_key = settings.JWT_SECRET_KEY
            elif (token_type==TokenType.REFRESH):
                expires_delta = datetime.now() + timedelta(
                    minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES
                )
                secret_key = settings.JWT_REFRESH_SECRET_KEY

            payload = {
                "exp": expires_delta,
                "sub":  self.id.__str__()
            }
            encoded_jwt = jwt.encode(
                payload, secret_key, settings.ALGORITHM
            )
            return encoded_jwt
        except Exception as e:
            return None
    
    @classmethod
    def decode_jwt(
        cls, session: Session, token: str, token_type=TokenType.AUTHENTICATION
    ) -> Union[dict, str]:
        """
        Decodes the auth token
        :param session: The database session.
        :type session: Session
        :param token: The auth token to be decoded.
        :type token: str
        :param token_type: The type of token to be decoded.
        :type token_type: str
        :return: The encoded payload if successful, otherwise an error message.
        :rtype: Union[dict, str]
        """
        try:
            payload = jwt.decode(jwt=token, key=settings.JWT_SECRET_KEY, algorithms=settings.ALGORITHM)
            if BlacklistedToken.is_blacklisted(session, token):
                logger.warning(f"Token is blacklisted. Please log in again.")
                return "Token is blacklisted. Please log in again."
            else:
                return payload
        except jwt.ExpiredSignatureError:
            logger.warning(f"{token_type} Token expired.")
            return f"{token_type} Token expired."
        except jwt.InvalidTokenError:
            logger.warning(f"Invalid {token_type.lower()} token.")
            return f"Invalid {token_type.lower()} token."


    def encode_single_use_jws(self, token_type: TokenType) -> str:
        """
        Generates a single use JSON web signature.
        :param token_type: The type of token to be generated.
        :type token_type: TokenType
        :return: The encoded single use signature.
        :rtype: str
        """
        try:
            signer = URLSafeTimedSerializer(settings.ACTIVATION_TOKEN_SECRET)
            data = {"id": self.id.__str__(), "type": token_type.value}
            return signer.dumps(data)
        except Exception as e:
            raise EncodingError("Error encoding single use JWS")

    @classmethod
    def decode_single_use_jws(
        cls, session: Session, token: str, required_token_type: TokenType
    ) -> dict:
        """
        :param session: The database session.
        :type session: Session
        :param token: JSON Web Signature to verify.
        :type token: str
        :param required_token_type: token type expected in JSON Web Signature.
        :type required_token_type: TokenType
        :return: The user if successful, otherwise an error message.
        :rtype: dict
        """
        try:
            signer = URLSafeTimedSerializer(settings.ACTIVATION_TOKEN_SECRET)
            data = signer.loads(token, max_age=settings.ACTIVATION_TOKEN_EXPIRY)
            user_id = data.get("id")
            token_type = data.get("type")
            if token_type != required_token_type.value:
                logger.warning(
                    f"Wrong token type (needed {required_token_type.value}, got {token_type})"
                )
                return {
                    "status": 1,
                    "message": f"Wrong token type (needed {required_token_type.value}, got {token_type})",
                }
            if not user_id:
                return {"status": 1, "message": "No User ID provided."}
            query = select(cls).where(cls.id == user_id)
            user = (session.execute(query)).unique().scalar_one_or_none()
            if not user:
                return {"status": 1, "message": "User not found."}
            return {"status": 0, "user": user}

        except SignatureExpired:
            logger.warning("Token signature expired.")
            return {
                "status": 1,
                "message": "The activation email is not valid anymore. Please contact your administrator.",
            }

        except BadSignature:
            logger.warning("Token signature not valid.")
            return {"status": 1, "message": "Token signature not valid."}

        except Exception as exception:
            return {"status": 1, "message": exception}

    def hash_secret(self, secret: str) -> None:
        """
        Hashes the secret provided by the user.
    :param secret: Plain text secret.
        :type secret: str
        :return: None
        """
        self.secret_hash = hash_secret(secret)

    def verify_secret(self, secret: str) -> bool:
        """
        Verifies the secret provided by the user.
        :param secret: The secret to be verified.
        :type secret: str
        :return: True if the secret is valid, otherwise False.
        :rtype: bool
        """
        return is_valid_secret(self.secret_hash, secret)

    @classmethod
    def create(
        cls,
        email: str,
        first_name: str,
        last_name: str,
        session: Session,
        role: Role = Role.USER,
    ) -> "User":
        """
        Creates a new user.
        :param email: The user's email address.
        :type email: str
        :param role: The user's role.
        :type role: Role
        :param session: The database session.
        :type session: Session
        :return: The new user.
        :rtype: User
        """
        user = User(
            activation_status=ActivationStatus.PENDING,
            email=email,
            is_verified_email=False,
            role=role,
            first_name=first_name,
            last_name=last_name,
        )
        session.add(user)
        session.commit()
        return user

    def update(
        self,
        data: dict,
        session: Session,
    ) -> None:
        """
        Updates the user.
        :param data: The parameters to update.
        :type data: dict
        :param session: The database session.
        :type session: Session
        :return: None
        """
        for key, value in data.items():
            setattr(self, key, value)

        session.add(self)
        session.commit()
        session.refresh(self)
    