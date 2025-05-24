from flask import Blueprint, request
from http import HTTPStatus
from ...errors import APIError
from ...decorators.auth import admin_required
from ...extensions import db
from ...models import User

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/users', methods=['GET'])
@admin_required
def list_users():
    try:
        users = User.query.all()
        return [user.to_admin_dict() for user in users], HTTPStatus.OK.value
    except Exception as e:
        raise APIError(
            message="Failed to retrieve users",
            code="USER_RETRIEVAL_FAILED",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value
        )

@admin_bp.route('/users/<int:user_id>/ban', methods=['PATCH'])
@admin_required
def toggle_ban(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            raise APIError(
                message="User not found",
                code="USER_NOT_FOUND",
                status_code=HTTPStatus.NOT_FOUND.value
            )

        data = request.get_json()
        if not data or 'banned' not in data:
            raise APIError(
                message="Missing 'banned' status in request",
                code="MISSING_STATUS",
                status_code=HTTPStatus.BAD_REQUEST.value
            )

        if data.get('banned'):
            if not data.get('reason'):
                raise APIError(
                    message="Ban reason is required",
                    code="MISSING_REASON",
                    status_code=HTTPStatus.BAD_REQUEST.value
                )
            user.ban_user(reason=data.get('reason'))
        else:
            user.unban_user()

        db.session.commit()
        return user.to_admin_dict(), HTTPStatus.OK.value

    except ValueError as e:
        db.session.rollback()
        raise APIError(
            message=str(e),
            code="INVALID_OPERATION",
            status_code=HTTPStatus.BAD_REQUEST.value
        )
    except Exception as e:
        db.session.rollback()
        raise APIError(
            message="Failed to update user status",
            code="USER_UPDATE_FAILED",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value
        )