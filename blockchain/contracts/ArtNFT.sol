// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts-upgradeable/token/ERC721/ERC721Upgradeable.sol";
import "@openzeppelin/contracts-upgradeable/token/ERC721/extensions/ERC721EnumerableUpgradeable.sol";
import "@openzeppelin/contracts-upgradeable/token/ERC721/extensions/ERC721URIStorageUpgradeable.sol";
import "@openzeppelin/contracts-upgradeable/security/PausableUpgradeable.sol";
import "@openzeppelin/contracts-upgradeable/access/AccessControlUpgradeable.sol";
import "@openzeppelin/contracts-upgradeable/security/ReentrancyGuardUpgradeable.sol";
import "@openzeppelin/contracts-upgradeable/proxy/utils/Initializable.sol";
import "@openzeppelin/contracts-upgradeable/proxy/utils/UUPSUpgradeable.sol";
import "@openzeppelin/contracts-upgradeable/utils/CountersUpgradeable.sol";
import "@openzeppelin/contracts/interfaces/IERC2981.sol";
import "./interfaces/IArtNFT.sol";

/**
 * @title ArtNFT
 * @dev Enterprise-grade NFT contract for digital art with verification and royalties
 * @author Art Platform Team
 */
contract ArtNFT is
    Initializable,
    ERC721Upgradeable,
    ERC721EnumerableUpgradeable,
    ERC721URIStorageUpgradeable,
    PausableUpgradeable,
    AccessControlUpgradeable,
    ReentrancyGuardUpgradeable,
    UUPSUpgradeable,
    IERC2981,
    IArtNFT
{
    using CountersUpgradeable for CountersUpgradeable.Counter;

    // Role definitions
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");
    bytes32 public constant VERIFIER_ROLE = keccak256("VERIFIER_ROLE");
    bytes32 public constant UPGRADER_ROLE = keccak256("UPGRADER_ROLE");

    // Constants
    uint256 public constant MAX_ROYALTY_BPS = 1000; // 10% maximum royalty
    uint256 public constant BPS_DENOMINATOR = 10000;

    // State variables
    CountersUpgradeable.Counter private _tokenIdCounter;
    mapping(uint256 => ArtworkMetadata) private _artworkMetadata;
    mapping(uint256 => RoyaltyInfo) private _royaltyInfo;
    mapping(address => bool) public authorizedMinters;

    // Platform settings
    address public platformTreasury;
    uint256 public mintingFee;
    bool public publicMintingEnabled;

    // Custom errors for gas optimization
    error InvalidRoyaltyBps();
    error UnauthorizedMinter();
    error TokenNotExists();
    error InvalidCreator();
    error AlreadyVerified();
    error InsufficientMintingFee();

    /// @custom:oz-upgrades-unsafe-allow constructor
    constructor() {
        _disableInitializers();
    }

    /**
     * @dev Initialize the contract
     */
    function initialize(
        string memory name,
        string memory symbol,
        address _platformTreasury,
        uint256 _mintingFee
    ) public initializer {
        __ERC721_init(name, symbol);
        __ERC721Enumerable_init();
        __ERC721URIStorage_init();
        __Pausable_init();
        __AccessControl_init();
        __ReentrancyGuard_init();
        __UUPSUpgradeable_init();

        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(MINTER_ROLE, msg.sender);
        _grantRole(VERIFIER_ROLE, msg.sender);
        _grantRole(UPGRADER_ROLE, msg.sender);

        platformTreasury = _platformTreasury;
        mintingFee = _mintingFee;
        publicMintingEnabled = false;

        // Start token IDs from 1
        _tokenIdCounter.increment();
    }

    /**
     * @dev Mint new artwork NFT
     */
    function mintArtwork(
        address to,
        string memory title,
        string memory description,
        string memory imageURI,
        string memory metadataURI,
        uint256 royaltyBps
    ) external payable override nonReentrant whenNotPaused returns (uint256 tokenId) {
        // Validation
        if (royaltyBps > MAX_ROYALTY_BPS) revert InvalidRoyaltyBps();
        if (!publicMintingEnabled && !hasRole(MINTER_ROLE, msg.sender)) {
            revert UnauthorizedMinter();
        }
        if (msg.value < mintingFee) revert InsufficientMintingFee();

        // Get new token ID
        tokenId = _tokenIdCounter.current();
        _tokenIdCounter.increment();

        // Mint the token
        _safeMint(to, tokenId);
        _setTokenURI(tokenId, metadataURI);

        // Store artwork metadata
        _artworkMetadata[tokenId] = ArtworkMetadata({
            title: title,
            description: description,
            imageURI: imageURI,
            metadataURI: metadataURI,
            creator: msg.sender,
            royaltyBps: royaltyBps,
            isVerified: false,
            createdAt: block.timestamp,
            c2paHash: bytes32(0)
        });

        // Set royalty info
        _royaltyInfo[tokenId] = RoyaltyInfo({
            recipient: msg.sender,
            royaltyBps: royaltyBps
        });

        // Transfer minting fee to platform treasury
        if (msg.value > 0) {
            (bool success, ) = platformTreasury.call{value: msg.value}("");
            require(success, "Fee transfer failed");
        }

        emit ArtworkMinted(tokenId, msg.sender, to, metadataURI, royaltyBps);
    }

    /**
     * @dev Verify artwork with C2PA hash
     */
    function verifyArtwork(
        uint256 tokenId,
        bytes32 c2paHash
    ) external override onlyRole(VERIFIER_ROLE) {
        if (!_exists(tokenId)) revert TokenNotExists();
        if (_artworkMetadata[tokenId].isVerified) revert AlreadyVerified();

        _artworkMetadata[tokenId].isVerified = true;
        _artworkMetadata[tokenId].c2paHash = c2paHash;

        emit ArtworkVerified(tokenId, c2paHash, msg.sender);
    }

    /**
     * @dev Update royalty for a token (only creator)
     */
    function updateRoyalty(
        uint256 tokenId,
        uint256 royaltyBps
    ) external override {
        if (!_exists(tokenId)) revert TokenNotExists();
        if (_artworkMetadata[tokenId].creator != msg.sender) revert InvalidCreator();
        if (royaltyBps > MAX_ROYALTY_BPS) revert InvalidRoyaltyBps();

        _artworkMetadata[tokenId].royaltyBps = royaltyBps;
        _royaltyInfo[tokenId].royaltyBps = royaltyBps;

        emit RoyaltyUpdated(tokenId, msg.sender, royaltyBps);
    }

    /**
     * @dev Get artwork metadata
     */
    function getArtworkMetadata(uint256 tokenId) 
        external 
        view 
        override 
        returns (ArtworkMetadata memory) 
    {
        if (!_exists(tokenId)) revert TokenNotExists();
        return _artworkMetadata[tokenId];
    }

    /**
     * @dev Get royalty info for EIP-2981
     */
    function getRoyaltyInfo(uint256 tokenId) 
        external 
        view 
        override 
        returns (RoyaltyInfo memory) 
    {
        if (!_exists(tokenId)) revert TokenNotExists();
        return _royaltyInfo[tokenId];
    }

    /**
     * @dev EIP-2981 royalty info
     */
    function royaltyInfo(uint256 tokenId, uint256 salePrice)
        external
        view
        override
        returns (address receiver, uint256 royaltyAmount)
    {
        if (!_exists(tokenId)) return (address(0), 0);
        
        RoyaltyInfo memory royalty = _royaltyInfo[tokenId];
        royaltyAmount = (salePrice * royalty.royaltyBps) / BPS_DENOMINATOR;
        receiver = royalty.recipient;
    }

    /**
     * @dev Check if artwork is verified
     */
    function isVerified(uint256 tokenId) external view override returns (bool) {
        if (!_exists(tokenId)) return false;
        return _artworkMetadata[tokenId].isVerified;
    }

    /**
     * @dev Get creator of artwork
     */
    function getCreator(uint256 tokenId) external view override returns (address) {
        if (!_exists(tokenId)) return address(0);
        return _artworkMetadata[tokenId].creator;
    }

    // Admin functions
    function setPlatformTreasury(address _platformTreasury) external onlyRole(DEFAULT_ADMIN_ROLE) {
        platformTreasury = _platformTreasury;
    }

    function setMintingFee(uint256 _mintingFee) external onlyRole(DEFAULT_ADMIN_ROLE) {
        mintingFee = _mintingFee;
    }

    function setPublicMintingEnabled(bool _enabled) external onlyRole(DEFAULT_ADMIN_ROLE) {
        publicMintingEnabled = _enabled;
    }

    function pause() external onlyRole(DEFAULT_ADMIN_ROLE) {
        _pause();
    }

    function unpause() external onlyRole(DEFAULT_ADMIN_ROLE) {
        _unpause();
    }

    // Upgrade authorization
    function _authorizeUpgrade(address newImplementation) 
        internal 
        onlyRole(UPGRADER_ROLE) 
        override 
    {}

    // Override required functions
    function _beforeTokenTransfer(
        address from,
        address to,
        uint256 tokenId,
        uint256 batchSize
    ) internal override(ERC721Upgradeable, ERC721EnumerableUpgradeable) whenNotPaused {
        super._beforeTokenTransfer(from, to, tokenId, batchSize);
    }

    function _burn(uint256 tokenId) 
        internal 
        override(ERC721Upgradeable, ERC721URIStorageUpgradeable) 
    {
        super._burn(tokenId);
        delete _artworkMetadata[tokenId];
        delete _royaltyInfo[tokenId];
    }

    function tokenURI(uint256 tokenId)
        public
        view
        override(ERC721Upgradeable, ERC721URIStorageUpgradeable)
        returns (string memory)
    {
        return super.tokenURI(tokenId);
    }

    function supportsInterface(bytes4 interfaceId)
        public
        view
        override(ERC721Upgradeable, ERC721EnumerableUpgradeable, AccessControlUpgradeable, IERC165)
        returns (bool)
    {
        return interfaceId == type(IERC2981).interfaceId || 
               super.supportsInterface(interfaceId);
    }
} 