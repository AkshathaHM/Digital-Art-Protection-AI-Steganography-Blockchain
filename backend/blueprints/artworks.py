import hashlib
from io import BytesIO
from datetime import datetime, timezone
from pathlib import Path

from bson import ObjectId
from flask import Blueprint, current_app, jsonify, request, send_file
import requests
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from PIL import Image
from werkzeug.utils import secure_filename
from web3 import Web3

from extensions import mongo
from ml_model.inference import predict_image
from steganography import compute_phash, embed_watermark, extract_watermark, is_near_duplicate

artworks_bp = Blueprint('artworks', __name__, url_prefix='/api')


def _role_required(role):
    return get_jwt().get('role') == role


def _artworks():
    return mongo.db.artworks


@artworks_bp.get('/gallery')
@jwt_required()
def gallery():
    if not _role_required('buyer'):
        return jsonify({'error': 'buyer access required'}), 403
    documents = _artworks().find({'ai_classification': 'Human', 'verified': True}).sort('created_at', -1)
    return jsonify([_public_artwork(document) for document in documents])


@artworks_bp.get('/my-artworks')
@jwt_required()
def my_artworks():
    if not _role_required('artist'):
        return jsonify({'error': 'artist access required'}), 403
    documents = _artworks().find({'artist_id': get_jwt_identity()}).sort('created_at', -1)
    return jsonify([_public_artwork(document) for document in documents])


@artworks_bp.get('/my-purchases')
@jwt_required()
def my_purchases():
    if not _role_required('buyer'):
        return jsonify({'error': 'buyer access required'}), 403
    documents = _artworks().find({'buyer_id': get_jwt_identity(), 'is_sold': True}).sort('created_at', -1)
    return jsonify([_public_artwork(document) for document in documents])


@artworks_bp.get('/recommendations')
@jwt_required()
def recommendations():
    if not _role_required('buyer'):
        return jsonify({'error': 'buyer access required'}), 403
    source_hash = request.args.get('hash', '').strip()
    artwork_id = request.args.get('artwork_id')
    if artwork_id and not source_hash:
        source = _find_artwork(artwork_id)
        source_hash = source.get('content_hash', '') if source else ''
    if not source_hash:
        return jsonify({'error': 'hash or artwork_id is required'}), 400
    try:
        int(source_hash, 16)
    except ValueError:
        return jsonify({'error': 'hash must be hexadecimal'}), 400
    matches = []
    for document in _artworks().find({'ai_classification': 'Human', 'verified': True}):
        candidate_hash = document.get('content_hash')
        if candidate_hash:
            try:
                matches.append((is_near_duplicate(source_hash, candidate_hash), _hamming_distance(source_hash, candidate_hash), document))
            except ValueError:
                continue
    matches.sort(key=lambda item: item[1])
    return jsonify([_public_artwork(document) | {'similarity_distance': distance} for _, distance, document in matches[:12]])


