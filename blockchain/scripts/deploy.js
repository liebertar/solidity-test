const { ethers, upgrades } = require("hardhat");

async function main() {
  console.log("🚀 Starting deployment...");
  
  const [deployer] = await ethers.getSigners();
  console.log("Deploying contracts with the account:", deployer.address);
  console.log("Account balance:", (await deployer.getBalance()).toString());

  // Deploy ArtNFT contract
  console.log("\n📦 Deploying ArtNFT contract...");
  const ArtNFT = await ethers.getContractFactory("ArtNFT");
  
  const artNFT = await upgrades.deployProxy(
    ArtNFT,
    [
      "ArtPlatform", // name
      "ART", // symbol
      deployer.address, // platform treasury
      ethers.utils.parseEther("0.001") // minting fee (0.001 ETH)
    ],
    {
      initializer: "initialize",
      kind: "uups",
    }
  );
  await artNFT.deployed();
  console.log("✅ ArtNFT deployed to:", artNFT.address);

  // Deploy ArtMarketplace contract
  console.log("\n🏪 Deploying ArtMarketplace contract...");
  const ArtMarketplace = await ethers.getContractFactory("ArtMarketplace");
  
  const artMarketplace = await upgrades.deployProxy(
    ArtMarketplace,
    [
      deployer.address, // platform treasury
      250 // platform fee (2.5%)
    ],
    {
      initializer: "initialize",
      kind: "uups",
    }
  );
  await artMarketplace.deployed();
  console.log("✅ ArtMarketplace deployed to:", artMarketplace.address);

  // Setup initial roles and permissions
  console.log("\n⚙️  Setting up roles and permissions...");
  
  // Grant MINTER_ROLE to marketplace for automated minting
  const MINTER_ROLE = await artNFT.MINTER_ROLE();
  await artNFT.grantRole(MINTER_ROLE, artMarketplace.address);
  console.log("✅ Granted MINTER_ROLE to marketplace");

  // Enable public minting (optional)
  // await artNFT.setPublicMintingEnabled(true);
  // console.log("✅ Enabled public minting");

  // Verify contracts on etherscan (if not on localhost)
  if (network.name !== "hardhat" && network.name !== "localhost") {
    console.log("\n🔍 Waiting for block confirmations...");
    await artNFT.deployTransaction.wait(5);
    await artMarketplace.deployTransaction.wait(5);

    console.log("📋 Verifying contracts on Etherscan...");
    try {
      await hre.run("verify:verify", {
        address: artNFT.address,
        constructorArguments: [],
      });
      console.log("✅ ArtNFT verified");
    } catch (error) {
      console.log("❌ ArtNFT verification failed:", error.message);
    }

    try {
      await hre.run("verify:verify", {
        address: artMarketplace.address,
        constructorArguments: [],
      });
      console.log("✅ ArtMarketplace verified");
    } catch (error) {
      console.log("❌ ArtMarketplace verification failed:", error.message);
    }
  }

  // Save deployment addresses
  const deploymentInfo = {
    network: network.name,
    deployer: deployer.address,
    contracts: {
      ArtNFT: {
        address: artNFT.address,
        implementation: await upgrades.erc1967.getImplementationAddress(artNFT.address),
        admin: await upgrades.erc1967.getAdminAddress(artNFT.address),
      },
      ArtMarketplace: {
        address: artMarketplace.address,
        implementation: await upgrades.erc1967.getImplementationAddress(artMarketplace.address),
        admin: await upgrades.erc1967.getAdminAddress(artMarketplace.address),
      },
    },
    timestamp: new Date().toISOString(),
  };

  console.log("\n📄 Deployment Summary:");
  console.log("=".repeat(50));
  console.log(`Network: ${deploymentInfo.network}`);
  console.log(`Deployer: ${deploymentInfo.deployer}`);
  console.log(`ArtNFT: ${deploymentInfo.contracts.ArtNFT.address}`);
  console.log(`ArtMarketplace: ${deploymentInfo.contracts.ArtMarketplace.address}`);
  console.log("=".repeat(50));

  // Save to file
  const fs = require("fs");
  const path = require("path");
  
  const deploymentsDir = path.join(__dirname, "..", "deployments");
  if (!fs.existsSync(deploymentsDir)) {
    fs.mkdirSync(deploymentsDir);
  }
  
  const deploymentFile = path.join(deploymentsDir, `${network.name}.json`);
  fs.writeFileSync(deploymentFile, JSON.stringify(deploymentInfo, null, 2));
  
  console.log(`💾 Deployment info saved to: ${deploymentFile}`);
  console.log("🎉 Deployment completed successfully!");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("❌ Deployment failed:", error);
    process.exit(1);
  }); 