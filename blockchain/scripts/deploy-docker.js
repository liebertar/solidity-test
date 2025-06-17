const hre = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
  console.log("🚀 Starting Docker deployment...");
  
  // Get signers
  const [deployer] = await hre.ethers.getSigners();
  console.log("Deploying contracts with account:", deployer.address);
  console.log("Account balance:", (await deployer.getBalance()).toString());

  // Deployment configuration
  const mintingFee = hre.ethers.utils.parseEther("0.001"); // 0.001 ETH

  console.log("📄 Deploying Simple NFT Contract...");
  
  // Deploy Simple NFT contract
  const SimpleNFT = await hre.ethers.getContractFactory("SimpleNFT");
  const nft = await hre.upgrades.deployProxy(
    SimpleNFT,
    [
      "Enterprise NFT Platform",
      "ENP", 
      mintingFee
    ],
    { 
      initializer: "initialize",
      kind: "uups"
    }
  );

  await nft.deployed();
  console.log("✅ Simple NFT Contract deployed to:", nft.address);

  // Prepare contract data for sharing
  const contractData = {
    network: "localhost",
    chainId: 31337,
    deployed_at: new Date().toISOString(),
    deployer: deployer.address,
    contracts: {
      nft: {
        address: nft.address,
        name: "Enterprise NFT Platform",
        symbol: "ENP",
        minting_fee: mintingFee.toString()
      }
    },
    test_accounts: [
      "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
      "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
      "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC",
      "0x90F79bf6EB2c4f870365E785982E1f101E93b906"
    ]
  };

  // Save to shared volume
  const sharedPath = "/shared/contracts.json";
  fs.writeFileSync(sharedPath, JSON.stringify(contractData, null, 2));
  console.log("✅ Contract addresses saved to:", sharedPath);

  // Also save to local directory for reference
  const localPath = path.join(__dirname, "../deployed-contracts.json");
  fs.writeFileSync(localPath, JSON.stringify(contractData, null, 2));
  console.log("✅ Contract addresses also saved locally to:", localPath);

  console.log("\n🎉 Docker deployment complete!");
  console.log("========================================");
  console.log("NFT Contract:", nft.address);
  console.log("Deployer:", deployer.address);
  console.log("Network: localhost (Docker)");
  console.log("========================================");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("❌ Deployment failed:", error);
    process.exit(1);
  }); 