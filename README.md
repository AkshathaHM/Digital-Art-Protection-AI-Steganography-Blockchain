# Protecting Digital Art Through Steganography and Blockchain

A full-stack platform for human-created digital art verification, DCT watermarking, duplicate detection, IPFS storage, and Ethereum ownership records.

## Repository layout

- `frontend/` React client
- `backend/` Flask API
- `blockchain/` Solidity contracts and local-chain configuration
- `ml_model/` VGG16 training and inference
- `steganography/` DCT watermarking and perceptual hashing

## Technology baseline

React, Flask, VGG16, DCT steganography, perceptual hashing, IPFS, Ethereum/Hardhat, MongoDB, Web3.py, and ethers.js.

## Account roles

Registration uses separate Artist and Buyer entry points; there is no role selector inside either form. Artists can upload and manage their own work. Buyers can browse watermarked gallery images, verify ownership, purchase work, and download originals after successful purchase. The backend enforces these role boundaries in addition to the frontend route guards.

## Local setup

Use Python 3.12 for the backend and ML modules. TensorFlow and a trained model are required before uploads can be accepted.

### 1. Start MongoDB, Ganache, and IPFS

With Docker Desktop running, from the project root:

```powershell
docker compose up -d mongodb ganache ipfs
```

Ganache stores its chain database in the named `ganache-data` volume. Keep that volume when restarting Docker; deleting it resets the chain and makes existing MongoDB artwork records point at a different blockchain state.

### 2. Deploy the local blockchain

Open a new terminal:

```powershell
cd d:\Projects\Academic\digital-art-protection\blockchain
npm install
npm run deploy:ganache
```

The persistent Ganache service provides chain ID `1337` at `http://127.0.0.1:7545`. The deployment address is written to `blockchain/deployments/ganache.json`.

### 3. Configure the Flask API

Open a new terminal:

```powershell
cd d:\Projects\Academic\digital-art-protection\backend
Copy-Item ..\.env.example .env
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Edit `backend/.env` and set `BLOCKCHAIN_PRIVATE_KEY` to a local Ganache account key. Keep `BLOCKCHAIN_RPC_URL` at `http://127.0.0.1:7545` and set the deployed contract address.

Before production deployment, replace both Flask/JWT secrets, the contract address, RPC URL, and wallet key with production values supplied by a secret manager. Do not commit `.env` files or reuse any Ganache account key.

Train the model before starting uploads, following the ML instructions below. Then start Flask:

```powershell
flask --app app run --debug --port 5000
```

Check it at `http://localhost:5000/health`.

### 4. Start React

Open another terminal:

```powershell
cd d:\Projects\Academic\digital-art-protection\frontend
Copy-Item .env.example .env
npm install
npm run dev
```

Open `http://localhost:5173` (or the alternate Vite port shown in the terminal).

### 5. Train the VGG16 detector

Put labeled images in `ml_model/data/train/Human`, `ml_model/data/train/AI`, `ml_model/data/validation/Human`, and `ml_model/data/validation/AI`. In a Python 3.12 environment:

```powershell
cd d:\Projects\Academic\digital-art-protection\ml_model
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m training.train --data-dir data --output vgg16_ai_detector.h5 --epochs 10
```

The generated file must be at `ml_model/vgg16_ai_detector.h5`, matching the backend configuration.

### 6. Optional MetaMask setup

Add a custom network with RPC `http://127.0.0.1:7545`, chain ID `1337`, and currency symbol `ETH`. Import one funded account using a key shown by Ganache. Never use these development keys outside the local chain.

## Planned local services

- React: `http://localhost:5173`
- Flask API: `http://localhost:5000`
- MongoDB: `mongodb://localhost:27017/digital_art_protection`
- Ganache JSON-RPC: `http://localhost:7545` (chain ID `1337`, persistent `ganache-data` volume)
- IPFS API: `http://localhost:5001`

See each module's README for module-specific setup instructions.
