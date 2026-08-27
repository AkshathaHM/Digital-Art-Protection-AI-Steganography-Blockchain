// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

contract DigitalArt {
    struct Artwork {
        address owner;
        address artist;
        string ipfsHash;
        string watermarkHash;
        string perceptualHash;
        string username;
        uint256 timestamp;
        uint256 price;
        bool isSold;
    }

    uint256 public nextArtworkId;
    mapping(uint256 => Artwork) private artworks;
    mapping(bytes32 => uint256) private artworkIdsByHash;
    mapping(bytes32 => bool) private artworkHashExists;

    event ArtworkRegistered(
        uint256 indexed artworkId,
        address indexed artist,
        string ipfsHash,
        string watermarkHash,
        uint256 price
    );
    event OwnershipTransferred(uint256 indexed artworkId, address indexed previousOwner, address indexed newOwner);
    event ArtworkPurchased(uint256 indexed artworkId, address indexed seller, address indexed buyer, uint256 price);

    function registerArtwork(string calldata ipfsHash, string calldata watermarkHash, uint256 price)
        external
        returns (uint256 artworkId)
    {
        require(bytes(ipfsHash).length > 0, 'IPFS hash is required');
        require(bytes(watermarkHash).length > 0, 'Watermark hash is required');
        artworkId = nextArtworkId++;
        artworks[artworkId] = Artwork(msg.sender, msg.sender, ipfsHash, watermarkHash, '', '', block.timestamp, price, false);
        emit ArtworkRegistered(artworkId, msg.sender, ipfsHash, watermarkHash, price);
    }

    function registerArtwork(uint256 timestamp, string calldata username, string calldata ipfsHash, string calldata perceptualHash)
        external
        returns (uint256 artworkId)
    {
        return registerArtwork(timestamp, username, ipfsHash, perceptualHash, 0);
    }

    function registerArtwork(uint256 timestamp, string calldata username, string calldata ipfsHash, string calldata perceptualHash, uint256 price)
        public
        returns (uint256 artworkId)
    {
        require(bytes(ipfsHash).length > 0, 'IPFS hash is required');
        require(bytes(perceptualHash).length > 0, 'Perceptual hash is required');
        bytes32 hashKey = keccak256(bytes(perceptualHash));
        require(!artworkHashExists[hashKey], 'Perceptual hash already exists');
        artworkId = nextArtworkId++;
        artworks[artworkId] = Artwork(msg.sender, msg.sender, ipfsHash, '', perceptualHash, username, timestamp, price, false);
        artworkIdsByHash[hashKey] = artworkId;
        artworkHashExists[hashKey] = true;
        emit ArtworkRegistered(artworkId, msg.sender, ipfsHash, '', price);
    }

    function transferOwnership(uint256 artworkId, address newOwner) external {
        _transferOwnership(artworkId, newOwner);
    }

    function _transferOwnership(uint256 artworkId, address newOwner) internal {
        Artwork storage artwork = artworks[artworkId];
        require(artwork.artist != address(0), 'Artwork does not exist');
        require(msg.sender == artwork.owner, 'Only owner can transfer');
        require(newOwner != address(0), 'New owner is required');
        address previousOwner = artwork.owner;
        artwork.owner = newOwner;
        artwork.isSold = true;
        emit OwnershipTransferred(artworkId, previousOwner, newOwner);
    }

    function transferOwnership(string calldata perceptualHash, address newOwner) external payable {
        bytes32 hashKey = keccak256(bytes(perceptualHash));
        require(artworkHashExists[hashKey], 'Artwork does not exist');
        uint256 artworkId = artworkIdsByHash[hashKey];
        Artwork storage artwork = artworks[artworkId];
        require(!artwork.isSold, 'Artwork is already sold');
        require(msg.sender != artwork.owner, 'Owner cannot purchase');
        require(newOwner == msg.sender, 'New owner must be the buyer');
        require(msg.value == artwork.price, 'Incorrect payment');
        address seller = artwork.owner;
        artwork.owner = newOwner;
        artwork.isSold = true;
        emit OwnershipTransferred(artworkId, seller, newOwner);
        (bool paid, ) = payable(seller).call{value: msg.value}('');
        require(paid, 'Payment failed');
    }

    function purchaseArtwork(uint256 artworkId) external payable {
        Artwork storage artwork = artworks[artworkId];
        require(artwork.artist != address(0), 'Artwork does not exist');
        require(!artwork.isSold, 'Artwork is already sold');
        require(msg.sender != artwork.owner, 'Owner cannot purchase');
        require(msg.value == artwork.price, 'Incorrect payment');

        address seller = artwork.owner;
        artwork.owner = msg.sender;
        artwork.isSold = true;
        (bool paid, ) = payable(seller).call{value: msg.value}('');
        require(paid, 'Payment failed');
        emit ArtworkPurchased(artworkId, seller, msg.sender, msg.value);
    }

    function getOwnership(uint256 artworkId)
        external
        view
        returns (address owner, address artist, string memory ipfsHash, string memory watermarkHash, uint256 price, bool isSold, string memory perceptualHash)
    {
        Artwork memory artwork = artworks[artworkId];
        require(artwork.artist != address(0), 'Artwork does not exist');
        return (artwork.owner, artwork.artist, artwork.ipfsHash, artwork.watermarkHash, artwork.price, artwork.isSold, artwork.perceptualHash);
    }

    function getArtworkDetailsByHash(string calldata perceptualHash)
        external
        view
        returns (address owner, address artist, string memory username, uint256 timestamp, string memory ipfsHash, string memory storedPerceptualHash, uint256 price, bool isSold)
    {
        bytes32 hashKey = keccak256(bytes(perceptualHash));
        require(artworkHashExists[hashKey], 'Artwork does not exist');
        Artwork memory artwork = artworks[artworkIdsByHash[hashKey]];
        return (artwork.owner, artwork.artist, artwork.username, artwork.timestamp, artwork.ipfsHash, artwork.perceptualHash, artwork.price, artwork.isSold);
    }
}
