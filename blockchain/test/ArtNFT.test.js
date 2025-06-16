const { expect } = require("chai");
const { ethers, upgrades } = require("hardhat");

describe("ArtNFT", function () {
  let artNFT;
  let owner, creator, buyer, verifier, treasury;
  let mintingFee;

  beforeEach(async function () {
    [owner, creator, buyer, verifier, treasury] = await ethers.getSigners();
    
    mintingFee = ethers.utils.parseEther("0.001");
    
    const ArtNFT = await ethers.getContractFactory("ArtNFT");
    artNFT = await upgrades.deployProxy(
      ArtNFT,
      [
        "ArtPlatform",
        "ART", 
        treasury.address,
        mintingFee
      ],
      { initializer: "initialize", kind: "uups" }
    );
    await artNFT.deployed();

    // Grant roles
    const VERIFIER_ROLE = await artNFT.VERIFIER_ROLE();
    await artNFT.grantRole(VERIFIER_ROLE, verifier.address);
  });

  describe("Deployment", function () {
    it("Should set the right name and symbol", async function () {
      expect(await artNFT.name()).to.equal("ArtPlatform");
      expect(await artNFT.symbol()).to.equal("ART");
    });

    it("Should set the right treasury and minting fee", async function () {
      expect(await artNFT.platformTreasury()).to.equal(treasury.address);
      expect(await artNFT.mintingFee()).to.equal(mintingFee);
    });

    it("Should have the right roles assigned", async function () {
      const DEFAULT_ADMIN_ROLE = await artNFT.DEFAULT_ADMIN_ROLE();
      const MINTER_ROLE = await artNFT.MINTER_ROLE();
      const VERIFIER_ROLE = await artNFT.VERIFIER_ROLE();

      expect(await artNFT.hasRole(DEFAULT_ADMIN_ROLE, owner.address)).to.be.true;
      expect(await artNFT.hasRole(MINTER_ROLE, owner.address)).to.be.true;
      expect(await artNFT.hasRole(VERIFIER_ROLE, verifier.address)).to.be.true;
    });
  });

  describe("Minting", function () {
    const artworkData = {
      title: "Digital Masterpiece",
      description: "A beautiful digital artwork",
      imageURI: "ipfs://QmExampleImageHash",
      metadataURI: "ipfs://QmExampleMetadataHash",
      royaltyBps: 500 // 5%
    };

    it("Should mint artwork successfully with admin role", async function () {
      const tx = await artNFT.mintArtwork(
        creator.address,
        artworkData.title,
        artworkData.description,
        artworkData.imageURI,
        artworkData.metadataURI,
        artworkData.royaltyBps,
        { value: mintingFee }
      );

      const receipt = await tx.wait();
      const event = receipt.events.find(e => e.event === "ArtworkMinted");
      
      expect(event.args.tokenId).to.equal(1);
      expect(event.args.creator).to.equal(owner.address);
      expect(event.args.owner).to.equal(creator.address);
      expect(event.args.royaltyBps).to.equal(artworkData.royaltyBps);
    });

    it("Should fail minting without sufficient fee", async function () {
      await expect(
        artNFT.mintArtwork(
          creator.address,
          artworkData.title,
          artworkData.description,
          artworkData.imageURI,
          artworkData.metadataURI,
          artworkData.royaltyBps,
          { value: ethers.utils.parseEther("0.0005") }
        )
      ).to.be.revertedWithCustomError(artNFT, "InsufficientMintingFee");
    });

    it("Should fail minting with excessive royalty", async function () {
      await expect(
        artNFT.mintArtwork(
          creator.address,
          artworkData.title,
          artworkData.description,
          artworkData.imageURI,
          artworkData.metadataURI,
          1500, // 15% - exceeds MAX_ROYALTY_BPS
          { value: mintingFee }
        )
      ).to.be.revertedWithCustomError(artNFT, "InvalidRoyaltyBps");
    });

    it("Should fail minting without MINTER_ROLE when public minting disabled", async function () {
      await expect(
        artNFT.connect(creator).mintArtwork(
          creator.address,
          artworkData.title,
          artworkData.description,
          artworkData.imageURI,
          artworkData.metadataURI,
          artworkData.royaltyBps,
          { value: mintingFee }
        )
      ).to.be.revertedWithCustomError(artNFT, "UnauthorizedMinter");
    });

    it("Should allow public minting when enabled", async function () {
      await artNFT.setPublicMintingEnabled(true);
      
      await expect(
        artNFT.connect(creator).mintArtwork(
          creator.address,
          artworkData.title,
          artworkData.description,
          artworkData.imageURI,
          artworkData.metadataURI,
          artworkData.royaltyBps,
          { value: mintingFee }
        )
      ).not.to.be.reverted;
    });

    it("Should transfer minting fee to treasury", async function () {
      const treasuryBalanceBefore = await treasury.getBalance();
      
      await artNFT.mintArtwork(
        creator.address,
        artworkData.title,
        artworkData.description,
        artworkData.imageURI,
        artworkData.metadataURI,
        artworkData.royaltyBps,
        { value: mintingFee }
      );

      const treasuryBalanceAfter = await treasury.getBalance();
      expect(treasuryBalanceAfter.sub(treasuryBalanceBefore)).to.equal(mintingFee);
    });
  });

  describe("Artwork Metadata", function () {
    let tokenId;

    beforeEach(async function () {
      const tx = await artNFT.mintArtwork(
        creator.address,
        "Test Artwork",
        "Test Description",
        "ipfs://testimage",
        "ipfs://testmetadata",
        300,
        { value: mintingFee }
      );
      const receipt = await tx.wait();
      tokenId = receipt.events.find(e => e.event === "ArtworkMinted").args.tokenId;
    });

    it("Should return correct artwork metadata", async function () {
      const metadata = await artNFT.getArtworkMetadata(tokenId);
      
      expect(metadata.title).to.equal("Test Artwork");
      expect(metadata.description).to.equal("Test Description");
      expect(metadata.imageURI).to.equal("ipfs://testimage");
      expect(metadata.metadataURI).to.equal("ipfs://testmetadata");
      expect(metadata.creator).to.equal(owner.address);
      expect(metadata.royaltyBps).to.equal(300);
      expect(metadata.isVerified).to.be.false;
    });

    it("Should return correct creator", async function () {
      expect(await artNFT.getCreator(tokenId)).to.equal(owner.address);
    });

    it("Should return correct royalty info", async function () {
      const royaltyInfo = await artNFT.getRoyaltyInfo(tokenId);
      expect(royaltyInfo.recipient).to.equal(owner.address);
      expect(royaltyInfo.royaltyBps).to.equal(300);
    });

    it("Should calculate EIP-2981 royalty correctly", async function () {
      const salePrice = ethers.utils.parseEther("1");
      const [recipient, royaltyAmount] = await artNFT.royaltyInfo(tokenId, salePrice);
      
      expect(recipient).to.equal(owner.address);
      expect(royaltyAmount).to.equal(salePrice.mul(300).div(10000)); // 3%
    });
  });

  describe("Verification", function () {
    let tokenId;
    const c2paHash = ethers.utils.keccak256(ethers.utils.toUtf8Bytes("test-c2pa-data"));

    beforeEach(async function () {
      const tx = await artNFT.mintArtwork(
        creator.address,
        "Test Artwork",
        "Test Description",
        "ipfs://testimage",
        "ipfs://testmetadata",
        300,
        { value: mintingFee }
      );
      const receipt = await tx.wait();
      tokenId = receipt.events.find(e => e.event === "ArtworkMinted").args.tokenId;
    });

    it("Should verify artwork with VERIFIER_ROLE", async function () {
      await expect(
        artNFT.connect(verifier).verifyArtwork(tokenId, c2paHash)
      ).to.emit(artNFT, "ArtworkVerified")
       .withArgs(tokenId, c2paHash, verifier.address);

      expect(await artNFT.isVerified(tokenId)).to.be.true;
      
      const metadata = await artNFT.getArtworkMetadata(tokenId);
      expect(metadata.isVerified).to.be.true;
      expect(metadata.c2paHash).to.equal(c2paHash);
    });

    it("Should fail verification without VERIFIER_ROLE", async function () {
      await expect(
        artNFT.connect(creator).verifyArtwork(tokenId, c2paHash)
      ).to.be.reverted;
    });

    it("Should fail verification of non-existent token", async function () {
      await expect(
        artNFT.connect(verifier).verifyArtwork(999, c2paHash)
      ).to.be.revertedWithCustomError(artNFT, "TokenNotExists");
    });

    it("Should fail double verification", async function () {
      await artNFT.connect(verifier).verifyArtwork(tokenId, c2paHash);
      
      await expect(
        artNFT.connect(verifier).verifyArtwork(tokenId, c2paHash)
      ).to.be.revertedWithCustomError(artNFT, "AlreadyVerified");
    });
  });

  describe("Royalty Updates", function () {
    let tokenId;

    beforeEach(async function () {
      const tx = await artNFT.mintArtwork(
        creator.address,
        "Test Artwork",
        "Test Description",
        "ipfs://testimage",
        "ipfs://testmetadata",
        300,
        { value: mintingFee }
      );
      const receipt = await tx.wait();
      tokenId = receipt.events.find(e => e.event === "ArtworkMinted").args.tokenId;
    });

    it("Should allow creator to update royalty", async function () {
      await expect(
        artNFT.updateRoyalty(tokenId, 500)
      ).to.emit(artNFT, "RoyaltyUpdated")
       .withArgs(tokenId, owner.address, 500);

      const royaltyInfo = await artNFT.getRoyaltyInfo(tokenId);
      expect(royaltyInfo.royaltyBps).to.equal(500);
    });

    it("Should fail royalty update by non-creator", async function () {
      await expect(
        artNFT.connect(creator).updateRoyalty(tokenId, 500)
      ).to.be.revertedWithCustomError(artNFT, "InvalidCreator");
    });

    it("Should fail royalty update with excessive rate", async function () {
      await expect(
        artNFT.updateRoyalty(tokenId, 1500)
      ).to.be.revertedWithCustomError(artNFT, "InvalidRoyaltyBps");
    });
  });

  describe("Admin Functions", function () {
    it("Should allow admin to set platform treasury", async function () {
      const newTreasury = buyer.address;
      await artNFT.setPlatformTreasury(newTreasury);
      expect(await artNFT.platformTreasury()).to.equal(newTreasury);
    });

    it("Should allow admin to set minting fee", async function () {
      const newFee = ethers.utils.parseEther("0.002");
      await artNFT.setMintingFee(newFee);
      expect(await artNFT.mintingFee()).to.equal(newFee);
    });

    it("Should allow admin to enable/disable public minting", async function () {
      await artNFT.setPublicMintingEnabled(true);
      expect(await artNFT.publicMintingEnabled()).to.be.true;
      
      await artNFT.setPublicMintingEnabled(false);
      expect(await artNFT.publicMintingEnabled()).to.be.false;
    });

    it("Should allow admin to pause/unpause", async function () {
      await artNFT.pause();
      expect(await artNFT.paused()).to.be.true;
      
      await artNFT.unpause();
      expect(await artNFT.paused()).to.be.false;
    });

    it("Should fail admin functions without proper role", async function () {
      await expect(
        artNFT.connect(creator).setPlatformTreasury(creator.address)
      ).to.be.reverted;
    });
  });

  describe("ERC721 Compliance", function () {
    let tokenId;

    beforeEach(async function () {
      const tx = await artNFT.mintArtwork(
        creator.address,
        "Test Artwork",
        "Test Description",
        "ipfs://testimage",
        "ipfs://testmetadata",
        300,
        { value: mintingFee }
      );
      const receipt = await tx.wait();
      tokenId = receipt.events.find(e => e.event === "ArtworkMinted").args.tokenId;
    });

    it("Should support required interfaces", async function () {
      expect(await artNFT.supportsInterface("0x80ac58cd")).to.be.true; // ERC721
      expect(await artNFT.supportsInterface("0x2a55205a")).to.be.true; // ERC2981
    });

    it("Should return correct token URI", async function () {
      expect(await artNFT.tokenURI(tokenId)).to.equal("ipfs://testmetadata");
    });

    it("Should return correct owner", async function () {
      expect(await artNFT.ownerOf(tokenId)).to.equal(creator.address);
    });

    it("Should handle transfers correctly", async function () {
      await artNFT.connect(creator).transferFrom(creator.address, buyer.address, tokenId);
      expect(await artNFT.ownerOf(tokenId)).to.equal(buyer.address);
    });

    it("Should enumerate tokens correctly", async function () {
      expect(await artNFT.totalSupply()).to.equal(1);
      expect(await artNFT.tokenByIndex(0)).to.equal(tokenId);
      expect(await artNFT.tokenOfOwnerByIndex(creator.address, 0)).to.equal(tokenId);
    });
  });

  describe("Upgrade", function () {
    it("Should be upgradeable by UPGRADER_ROLE", async function () {
      const ArtNFTV2 = await ethers.getContractFactory("ArtNFT");
      
      await expect(
        upgrades.upgradeProxy(artNFT.address, ArtNFTV2)
      ).not.to.be.reverted;
    });

    it("Should fail upgrade without UPGRADER_ROLE", async function () {
      const UPGRADER_ROLE = await artNFT.UPGRADER_ROLE();
      await artNFT.revokeRole(UPGRADER_ROLE, owner.address);
      
      const ArtNFTV2 = await ethers.getContractFactory("ArtNFT");
      
      await expect(
        upgrades.upgradeProxy(artNFT.address, ArtNFTV2)
      ).to.be.reverted;
    });
  });
}); 