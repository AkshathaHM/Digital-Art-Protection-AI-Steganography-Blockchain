from io import BytesIO
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest
from flask_jwt_extended import create_access_token

sys.path.insert(0, str(Path(__file__).parents[1]))

from app import create_app


class TestConfig:
    TESTING = True
    SECRET_KEY = 'test-secret-with-at-least-32-bytes'
    JWT_SECRET_KEY = 'test-jwt-secret-with-at-least-32-bytes'
    MONGO_URI = 'mongodb://localhost:27017/digital_art_protection_test'
    MONGO_DB_NAME = 'digital_art_protection_test'
    UPLOAD_DIR = Path('uploads')
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
    FRONTEND_ORIGIN = 'http://localhost:5174'
    IPFS_API_URL = 'http://ipfs/api/v0'
    IPFS_GATEWAY_URL = 'http://ipfs/ipfs'
    BLOCKCHAIN_RPC_URL = 'http://blockchain:7545'
    CONTRACT_ADDRESS = ''
    BLOCKCHAIN_PRIVATE_KEY = ''


@pytest.fixture
def client(monkeypatch):
    app = create_app(TestConfig)
    app.extensions['blockchain_service'] = Mock()
    app.extensions['ipfs_service'] = Mock()
    yield app.test_client()


def test_health(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json['status'] == 'ok'


def test_upload_requires_authentication(client):
    response = client.post('/api/upload', data={'image': (BytesIO(b'not-an-image'), 'art.png')})
    assert response.status_code == 401


def test_verify_returns_not_found_for_unknown_artwork(client, monkeypatch):
    monkeypatch.setattr('blueprints.artworks._find_artwork', lambda identifier: None)
    with client.application.app_context():
        token = create_access_token(identity='buyer-1', additional_claims={'role': 'buyer'})
    response = client.post('/api/verify-ownership', json={'artwork_id': 'missing'}, headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 404
    assert response.json == {'error': 'artwork not found'}


def test_purchase_rejects_unknown_artwork(client, monkeypatch):
    monkeypatch.setattr('blueprints.artworks._find_artwork', lambda identifier: None)
    with client.application.app_context():
        token = create_access_token(identity='buyer-1', additional_claims={'role': 'buyer'})
    response = client.post('/api/purchase', json={'artwork_id': 'missing'}, headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 404
    assert response.json == {'error': 'artwork not found'}


def test_download_requires_authentication(client):
    response = client.get('/api/artworks/0/download')
    assert response.status_code == 401