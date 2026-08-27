# Backend

Flask API boundary for authentication, image analysis, watermarking, IPFS uploads, gallery queries, and blockchain transactions.

## Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
flask --app app run --debug --port 5000
```

Copy the repository `.env.example` to `.env` and set non-default secrets before exposing the API beyond local development.
For production, provide independently generated `FLASK_SECRET_KEY` and `JWT_SECRET_KEY`, a production RPC endpoint, contract address, and wallet key through a secret manager. The API refuses placeholder values when `FLASK_ENV=production`; never reuse Ganache accounts or keys in production.
For local testing, `PASSWORD_RESET_RETURN_TOKEN=true` returns the reset token in the response. Set it to `false` in production and connect the endpoint to your email provider before deploying.

## Routes

- `POST /api/auth/register`
- `POST /api/auth/register/artist`
- `POST /api/auth/register/buyer`
- `POST /api/auth/login`
- `POST /api/auth/forgot-password` (creates a 30-minute reset token)
- `POST /api/auth/reset-password` (consumes a reset token once)
- `POST /api/upload` (artist JWT required; pipeline enabled in Steps 3-5)
- `GET /api/gallery` (buyer JWT required; returns watermarked images only)
- `POST /api/verify-ownership` (buyer JWT required)
- `POST /api/purchase` (buyer JWT required; enabled with the deployed contract)
- `GET /api/artworks/<identifier>/download` (requires JWT; available after purchase)
- `GET /api/my-artworks` (artist JWT required)
- `GET /api/my-purchases` (buyer JWT required)
- `GET /health`

## Integrated upload flow

`POST /api/upload` accepts an authenticated multipart image, runs VGG16 inference, rejects an `AI` result, creates a DCT watermark, computes a pHash, rejects near-duplicates, uploads both watermarked and clean files to IPFS, registers the watermarked CID on `DigitalArt`, and persists the provenance record in MongoDB.

Set `MODEL_PATH`, `CONTRACT_ADDRESS`, and `BLOCKCHAIN_PRIVATE_KEY` in `.env`. Ganache, MongoDB, IPFS, and the trained model must be available for a successful upload.

Admin endpoints require a JWT whose role is `admin`:

- `GET /api/admin/users`
- `PATCH /api/admin/users/<id>` with `{ "disabled": true }` or `{ "role": "admin" }`
- `DELETE /api/admin/users/<id>`
- `GET /api/admin/artworks`
- `DELETE /api/admin/artworks/<id>`

Promote a local user with MongoDB Compass or `mongosh`:

```javascript
use digital_art_protection
db.users.updateOne({ email: "admin@example.com" }, { $set: { role: "admin" } })
```
