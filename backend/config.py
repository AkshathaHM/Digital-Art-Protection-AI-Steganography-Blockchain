import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent


class Config:
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'change-me-in-production')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'change-me-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=12)
    PASSWORD_RESET_RETURN_TOKEN = os.getenv('PASSWORD_RESET_RETURN_TOKEN', 'false').lower() == 'true'
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/digital_art_protection')
    MONGO_DB_NAME = os.getenv('MONGO_DB_NAME', 'digital_art_protection')
    IPFS_API_URL = os.getenv('IPFS_API_URL', 'http://127.0.0.1:5001/api/v0')
    IPFS_GATEWAY_URL = os.getenv('IPFS_GATEWAY_URL', 'http://127.0.0.1:8080/ipfs')
    FRONTEND_ORIGIN = os.getenv('FRONTEND_ORIGIN', 'http://localhost:5173')
    BLOCKCHAIN_RPC_URL = os.getenv('BLOCKCHAIN_RPC_URL', 'http://127.0.0.1:7545')
    CONTRACT_ADDRESS = os.getenv('CONTRACT_ADDRESS', '')
    BLOCKCHAIN_PRIVATE_KEY = os.getenv('BLOCKCHAIN_PRIVATE_KEY', '')
    BLOCKCHAIN_ACCOUNT = os.getenv('BLOCKCHAIN_ACCOUNT', '')
    MODEL_PATH = os.getenv('MODEL_PATH', str(BASE_DIR.parent / 'ml_model' / 'vgg16_ai_detector.h5'))
    UPLOAD_DIR = Path(os.getenv('UPLOAD_DIR', str(BASE_DIR / 'uploads')))
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_UPLOAD_BYTES', str(25 * 1024 * 1024)))
    ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp'}

    @classmethod
    def validate_for_production(cls):
        if os.getenv('FLASK_ENV', '').lower() != 'production':
            return
        required = {
            'FLASK_SECRET_KEY': cls.SECRET_KEY,
            'JWT_SECRET_KEY': cls.JWT_SECRET_KEY,
            'BLOCKCHAIN_PRIVATE_KEY': cls.BLOCKCHAIN_PRIVATE_KEY,
            'CONTRACT_ADDRESS': cls.CONTRACT_ADDRESS,
        }
        placeholders = {'', 'change-me-in-production', 'replace-after-deployment'}
        missing = [name for name, value in required.items() if value in placeholders]
        if missing:
            raise RuntimeError(f'Production secrets/configuration are missing: {", ".join(missing)}')
        if cls.BLOCKCHAIN_RPC_URL.startswith(('http://127.0.0.1', 'http://localhost')):
            raise RuntimeError('Production blockchain RPC must not point to local Ganache')
