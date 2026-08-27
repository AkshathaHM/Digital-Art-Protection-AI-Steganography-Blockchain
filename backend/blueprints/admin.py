from bson import ObjectId
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, jwt_required

from extensions import mongo

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')


def _admin_required():
    return get_jwt().get('role') == 'admin'


@admin_bp.get('/users')
@jwt_required()
def users():
    if not _admin_required():
        return jsonify({'error': 'admin access required'}), 403
    return jsonify([{
        'id': str(user['_id']),
        'username': user.get('username'),
        'email': user.get('email'),
        'role': user.get('role', 'artist'),
        'disabled': user.get('disabled', False),
        'created_at': user.get('created_at').isoformat() if user.get('created_at') else None,
    } for user in mongo.db.users.find().sort('created_at', -1)])


@admin_bp.patch('/users/<user_id>')
@jwt_required()
def update_user(user_id):
    if not _admin_required():
        return jsonify({'error': 'admin access required'}), 403
    if not ObjectId.is_valid(user_id):
        return jsonify({'error': 'invalid user id'}), 400
    payload = request.get_json(silent=True) or {}
    update = {}
    if payload.get('role') in {'artist', 'buyer', 'admin'}:
        update['role'] = payload['role']
    if isinstance(payload.get('disabled'), bool):
        update['disabled'] = payload['disabled']
    if not update:
        return jsonify({'error': 'role or disabled is required'}), 400
    mongo.db.users.update_one({'_id': ObjectId(user_id)}, {'$set': update})
    return jsonify({'message': 'user updated'})


@admin_bp.delete('/users/<user_id>')
@jwt_required()
def delete_user(user_id):
    if not _admin_required():
        return jsonify({'error': 'admin access required'}), 403
    if not ObjectId.is_valid(user_id):
        return jsonify({'error': 'invalid user id'}), 400
    mongo.db.users.delete_one({'_id': ObjectId(user_id)})
    mongo.db.artworks.delete_many({'artist_id': user_id})
    return jsonify({'message': 'user and authored artworks removed'})


@admin_bp.get('/artworks')
@jwt_required()
def artworks():
    if not _admin_required():
        return jsonify({'error': 'admin access required'}), 403
    return jsonify([{
        'id': str(artwork['_id']),
        'title': artwork.get('title'),
        'artist_id': artwork.get('artist_id'),
        'verified': artwork.get('verified', False),
        'ai_classification': artwork.get('ai_classification'),
        'ipfs_cid': artwork.get('ipfs_cid'),
    } for artwork in mongo.db.artworks.find().sort('created_at', -1)])


@admin_bp.delete('/artworks/<artwork_id>')
@jwt_required()
def delete_artwork(artwork_id):
    if not _admin_required():
        return jsonify({'error': 'admin access required'}), 403
    if not ObjectId.is_valid(artwork_id):
        return jsonify({'error': 'invalid artwork id'}), 400
    mongo.db.artworks.delete_one({'_id': ObjectId(artwork_id)})
    return jsonify({'message': 'artwork removed'})
