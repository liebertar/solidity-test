// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC721/IERC721.sol";

/**
 * @title IArtNFT
 * @dev Interface for Art NFT contract with enterprise-grade features
 * @author Art Platform Team
 */
interface IArtNFT is IERC721 {
    /**
     * @dev Struct to hold artwork metadata
     */
    struct ArtworkMetadata {
        string title;
        string description;
        string imageURI;
        string metadataURI;
        address creator;
        uint256 royaltyBps; // Basis points (100 = 1%)
        bool isVerified;
        uint256 createdAt;
        bytes32 c2paHash; // C2PA verification hash
    }

    /**
     * @dev Struct for royalty information
     */
    struct RoyaltyInfo {
        address recipient;
        uint256 royaltyBps;
    }

    // Events
    event ArtworkMinted(
        uint256 indexed tokenId,
        address indexed creator,
        address indexed owner,
        string metadataURI,
        uint256 royaltyBps
    );

    event ArtworkVerified(
        uint256 indexed tokenId,
        bytes32 c2paHash,
        address verifier
    );

    event RoyaltyUpdated(
        uint256 indexed tokenId,
        address recipient,
        uint256 royaltyBps
    );

    // Core Functions
    function mintArtwork(
        address to,
        string memory title,
        string memory description,
        string memory imageURI,
        string memory metadataURI,
        uint256 royaltyBps
    ) external returns (uint256 tokenId);

    function verifyArtwork(
        uint256 tokenId,
        bytes32 c2paHash
    ) external;

    function updateRoyalty(
        uint256 tokenId,
        uint256 royaltyBps
    ) external;

    // View Functions
    function getArtworkMetadata(uint256 tokenId) 
        external 
        view 
        returns (ArtworkMetadata memory);

    function getRoyaltyInfo(uint256 tokenId) 
        external 
        view 
        returns (RoyaltyInfo memory);

    function isVerified(uint256 tokenId) external view returns (bool);

    function getCreator(uint256 tokenId) external view returns (address);

    function totalSupply() external view returns (uint256);

    function tokenByIndex(uint256 index) external view returns (uint256);

    function tokenOfOwnerByIndex(address owner, uint256 index) 
        external 
        view 
        returns (uint256);
} 