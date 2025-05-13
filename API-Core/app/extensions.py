# Extensions init: db, jwt, cors configs
import os

from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from datetime import timedelta
from dotenv import load_dotenv

#db
from flask_sqlalchemy import SQLAlchemy

load_dotenv()

db= SQLAlchemy() #new sqlAlchemy object
migrate = Migrate()
cors= CORS()
jwt = JWTManager()

def init_app(app):
    db.init_app(app)
    migrate.init_app(app, db) #to initialize migrations with app and db

def init_jwt(app):
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
    print(f"🔑 ACTUAL JWT SECRET: {app.config['JWT_SECRET_KEY']}")
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
    app.config['JWT_COOKIE_CSRF_PROTECT'] = False
    app.config['JWT_CSRF_CHECK_FORM'] = False
    jwt.init_app(app)

    from .models import User#importing here to avoid circular import err

    #add user identity loader
    @jwt.user_identity_loader
    def user_identity_lookup(user_id):
        return user_id

    #adding claims to tokens
    @jwt.additional_claims_loader
    def add_claims_to_access_token(identity):
        user = User.query.get(identity)
        return {
            'is_admin': user.is_admin,
            'email': user.email,
            'status': user.account_status.value
        }

    @jwt.unauthorized_loader
    def unauthorized_callback(reason):
        print(f"❌ Unauthorized: {reason}")
        return {"error": "Missing Authorization Header"}, 401

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        print("⏰ Token expired")
        return {"error": "Token expired"}, 401

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        print("🔁 Token revoked")
        return {"error": "Token revoked"}, 401

    # @jwt.user_lookup_loader
    # def user_lookup_callback(_jwt_header, jwt_data):
    #     try:
    #         identity = jwt_data["sub"]
    #         return User.query.get(identity)
    #     except Exception as e:
    #         print(f"🔥 User lookup failed: {str(e)}")
    #         return None
    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        try:
            user = User.query.get(jwt_data["sub"])
            if not user:
                print(f"❌ User {jwt_data['sub']} not found in database")
                return None  # This triggers 'invalid token'
            return user
        except Exception as e:
            print(f"🔥 Database error: {str(e)}")
            return None

    @jwt.invalid_token_loader
    def invalid_token_callback(reason):
        print(f"❌ Invalid token details: {reason}")
        return {"error": "Invalid token"}, 422
