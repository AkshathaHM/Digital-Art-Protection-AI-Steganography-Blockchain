from datetime import datetime, timedelta, timezone
import hashlib
import secrets

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt, jwt_required
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import mongo

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


def _users():
    return mongo.db.users


def _register(role):
    payload = request.get_json(silent=True) or {}
    email = payload.get('email', '').strip().lower()
    password = payload.get('password', '')
    username = payload.get('username', '').strip()
    if not email or not password or not username:
        return jsonify({'error': 'username, email, and password are required'}), 400
    if len(password) < 8:
        return jsonify({'error': 'password must be at least 8 characters'}), 400
    if _users().find_one({'email': email}):
        return jsonify({'error': 'email is already registered'}), 409

    user = {
        'username': username,
        'email': email,
        'password_hash': generate_password_hash(password),
        'role': role,
        'created_at': datetime.now(timezone.utc),
    }
    result = _users().insert_one(user)
    return jsonify({'message': 'user registered', 'user_id': str(result.inserted_id)}), 201


@auth_bp.post('/register')
def register():
    return _register('artist')


@auth_bp.post('/register/artist')
def register_artist():
    return _register('artist')


@auth_bp.post('/register/buyer')
def register_buyer():
    return _register('buyer')


@auth_bp.get('/profile')
@jwt_required()
def profile():
    user = _users().find_one({'_id': __import__('bson').ObjectId(get_jwt()['sub'])}, {'password_hash': 0})
    if user is None:
        return jsonify({'error': 'user not found'}), 404
    user['id'] = str(user.pop('_id'))
    return jsonify(user)


@auth_bp.post('/login')
def login():
    payload = request.get_json(silent=True) or {}
    email = payload.get('email', '').strip().lower()
    password = payload.get('password', '')
    user = _users().find_one({'email': email})
    if not user or user.get('disabled', False) or not check_password_hash(user['password_hash'], password):
        return jsonify({'error': 'invalid credentials'}), 401
    token = create_access_token(identity=str(user['_id']), additional_claims={'role': user['role']})
    return jsonify({'access_token': token, 'user': {'id': str(user['_id']), 'username': user['username'], 'email': user['email'], 'role': user['role']}})


@auth_bp.post('/forgot-password')
def forgot_password():
    payload = request.get_json(silent=True) or {}
    email = payload.get('email', '').strip().lower()
    user = _users().find_one({'email': email})
    response = {'message': 'If an account exists for that email, password reset instructions have been created.'}
    if user is None:
        return jsonify(response)
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode('utf-8')).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)
    mongo.db.password_resets.delete_many({'user_id': str(user['_id'])})
    mongo.db.password_resets.insert_one({'user_id': str(user['_id']), 'token_hash': token_hash, 'expires_at': expires_at, 'used': False})
    if current_app.config.get('TESTING') or current_app.config.get('PASSWORD_RESET_RETURN_TOKEN', False):
        response['reset_token'] = raw_token
    return jsonify(response)


@auth_bp.post('/reset-password')
def reset_password():
    payload = request.get_json(silent=True) or {}
    raw_token = payload.get('token', '')
    password = payload.get('password', '')
    if len(password) < 8:
        return jsonify({'error': 'password must be at least 8 characters'}), 400
    token_hash = hashlib.sha256(raw_token.encode('utf-8')).hexdigest()
    reset = mongo.db.password_resets.find_one({'token_hash': token_hash, 'used': False})
    if reset is None or reset['expires_at'] < datetime.now(timezone.utc):
        return jsonify({'error': 'reset link is invalid or expired'}), 400
    result = _users().update_one({'_id': __import__('bson').ObjectId(reset['user_id'])}, {'$set': {'password_hash': generate_password_hash(password)}})
    if result.matched_count != 1:
        return jsonify({'error': 'user not found'}), 404
    mongo.db.password_resets.update_one({'_id': reset['_id']}, {'$set': {'used': True, 'used_at': datetime.now(timezone.utc)}})
    return jsonify({'message': 'password reset successful'})
