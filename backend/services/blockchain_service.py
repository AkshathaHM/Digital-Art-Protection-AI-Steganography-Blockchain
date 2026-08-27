import json
from pathlib import Path

from web3 import Web3
from web3.exceptions import ContractLogicError, Web3RPCError


class BlockchainService:
    def __init__(self, rpc_url: str, contract_address: str = '', private_key: str = ''):
        self.web3 = Web3(Web3.HTTPProvider(rpc_url))
        self.contract = None
        self.account = None
        if private_key:
            self.account = self.web3.eth.account.from_key(private_key)
        if contract_address:
            artifact_path = Path(__file__).parents[2] / 'blockchain' / 'artifacts' / 'contracts' / 'DigitalArt.sol' / 'DigitalArt.json'
            if artifact_path.exists():
                artifact = json.loads(artifact_path.read_text(encoding='utf-8'))
                self.contract = self.web3.eth.contract(
                    address=Web3.to_checksum_address(contract_address),
                    abi=artifact['abi'],
                )

    @property
    def available(self) -> bool:
        return bool(self.contract and self.account and self.web3.is_connected())

    def ownership(self, artwork_id: int):
        if not self.contract:
            return None
        try:
            return self.contract.functions.getOwnership(artwork_id).call()
        except (ContractLogicError, Web3RPCError):
            return None

    def register_existing_artwork(self, artwork: dict) -> dict:
        return self.register_artwork(
            artwork['ipfs_cid'],
            artwork.get('watermark_hash', ''),
            int(artwork.get('price_wei', 0)),
            username=artwork.get('username', ''),
            timestamp=int(artwork.get('created_at').timestamp()) if artwork.get('created_at') else 0,
            perceptual_hash=artwork['content_hash'],
        )

    def register_artwork(self, ipfs_hash: str, watermark_hash: str, price_wei: int, username: str = '', timestamp: int = 0, perceptual_hash: str = '') -> dict:
        if not self.available:
            raise RuntimeError('blockchain service is not configured or Ganache is unavailable')
        artwork_id = self.contract.functions.nextArtworkId().call()
        nonce = self.web3.eth.get_transaction_count(self.account.address)
        transaction = self.contract.functions.registerArtwork(
            timestamp, username, ipfs_hash, perceptual_hash, price_wei
        ).build_transaction({
            'from': self.account.address,
            'nonce': nonce,
            'chainId': self.web3.eth.chain_id,
            'gas': 500000,
            'gasPrice': self.web3.eth.gas_price,
        })
        signed = self.account.sign_transaction(transaction)
        tx_hash = self.web3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt['status'] != 1:
            raise RuntimeError('artwork registration transaction failed')
        return {'transaction_hash': tx_hash.hex(), 'artwork_id': artwork_id}

    def validate_receipt(self, transaction_hash: str) -> bool:
        if not self.web3.is_connected():
            raise RuntimeError('blockchain node is unavailable')
        receipt = self.web3.eth.get_transaction_receipt(transaction_hash)
        return receipt['status'] == 1

    def validate_purchase(self, transaction_hash: str, artwork_id: int, buyer: str, expected_price: int) -> bool:
        if not self.contract or not self.web3.is_connected():
            raise RuntimeError('blockchain service is unavailable')
        receipt = self.web3.eth.get_transaction_receipt(transaction_hash)
        transaction = self.web3.eth.get_transaction(transaction_hash)
        if receipt['status'] != 1 or transaction['to'] != self.contract.address:
            return False
        if transaction['from'].lower() != buyer.lower() or transaction['value'] != expected_price:
            return False
        function, parameters = self.contract.decode_function_input(transaction['input'])
        if function.fn_name == 'purchaseArtwork':
            return int(parameters['artworkId']) == int(artwork_id)
        if function.fn_name == 'transferOwnership':
            return parameters['perceptualHash'] == self.contract.functions.getOwnership(artwork_id).call()[6]
        return False
