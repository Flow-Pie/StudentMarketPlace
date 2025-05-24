from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from flask import Blueprint, request
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity,
    get_jwt
)
from sqlalchemy.exc import IntegrityError
from werkzeug.routing import ValidationError

from ...errors import APIError
from ...extensions import db
from ...models.user import TokenBlockList, User
from ...models.user import AccountStatus
from ...schemas.auth import LoginSchema, RegistrationSchema
from ...services.auth import AuthService

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        schema = LoginSchema()
        data = schema.load(request.json)

        user = User.query.filter_by(email=data['email']).first()

        if not user or not user.check_password(data['password']):
            raise APIError(
                message="Invalid credentials",
                code="INVALID_CREDENTIALS",
                status_code=HTTPStatus.UNAUTHORIZED.value
            )

        if user.account_status != AccountStatus.ACTIVE:
            if user.account_status == AccountStatus.BANNED:
                raise APIError(
                    message="Your account has been banned",
                    code="ACCOUNT_BANNED",
                    status_code=HTTPStatus.FORBIDDEN.value
                )
            raise APIError(
                message="Account not active",
                code="ACCOUNT_INACTIVE",
                status_code=HTTPStatus.FORBIDDEN.value
            )

        # Update last login
        user.last_login = datetime.now(timezone.utc)
        db.session.commit()

        access_token, refresh_token = AuthService.generate_token(user)
        return {
            "message": "Login successful",
            "tokens": {
                "access_token": access_token,
                "refresh_token": refresh_token
            },
            "user": {
                "id": user.user_id,
                "email": user.email,
                'name': user.get_full_name()
            }
        }, HTTPStatus.OK.value

    except ValidationError as err:
        raise APIError(
            message="Invalid login data",
            code="VALIDATION_ERROR",
            status_code=HTTPStatus.BAD_REQUEST.value,
        )
    except Exception as err:
        db.session.rollback()
        raise APIError(
            message="Login failed",
            code="LOGIN_FAILED",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value
        )


@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        schema = RegistrationSchema()
        data = schema.load(request.json)

        user = User(
            email=data['email'],
            password=data['password'],
            first_name=data['first_name'],
            last_name=data['last_name']
        )

        db.session.add(user)
        db.session.commit()

        return {
            "message": "Registration successful",
            "user": {
                "id": user.user_id,
                "email": user.email
            }
        }, HTTPStatus.CREATED.value

    except ValidationError as err:
        raise APIError(
            message="Invalid registration data",
            code="VALIDATION_ERROR",
            status_code=HTTPStatus.BAD_REQUEST.value,
        )
    except IntegrityError:
        db.session.rollback()
        raise APIError(
            message="Email already registered",
            code="EMAIL_EXISTS",
            status_code=HTTPStatus.BAD_REQUEST.value
        )
    except Exception as err:
        db.session.rollback()
        raise APIError(
            message="Registration failed",
            code="REGISTRATION_FAILED",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value
        )


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh_access_token():
    try:
        identity = get_jwt_identity()
        new_access_token = create_access_token(identity=identity)
        return {"access_token": new_access_token}, HTTPStatus.OK.value
    except Exception as err:
        raise APIError(
            message="Token refresh failed",
            code="REFRESH_FAILED",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value
        )


@auth_bp.route('/logout', methods=['POST'])
@jwt_required(verify_type=False)
def logout():
    try:
        jwt = get_jwt()
        jti = jwt['jti']
        token_type = jwt['type']

        token_block = TokenBlockList(jti=jti)
        token_block.save()

        return {
            "message": f"{token_type} token revoked successfully"
        }, HTTPStatus.OK.value
    except Exception as err:
        raise APIError(
            message="Logout failed",
            code="LOGOUT_FAILED",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value
        )