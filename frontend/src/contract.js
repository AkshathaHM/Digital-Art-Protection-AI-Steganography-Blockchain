export const digitalArtAbi = [
  { inputs: [], name: 'nextArtworkId', outputs: [{ name: '', type: 'uint256' }], stateMutability: 'view', type: 'function' },
  { inputs: [{ name: 'ipfsHash', type: 'string' }, { name: 'watermarkHash', type: 'string' }, { name: 'price', type: 'uint256' }], name: 'registerArtwork', outputs: [{ name: 'artworkId', type: 'uint256' }], stateMutability: 'nonpayable', type: 'function' },
  { inputs: [{ name: 'timestamp', type: 'uint256' }, { name: 'username', type: 'string' }, { name: 'ipfsHash', type: 'string' }, { name: 'perceptualHash', type: 'string' }, { name: 'price', type: 'uint256' }], name: 'registerArtwork', outputs: [{ name: 'artworkId', type: 'uint256' }], stateMutability: 'nonpayable', type: 'function' },
  { inputs: [{ name: 'artworkId', type: 'uint256' }], name: 'purchaseArtwork', outputs: [], stateMutability: 'payable', type: 'function' },
  { inputs: [{ name: 'artworkId', type: 'uint256' }, { name: 'newOwner', type: 'address' }], name: 'transferOwnership', outputs: [], stateMutability: 'nonpayable', type: 'function' },
  { inputs: [{ name: 'perceptualHash', type: 'string' }, { name: 'newOwner', type: 'address' }], name: 'transferOwnership', outputs: [], stateMutability: 'payable', type: 'function' },
  { inputs: [{ name: 'artworkId', type: 'uint256' }], name: 'getOwnership', outputs: [{ name: 'owner', type: 'address' }, { name: 'artist', type: 'address' }, { name: 'ipfsHash', type: 'string' }, { name: 'watermarkHash', type: 'string' }, { name: 'price', type: 'uint256' }, { name: 'isSold', type: 'bool' }, { name: 'perceptualHash', type: 'string' }], stateMutability: 'view', type: 'function' },
  { inputs: [{ name: 'perceptualHash', type: 'string' }], name: 'getArtworkDetailsByHash', outputs: [{ name: 'owner', type: 'address' }, { name: 'artist', type: 'address' }, { name: 'username', type: 'string' }, { name: 'timestamp', type: 'uint256' }, { name: 'ipfsHash', type: 'string' }, { name: 'storedPerceptualHash', type: 'string' }, { name: 'price', type: 'uint256' }, { name: 'isSold', type: 'bool' }], stateMutability: 'view', type: 'function' },
];

export const contractAddress = import.meta.env.VITE_CONTRACT_ADDRESS || '';
const expectedChainId = BigInt(import.meta.env.VITE_CHAIN_ID || '1337');
const rpcUrl = import.meta.env.VITE_RPC_URL || 'http://127.0.0.1:7545';
const networkName = import.meta.env.VITE_NETWORK_NAME || 'Ganache Local';

async function selectLocalNetwork() {
  const chainId = `0x${expectedChainId.toString(16)}`;
  try {
    await window.ethereum.request({ method: 'wallet_switchEthereumChain', params: [{ chainId }] });
  } catch (error) {
    if (error.code !== 4902) throw error;
    await window.ethereum.request({
      method: 'wallet_addEthereumChain',
      params: [{
        chainId,
        chainName: networkName,
        nativeCurrency: { name: 'Ether', symbol: 'ETH', decimals: 18 },
        rpcUrls: [rpcUrl],
      }],
    });
  }
}

export async function connectWallet() {
  if (!window.ethereum) throw new Error('MetaMask or a compatible wallet is required');
  await window.ethereum.request({ method: 'eth_requestAccounts' });
  const currentChainId = await window.ethereum.request({ method: 'eth_chainId' });
  if (BigInt(currentChainId) !== expectedChainId) {
    await selectLocalNetwork();
  }
  const selectedChainId = await window.ethereum.request({ method: 'eth_chainId' });
  if (BigInt(selectedChainId) !== expectedChainId) {
    throw new Error(`Wrong network. Select ${networkName} (chain ID ${expectedChainId.toString()}) in MetaMask.`);
  }
  const { default: Web3 } = await import('web3');
  const web3 = new Web3(window.ethereum);
  const accounts = await web3.eth.getAccounts();
  const balance = await web3.eth.getBalance(accounts[0]);
  if (BigInt(balance) === 0n) {
    throw new Error(`Wallet ${accounts[0]} has no Ganache ETH. Import a funded buyer account and switch MetaMask to Ganache Local (chain ID 1337).`);
  }
  return { address: accounts[0], web3 };
}
