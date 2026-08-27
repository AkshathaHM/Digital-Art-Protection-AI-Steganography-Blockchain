# Blockchain

Solidity contracts for artwork provenance, ownership transfer, and marketplace purchases on Hardhat Local.

The primary contract is `contracts/DigitalArt.sol`. Its ABI is checked in at `abi/DigitalArt.json` for the Flask and React clients.

The included Hardhat node uses chain ID `31337` at `http://127.0.0.1:8545` and is the primary local instance. Ganache support remains available as an optional network with chain ID `1337` at `http://127.0.0.1:7545`.

## Compile and deploy

```powershell
npm install
npm run compile
npm run deploy:ganache
```

Start Ganache GUI first, or run `npm run node` and use the `localhost` network instead.
