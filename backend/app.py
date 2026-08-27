from flask import Flask, jsonify, request
from flask_cors import CORS
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from blueprints.artworks import artworks_bp
from blueprints.admin import admin_bp
from blueprints.auth import auth_bp
from config import Config
from extensions import jwt, mongo
from ml_model.inference import warm_model
from services.blockchain_service import BlockchainService
from services.ipfs_service import IpfsService


def create_app(config_class=Config):
    validator = getattr(config_class, 'validate_for_production', None)
    if validator:
        validator()
    application = Flask(__name__)
    application.config.from_object(config_class)
    CORS(application, resources={r'/api/*': {'origins': '*'}})
    if not application.config.get('TESTING'):
        try:
            warm_model(application.config['MODEL_PATH'])
        except (FileNotFoundError, RuntimeError, OSError) as error:
            application.logger.warning('AI detector warm-up skipped: %s', error)
    mongo.init_app(application)
    jwt.init_app(application)
    application.config['UPLOAD_DIR'].mkdir(parents=True, exist_ok=True)
    application.extensions['ipfs_service'] = IpfsService(
        application.config['IPFS_API_URL'],
        origin=application.config['FRONTEND_ORIGIN'],
    )
    application.extensions['blockchain_service'] = BlockchainService(
        application.config['BLOCKCHAIN_RPC_URL'],
        application.config['CONTRACT_ADDRESS'],
        application.config['BLOCKCHAIN_PRIVATE_KEY'],
    )
    application.register_blueprint(auth_bp)
    application.register_blueprint(artworks_bp)
    application.register_blueprint(admin_bp)

    @application.get('/health')
    def health():
        return jsonify({'status': 'ok', 'service': 'digital-art-protection-api'})

    @application.after_request
    def add_cors_headers(response):
        request_origin = request.headers.get('Origin', '')
        allowed_origins = {
            application.config['FRONTEND_ORIGIN'],
            'http://localhost:5173',
            'http://localhost:5174',
            'http://127.0.0.1:5173',
            'http://127.0.0.1:5174',
        }
        response.headers['Access-Control-Allow-Origin'] = (
            request_origin if request_origin in allowed_origins else application.config['FRONTEND_ORIGIN']
        )
        response.headers.setdefault('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        response.headers.setdefault('Access-Control-Allow-Methods', 'GET, POST, PATCH, DELETE, OPTIONS')
        return response

    return application


app = create_app()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