@artworks_bp.post('/upload')
@jwt_required()
def upload():
    if not _role_required('artist'):
        return jsonify({'error': 'artist access required'}), 403
    image_file = request.files.get('image')
    if image_file is None or not image_file.filename:
        return jsonify({'error': 'image file is required'}), 400
    extension = image_file.filename.rsplit('.', 1)[-1].lower() if '.' in image_file.filename else ''
    if extension not in current_app.config['ALLOWED_IMAGE_EXTENSIONS']:
        return jsonify({'error': 'unsupported image type'}), 415

    upload_id = f'{datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")}_{secure_filename(image_file.filename)}'
    original_path = current_app.config['UPLOAD_DIR'] / f'original_{upload_id}'
    watermarked_path = current_app.config['UPLOAD_DIR'] / f'watermarked_{upload_id}'
    artwork_id = None
    image_file.save(original_path)
    try:
        classification = predict_image(original_path, current_app.config['MODEL_PATH'])
        if classification == 'AI':
            return jsonify({'accepted': False, 'classification': 'AI', 'message': 'AI-generated images are not accepted'}), 422

        artist_id = get_jwt_identity()
        created_at = datetime.now(timezone.utc)
        artist = mongo.db.users.find_one({'_id': ObjectId(artist_id)}, {'username': 1})
        username = artist.get('username', '') if artist else ''
        pending = {
            'title': request.form.get('title', '').strip() or Path(image_file.filename).stem,
            'artist_id': artist_id,
            'owner': artist_id,
            'ai_classification': 'Human',
            'verified': False,
            'created_at': created_at,
        }
        artwork_id = _artworks().insert_one(pending).inserted_id
        watermark = f'{artist_id}:{created_at.isoformat()}:{artwork_id}'
        with Image.open(original_path) as image:
            watermarked = embed_watermark(image, watermark)
            watermarked.save(watermarked_path, format='PNG')
            content_hash = compute_phash(image)
        watermark_hash = hashlib.sha256(watermark.encode('utf-8')).hexdigest()
        duplicate = _find_duplicate(content_hash)
        if duplicate:
            _artworks().delete_one({'_id': artwork_id})
            return jsonify({'accepted': False, 'error': 'near-duplicate artwork already exists', 'existing_artwork_id': str(duplicate['_id'])}), 409

        ipfs = current_app.extensions['ipfs_service']
        clean_cid = ipfs.add_file(original_path)
        watermarked_cid = ipfs.add_file(watermarked_path)
        price_wei = _price_to_wei(request.form.get('price', '0'))
        price_wei = _mongo_integer(price_wei, 'price')
        blockchain = current_app.extensions['blockchain_service']
        registration = blockchain.register_artwork(
            watermarked_cid,
            watermark_hash,
            price_wei,
            username=username,
            timestamp=int(created_at.timestamp()),
            perceptual_hash=content_hash,
        )
        blockchain_artwork_id = _mongo_integer(registration['artwork_id'], 'blockchain artwork')
        _artworks().update_one({'_id': artwork_id}, {'$set': {
            'content_hash': content_hash,
            'watermark': watermark,
            'watermark_hash': watermark_hash,
            'ipfs_cid': watermarked_cid,
            'clean_ipfs_cid': clean_cid,
            'blockchain_artwork_id': blockchain_artwork_id,
            'blockchain_transaction': registration['transaction_hash'],
            'price_wei': price_wei,
            'price': request.form.get('price', '0'),
            'verified': True,
        }})
        return jsonify({
            'accepted': True,
            'classification': 'Human',
            'message': 'Human artwork accepted and stored on IPFS and blockchain',
            'artwork_id': str(artwork_id),
            'ipfs_cid': watermarked_cid,
            'clean_ipfs_cid': clean_cid,
            'blockchain_artwork_id': blockchain_artwork_id,
        }), 201
    except (FileNotFoundError, RuntimeError, ValueError, OSError, requests.RequestException) as error:
        if artwork_id is not None:
            _artworks().delete_one({'_id': artwork_id, 'verified': False})
        return jsonify({'error': str(error)}), 503
    except Exception:
        if artwork_id is not None:
            _artworks().delete_one({'_id': artwork_id, 'verified': False})
        current_app.logger.exception('Unexpected artwork upload failure')
        return jsonify({'error': 'upload failed inside the server; check the Flask terminal for details'}), 503
    finally:
        original_path.unlink(missing_ok=True)
        watermarked_path.unlink(missing_ok=True)


@artworks_bp.post('/verify-ownership')
@jwt_required()
def verify_ownership():
    if not _role_required('buyer'):
        return jsonify({'error': 'buyer access required'}), 403
    payload = request.get_json(silent=True) or {}
    artwork = _find_artwork(payload.get('artwork_id'))
    if artwork is None:
        return jsonify({'error': 'artwork not found'}), 404
    try:
        watermark = artwork.get('watermark', '')
        image_bytes = current_app.extensions['ipfs_service'].read_file(artwork['ipfs_cid'])
        extracted_watermark = extract_watermark(Image.open(BytesIO(image_bytes)))
        watermark_valid = extracted_watermark == watermark and hashlib.sha256(extracted_watermark.encode('utf-8')).hexdigest() == artwork.get('watermark_hash')
        blockchain = current_app.extensions['blockchain_service']
        blockchain_owner = blockchain.ownership(artwork.get('blockchain_artwork_id')) if artwork.get('blockchain_artwork_id') is not None else None
        if blockchain_owner is None and watermark_valid and artwork.get('content_hash') and artwork.get('ipfs_cid'):
            registration = blockchain.register_existing_artwork(artwork)
            blockchain_artwork_id = _mongo_integer(registration['artwork_id'], 'blockchain artwork')
            _artworks().update_one({'_id': artwork['_id']}, {'$set': {
                'blockchain_artwork_id': blockchain_artwork_id,
                'blockchain_transaction': registration['transaction_hash'],
                'verified': True,
            }})
            artwork['blockchain_artwork_id'] = blockchain_artwork_id
            blockchain_owner = blockchain.ownership(blockchain_artwork_id)
        blockchain_valid = blockchain_owner is not None and blockchain_owner[6] == artwork.get('content_hash')
        return jsonify({'verified': watermark_valid and blockchain_valid, 'watermark': extracted_watermark, 'owner': blockchain_owner[0] if blockchain_owner else None, 'artist': blockchain_owner[1] if blockchain_owner else None, 'blockchain': blockchain_valid})
    except (KeyError, RuntimeError, TypeError, ValueError) as error:
        return jsonify({'error': str(error)}), 503


