const hre = require('hardhat');
const fs = require('fs');
const path = require('path');

async function main() {
  const digitalArt = await hre.ethers.deployContract('DigitalArt');
  await digitalArt.waitForDeployment();
  const address = await digitalArt.getAddress();
  const deploymentDirectory = path.join(__dirname, '..', 'deployments');
  fs.mkdirSync(deploymentDirectory, { recursive: true });
  fs.writeFileSync(
    path.join(deploymentDirectory, `${hre.network.name}.json`),
    JSON.stringify({ network: hre.network.name, chainId: hre.network.config.chainId, address }, null, 2),
  );
  console.log(`DigitalArt deployed to ${address}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
