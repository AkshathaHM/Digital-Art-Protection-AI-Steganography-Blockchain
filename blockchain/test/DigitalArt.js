const { expect } = require('chai');
const { ethers } = require('hardhat');

describe('DigitalArt', function () {
  it('registers artwork and returns ownership metadata', async function () {
    const [artist] = await ethers.getSigners();
    const contract = await ethers.deployContract('DigitalArt');
    await contract.waitForDeployment();

    await contract.registerArtwork('QmArtwork', 'wm-hash', ethers.parseEther('1'));
    const ownership = await contract.getOwnership(0);

    expect(ownership.owner).to.equal(artist.address);
    expect(ownership.artist).to.equal(artist.address);
    expect(ownership.ipfsHash).to.equal('QmArtwork');
    expect(ownership.watermarkHash).to.equal('wm-hash');
    expect(ownership.price).to.equal(ethers.parseEther('1'));
    expect(ownership.isSold).to.equal(false);
  });

  it('transfers ownership once and prevents a second sale', async function () {
    const [artist, buyer] = await ethers.getSigners();
    const contract = await ethers.deployContract('DigitalArt');
    await contract.waitForDeployment();

    await contract.registerArtwork('QmArtwork', 'wm-hash', ethers.parseEther('1'));
    await expect(contract.connect(buyer).purchaseArtwork(0, { value: ethers.parseEther('1') }))
      .to.emit(contract, 'ArtworkPurchased')
      .withArgs(0, artist.address, buyer.address, ethers.parseEther('1'));
    await expect(contract.connect(artist).purchaseArtwork(0, { value: ethers.parseEther('1') }))
      .to.be.revertedWith('Artwork is already sold');
  });

  it('stores metadata and finds artwork by perceptual hash', async function () {
    const [artist] = await ethers.getSigners();
    const contract = await ethers.deployContract('DigitalArt');
    await contract.waitForDeployment();

    await contract['registerArtwork(uint256,string,string,string,uint256)'](
      1730000000, 'Aster Vale', 'QmArtwork', 'a1b2c3d4', ethers.parseEther('0.5'),
    );
    const details = await contract.getArtworkDetailsByHash('a1b2c3d4');

    expect(details.owner).to.equal(artist.address);
    expect(details.artist).to.equal(artist.address);
    expect(details.username).to.equal('Aster Vale');
    expect(details.timestamp).to.equal(1730000000);
    expect(details.ipfsHash).to.equal('QmArtwork');
    expect(details.storedPerceptualHash).to.equal('a1b2c3d4');
    expect(details.price).to.equal(ethers.parseEther('0.5'));
  });

  it('transfers ownership by perceptual hash after payment', async function () {
    const [artist, buyer] = await ethers.getSigners();
    const contract = await ethers.deployContract('DigitalArt');
    await contract.waitForDeployment();

    await contract['registerArtwork(uint256,string,string,string,uint256)'](
      1730000000, 'Aster Vale', 'QmArtwork', 'a1b2c3d4', ethers.parseEther('0.5'),
    );
    await expect(contract.connect(buyer)['transferOwnership(string,address)']('a1b2c3d4', buyer.address, { value: ethers.parseEther('0.5') }))
      .to.emit(contract, 'OwnershipTransferred')
      .withArgs(0, artist.address, buyer.address);

    const ownership = await contract.getOwnership(0);
    expect(ownership.owner).to.equal(buyer.address);
    expect(ownership.isSold).to.equal(true);
  });
});