@artworks_bp.post('/purchase')
@jwt_required()
def purchase():
    if not _role_required('buyer'):
        return jsonify({'error': 'buyer access required'}), 403
    payload = request.get_json(silent=True) or {}
    artwork = _find_artwork(payload.get('artwork_id'))
    transaction_hash = payload.get('transaction_hash')
    if artwork is None:
        return jsonify({'error': 'artwork not found'}), 404
    if not transaction_hash:
        return jsonify({'error': 'transaction_hash is required after wallet payment'}), 400
    try:
        blockchain = current_app.extensions['blockchain_service']
        buyer = payload.get('buyer_address', '').strip()
        if not buyer or not Web3.is_address(buyer):
            return jsonify({'error': 'buyer_address is required'}), 400
        if artwork.get('purchase_transaction') == transaction_hash:
            return jsonify({'error': 'transaction already processed'}), 409
        if not blockchain.validate_purchase(transaction_hash, artwork['blockchain_artwork_id'], buyer, artwork.get('price_wei', 0)):
            return jsonify({'error': 'blockchain transaction failed'}), 422
        ownership = blockchain.ownership(artwork['blockchain_artwork_id'])
        _artworks().update_one({'_id': artwork['_id']}, {'$set': {'owner': ownership[0], 'is_sold': ownership[5], 'buyer_id': get_jwt_identity(), 'purchase_transaction': transaction_hash}})
        clean_cid = artwork.get('clean_ipfs_cid')
        clean_url = f"{current_app.config['IPFS_GATEWAY_URL'].rstrip('/')}/{clean_cid}" if clean_cid else None
        return jsonify({'message': 'ownership transferred', 'owner': ownership[0], 'clean_ipfs_cid': clean_cid, 'clean_ipfs_url': clean_url})
    except (RuntimeError, TypeError, ValueError) as error:
        return jsonify({'error': str(error)}), 503


@artworks_bp.get('/artworks/<identifier>/download')
@jwt_required()
def download_original(identifier):
    if not _role_required('buyer'):
        return jsonify({'error': 'buyer access required'}), 403
    artwork = _find_artwork(identifier)
    if artwork is None:
        return jsonify({'error': 'artwork not found'}), 404
    if not artwork.get('is_sold'):
        blockchain_owner = current_app.extensions['blockchain_service'].ownership(artwork.get('blockchain_artwork_id'))
        if not blockchain_owner or not blockchain_owner[5]:
            return jsonify({'error': 'the clean original is available after purchase'}), 403
        _artworks().update_one({'_id': artwork['_id']}, {'$set': {'is_sold': True, 'owner': blockchain_owner[0]}})
    clean_cid = artwork.get('clean_ipfs_cid')
    if not clean_cid:
        return jsonify({'error': 'clean original is unavailable'}), 404
    try:
        content = current_app.extensions['ipfs_service'].read_file(clean_cid)
        return send_file(BytesIO(content), mimetype='image/png', as_attachment=True, download_name=f"{artwork.get('title') or 'artwork'}.png")
    except (KeyError, RuntimeError, OSError, requests.RequestException) as error:
        return jsonify({'error': str(error)}), 503


def _find_artwork(identifier):
    if not identifier:
        return None
    try:
        if ObjectId.is_valid(identifier):
            document = _artworks().find_one({'_id': ObjectId(identifier)})
            if document:
                return document
    except (TypeError, ValueError):
        pass
    try:
        return _artworks().find_one(
            {'blockchain_artwork_id': int(identifier)},
            sort=[('created_at', -1)],
        )
    except (TypeError, ValueError):
        return None


def _find_duplicate(content_hash):
    for document in _artworks().find({'verified': True}, {'content_hash': 1}):
        if document.get('content_hash') and is_near_duplicate(content_hash, document['content_hash']):
            return document
    return None


def _price_to_wei(value):
    try:
        return Web3.to_wei(value or '0', 'ether')
    except (TypeError, ValueError):
        raise ValueError('price must be a valid ETH amount')


def _mongo_integer(value, name):
    normalized = int(value)
    if normalized < 0 or normalized > 9223372036854775807:
        raise ValueError(f'{name} is outside MongoDB integer limits')
    return normalized


def _public_artwork(document):
    return {
        'id': str(document['_id']),
        'blockchain_artwork_id': document.get('blockchain_artwork_id'),
        'title': document.get('title'),
        'artist_id': document.get('artist_id'),
        'ipfs_cid': document.get('ipfs_cid'),
        'ipfs_url': f"{current_app.config['IPFS_GATEWAY_URL'].rstrip('/')}/{document['ipfs_cid']}" if document.get('ipfs_cid') else None,
        'content_hash': document.get('content_hash'),
        'watermark_hash': document.get('watermark_hash'),
        'price': document.get('price'),
        'owner': document.get('owner'),
        'verified': document.get('verified', False),
    }


def _hamming_distance(first_hash, second_hash):
    return (int(first_hash, 16) ^ int(second_hash, 16)).bit_count()
