// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts-upgradeable/security/ReentrancyGuardUpgradeable.sol";
import "@openzeppelin/contracts-upgradeable/security/PausableUpgradeable.sol";
import "@openzeppelin/contracts-upgradeable/access/AccessControlUpgradeable.sol";
import "@openzeppelin/contracts-upgradeable/proxy/utils/Initializable.sol";
import "@openzeppelin/contracts-upgradeable/proxy/utils/UUPSUpgradeable.sol";
import "@openzeppelin/contracts-upgradeable/utils/CountersUpgradeable.sol";
import "@openzeppelin/contracts/token/ERC721/IERC721.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/interfaces/IERC2981.sol";
import "./interfaces/IArtMarketplace.sol";
import "./interfaces/IArtNFT.sol";

/**
 * @title ArtMarketplace
 * @dev Enterprise-grade marketplace for trading art NFTs with auction capabilities
 * @author Art Platform Team
 */
contract ArtMarketplace is
    Initializable,
    ReentrancyGuardUpgradeable,
    PausableUpgradeable,
    AccessControlUpgradeable,
    UUPSUpgradeable,
    IArtMarketplace
{
    using CountersUpgradeable for CountersUpgradeable.Counter;
    using SafeERC20 for IERC20;

    // Role definitions
    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");
    bytes32 public constant OPERATOR_ROLE = keccak256("OPERATOR_ROLE");
    bytes32 public constant UPGRADER_ROLE = keccak256("UPGRADER_ROLE");

    // Constants
    uint256 public constant MAX_PLATFORM_FEE = 1000; // 10% maximum fee
    uint256 public constant BPS_DENOMINATOR = 10000;
    uint256 public constant MIN_BID_INCREMENT_BPS = 500; // 5% minimum increment

    // State variables
    CountersUpgradeable.Counter private _listingIdCounter;
    CountersUpgradeable.Counter private _offerIdCounter;

    mapping(uint256 => Listing) private _listings;
    mapping(uint256 => Offer) private _offers;
    mapping(address => bool) public supportedPaymentTokens;
    mapping(address => mapping(uint256 => uint256[])) private _nftListings; // nftContract => tokenId => listingIds
    mapping(address => uint256[]) private _sellerListings; // seller => listingIds

    // Platform settings
    address public platformTreasury;
    uint256 public platformFeeBps;
    uint256 public minAuctionDuration;
    uint256 public maxAuctionDuration;

    // Escrow for bids and offers
    mapping(address => mapping(address => uint256)) private _escrowBalance; // user => token => amount

    // Custom errors
    error InvalidPrice();
    error InvalidDuration();
    error ListingNotFound();
    error ListingNotActive();
    error UnauthorizedSeller();
    error InsufficientBid();
    error AuctionNotEnded();
    error AuctionEnded();
    error InvalidPaymentToken();
    error TransferFailed();
    error OfferNotFound();
    error OfferExpired();
    error OfferNotActive();

    /// @custom:oz-upgrades-unsafe-allow constructor
    constructor() {
        _disableInitializers();
    }

    /**
     * @dev Initialize the marketplace
     */
    function initialize(
        address _platformTreasury,
        uint256 _platformFeeBps
    ) public initializer {
        __ReentrancyGuard_init();
        __Pausable_init();
        __AccessControl_init();
        __UUPSUpgradeable_init();

        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(ADMIN_ROLE, msg.sender);
        _grantRole(OPERATOR_ROLE, msg.sender);
        _grantRole(UPGRADER_ROLE, msg.sender);

        platformTreasury = _platformTreasury;
        platformFeeBps = _platformFeeBps;
        minAuctionDuration = 1 hours;
        maxAuctionDuration = 30 days;

        // ETH is always supported (address(0))
        supportedPaymentTokens[address(0)] = true;

        // Start IDs from 1
        _listingIdCounter.increment();
        _offerIdCounter.increment();
    }

    /**
     * @dev Create a new listing
     */
    function createListing(
        address nftContract,
        uint256 tokenId,
        uint256 price,
        address paymentToken,
        ListingType listingType,
        uint256 duration
    ) external override nonReentrant whenNotPaused returns (uint256 listingId) {
        // Validation
        if (price == 0) revert InvalidPrice();
        if (!supportedPaymentTokens[paymentToken]) revert InvalidPaymentToken();
        if (listingType != ListingType.FIXED_PRICE) {
            if (duration < minAuctionDuration || duration > maxAuctionDuration) {
                revert InvalidDuration();
            }
        }

        // Check NFT ownership and approval
        IERC721 nft = IERC721(nftContract);
        require(nft.ownerOf(tokenId) == msg.sender, "Not NFT owner");
        require(
            nft.isApprovedForAll(msg.sender, address(this)) || 
            nft.getApproved(tokenId) == address(this),
            "Marketplace not approved"
        );

        // Create listing
        listingId = _listingIdCounter.current();
        _listingIdCounter.increment();

        uint256 endTime = listingType == ListingType.FIXED_PRICE ? 
            0 : block.timestamp + duration;

        _listings[listingId] = Listing({
            listingId: listingId,
            nftContract: nftContract,
            tokenId: tokenId,
            seller: msg.sender,
            price: price,
            paymentToken: paymentToken,
            listingType: listingType,
            status: ListingStatus.ACTIVE,
            startTime: block.timestamp,
            endTime: endTime,
            minBidIncrement: (price * MIN_BID_INCREMENT_BPS) / BPS_DENOMINATOR,
            highestBidder: address(0),
            highestBid: 0,
            royaltyPaid: false
        });

        // Track listings
        _nftListings[nftContract][tokenId].push(listingId);
        _sellerListings[msg.sender].push(listingId);

        emit ListingCreated(
            listingId,
            nftContract,
            tokenId,
            msg.sender,
            price,
            listingType
        );
    }

    /**
     * @dev Buy NFT at fixed price
     */
    function buyNow(uint256 listingId) external payable override nonReentrant whenNotPaused {
        Listing storage listing = _listings[listingId];
        if (listing.listingId == 0) revert ListingNotFound();
        if (listing.status != ListingStatus.ACTIVE) revert ListingNotActive();
        if (listing.listingType != ListingType.FIXED_PRICE) revert InvalidPrice();

        _executeSale(listingId, msg.sender, listing.price);
    }

    /**
     * @dev Place bid on auction
     */
    function placeBid(uint256 listingId) external payable override nonReentrant whenNotPaused {
        Listing storage listing = _listings[listingId];
        if (listing.listingId == 0) revert ListingNotFound();
        if (listing.status != ListingStatus.ACTIVE) revert ListingNotActive();
        if (listing.listingType == ListingType.FIXED_PRICE) revert InvalidPrice();
        if (block.timestamp >= listing.endTime) revert AuctionEnded();

        uint256 bidAmount;
        if (listing.paymentToken == address(0)) {
            bidAmount = msg.value;
        } else {
            // For ERC20 tokens, transfer to escrow
            IERC20 token = IERC20(listing.paymentToken);
            bidAmount = msg.value; // This should be passed as parameter in real implementation
            token.safeTransferFrom(msg.sender, address(this), bidAmount);
        }

        uint256 minBid = listing.highestBid == 0 ? 
            listing.price : 
            listing.highestBid + listing.minBidIncrement;

        if (bidAmount < minBid) revert InsufficientBid();

        // Refund previous bidder
        if (listing.highestBidder != address(0)) {
            _refundBidder(listing);
        }

        // Update listing
        listing.highestBidder = msg.sender;
        listing.highestBid = bidAmount;

        // Store bid in escrow
        _escrowBalance[msg.sender][listing.paymentToken] += bidAmount;

        emit BidPlaced(listingId, msg.sender, bidAmount);
    }

    /**
     * @dev Finalize auction
     */
    function finalizeAuction(uint256 listingId) external override nonReentrant {
        Listing storage listing = _listings[listingId];
        if (listing.listingId == 0) revert ListingNotFound();
        if (listing.status != ListingStatus.ACTIVE) revert ListingNotActive();
        if (listing.listingType == ListingType.FIXED_PRICE) revert InvalidPrice();
        if (block.timestamp < listing.endTime) revert AuctionNotEnded();

        if (listing.highestBidder != address(0)) {
            _executeSale(listingId, listing.highestBidder, listing.highestBid);
        } else {
            listing.status = ListingStatus.EXPIRED;
        }
    }

    /**
     * @dev Cancel listing
     */
    function cancelListing(uint256 listingId) external override nonReentrant {
        Listing storage listing = _listings[listingId];
        if (listing.listingId == 0) revert ListingNotFound();
        if (listing.seller != msg.sender) revert UnauthorizedSeller();
        if (listing.status != ListingStatus.ACTIVE) revert ListingNotActive();

        // Refund highest bidder if auction
        if (listing.highestBidder != address(0)) {
            _refundBidder(listing);
        }

        listing.status = ListingStatus.CANCELLED;
        emit ListingCancelled(listingId, msg.sender);
    }

    /**
     * @dev Make offer on NFT
     */
    function makeOffer(
        address nftContract,
        uint256 tokenId,
        uint256 amount,
        address paymentToken,
        uint256 expiration
    ) external override nonReentrant whenNotPaused returns (uint256 offerId) {
        if (amount == 0) revert InvalidPrice();
        if (!supportedPaymentTokens[paymentToken]) revert InvalidPaymentToken();
        if (expiration <= block.timestamp) revert OfferExpired();

        offerId = _offerIdCounter.current();
        _offerIdCounter.increment();

        // Transfer tokens to escrow
        if (paymentToken == address(0)) {
            require(msg.value == amount, "Incorrect ETH amount");
        } else {
            IERC20(paymentToken).safeTransferFrom(msg.sender, address(this), amount);
        }

        _offers[offerId] = Offer({
            offerId: offerId,
            nftContract: nftContract,
            tokenId: tokenId,
            offerer: msg.sender,
            amount: amount,
            paymentToken: paymentToken,
            expiration: expiration,
            isActive: true
        });

        _escrowBalance[msg.sender][paymentToken] += amount;

        emit OfferMade(offerId, nftContract, tokenId, msg.sender, amount);
    }

    /**
     * @dev Accept offer
     */
    function acceptOffer(uint256 offerId) external override nonReentrant whenNotPaused {
        Offer storage offer = _offers[offerId];
        if (offer.offerId == 0) revert OfferNotFound();
        if (!offer.isActive) revert OfferNotActive();
        if (block.timestamp >= offer.expiration) revert OfferExpired();

        // Check NFT ownership
        IERC721 nft = IERC721(offer.nftContract);
        require(nft.ownerOf(offer.tokenId) == msg.sender, "Not NFT owner");

        // Execute sale
        _executeOfferSale(offerId);
    }

    /**
     * @dev Cancel offer
     */
    function cancelOffer(uint256 offerId) external override nonReentrant {
        Offer storage offer = _offers[offerId];
        if (offer.offerId == 0) revert OfferNotFound();
        if (offer.offerer != msg.sender) revert UnauthorizedSeller();
        if (!offer.isActive) revert OfferNotActive();

        offer.isActive = false;

        // Refund offerer
        _escrowBalance[offer.offerer][offer.paymentToken] -= offer.amount;
        if (offer.paymentToken == address(0)) {
            (bool success, ) = offer.offerer.call{value: offer.amount}("");
            if (!success) revert TransferFailed();
        } else {
            IERC20(offer.paymentToken).safeTransfer(offer.offerer, offer.amount);
        }
    }

    /**
     * @dev Execute sale
     */
    function _executeSale(uint256 listingId, address buyer, uint256 price) internal {
        Listing storage listing = _listings[listingId];
        
        // Calculate fees
        uint256 platformFee = (price * platformFeeBps) / BPS_DENOMINATOR;
        uint256 royaltyAmount = 0;
        address royaltyRecipient = address(0);

        // Get royalty info if supported
        if (IERC165(listing.nftContract).supportsInterface(type(IERC2981).interfaceId)) {
            (royaltyRecipient, royaltyAmount) = IERC2981(listing.nftContract)
                .royaltyInfo(listing.tokenId, price);
        }

        uint256 sellerAmount = price - platformFee - royaltyAmount;

        // Transfer NFT
        IERC721(listing.nftContract).safeTransferFrom(
            listing.seller,
            buyer,
            listing.tokenId
        );

        // Handle payments
        if (listing.paymentToken == address(0)) {
            // ETH payments
            if (platformFee > 0) {
                (bool success, ) = platformTreasury.call{value: platformFee}("");
                if (!success) revert TransferFailed();
            }
            if (royaltyAmount > 0 && royaltyRecipient != address(0)) {
                (bool success, ) = royaltyRecipient.call{value: royaltyAmount}("");
                if (!success) revert TransferFailed();
            }
            (bool success, ) = listing.seller.call{value: sellerAmount}("");
            if (!success) revert TransferFailed();
        } else {
            // ERC20 payments
            IERC20 token = IERC20(listing.paymentToken);
            if (platformFee > 0) {
                token.safeTransfer(platformTreasury, platformFee);
            }
            if (royaltyAmount > 0 && royaltyRecipient != address(0)) {
                token.safeTransfer(royaltyRecipient, royaltyAmount);
            }
            token.safeTransfer(listing.seller, sellerAmount);
        }

        // Update listing status
        listing.status = ListingStatus.SOLD;

        // Remove from escrow if it was a bid
        if (listing.highestBidder == buyer) {
            _escrowBalance[buyer][listing.paymentToken] -= price;
        }

        emit ListingSold(listingId, buyer, price, royaltyAmount, platformFee);
    }

    /**
     * @dev Execute offer sale
     */
    function _executeOfferSale(uint256 offerId) internal {
        Offer storage offer = _offers[offerId];
        
        // Calculate fees (similar to _executeSale)
        uint256 platformFee = (offer.amount * platformFeeBps) / BPS_DENOMINATOR;
        uint256 royaltyAmount = 0;
        address royaltyRecipient = address(0);

        if (IERC165(offer.nftContract).supportsInterface(type(IERC2981).interfaceId)) {
            (royaltyRecipient, royaltyAmount) = IERC2981(offer.nftContract)
                .royaltyInfo(offer.tokenId, offer.amount);
        }

        uint256 sellerAmount = offer.amount - platformFee - royaltyAmount;

        // Transfer NFT
        IERC721(offer.nftContract).safeTransferFrom(
            msg.sender,
            offer.offerer,
            offer.tokenId
        );

        // Handle payments from escrow
        _escrowBalance[offer.offerer][offer.paymentToken] -= offer.amount;
        
        if (offer.paymentToken == address(0)) {
            if (platformFee > 0) {
                (bool success, ) = platformTreasury.call{value: platformFee}("");
                if (!success) revert TransferFailed();
            }
            if (royaltyAmount > 0 && royaltyRecipient != address(0)) {
                (bool success, ) = royaltyRecipient.call{value: royaltyAmount}("");
                if (!success) revert TransferFailed();
            }
            (bool success, ) = msg.sender.call{value: sellerAmount}("");
            if (!success) revert TransferFailed();
        } else {
            IERC20 token = IERC20(offer.paymentToken);
            if (platformFee > 0) {
                token.safeTransfer(platformTreasury, platformFee);
            }
            if (royaltyAmount > 0 && royaltyRecipient != address(0)) {
                token.safeTransfer(royaltyRecipient, royaltyAmount);
            }
            token.safeTransfer(msg.sender, sellerAmount);
        }

        offer.isActive = false;
        emit OfferAccepted(offerId, msg.sender);
    }

    /**
     * @dev Refund bidder
     */
    function _refundBidder(Listing storage listing) internal {
        _escrowBalance[listing.highestBidder][listing.paymentToken] -= listing.highestBid;
        
        if (listing.paymentToken == address(0)) {
            (bool success, ) = listing.highestBidder.call{value: listing.highestBid}("");
            if (!success) revert TransferFailed();
        } else {
            IERC20(listing.paymentToken).safeTransfer(listing.highestBidder, listing.highestBid);
        }
    }

    // View functions
    function getListing(uint256 listingId) external view override returns (Listing memory) {
        return _listings[listingId];
    }

    function getOffer(uint256 offerId) external view override returns (Offer memory) {
        return _offers[offerId];
    }

    function getActiveListings(uint256 offset, uint256 limit) 
        external 
        view 
        override 
        returns (Listing[] memory) 
    {
        // Implementation would require additional indexing for efficiency
        // This is a simplified version
        Listing[] memory listings = new Listing[](limit);
        uint256 count = 0;
        uint256 current = _listingIdCounter.current();
        
        for (uint256 i = 1; i < current && count < limit; i++) {
            if (i <= offset) continue;
            if (_listings[i].status == ListingStatus.ACTIVE) {
                listings[count] = _listings[i];
                count++;
            }
        }
        
        // Resize array
        assembly { mstore(listings, count) }
        return listings;
    }

    function getListingsByNFT(address nftContract, uint256 tokenId) 
        external 
        view 
        override 
        returns (Listing[] memory) 
    {
        uint256[] memory listingIds = _nftListings[nftContract][tokenId];
        Listing[] memory listings = new Listing[](listingIds.length);
        
        for (uint256 i = 0; i < listingIds.length; i++) {
            listings[i] = _listings[listingIds[i]];
        }
        
        return listings;
    }

    function getListingsBySeller(address seller) 
        external 
        view 
        override 
        returns (Listing[] memory) 
    {
        uint256[] memory listingIds = _sellerListings[seller];
        Listing[] memory listings = new Listing[](listingIds.length);
        
        for (uint256 i = 0; i < listingIds.length; i++) {
            listings[i] = _listings[listingIds[i]];
        }
        
        return listings;
    }

    function getOffersByNFT(address nftContract, uint256 tokenId) 
        external 
        view 
        override 
        returns (Offer[] memory) 
    {
        // This would require additional indexing in production
        uint256 current = _offerIdCounter.current();
        uint256 count = 0;
        
        // Count matching offers
        for (uint256 i = 1; i < current; i++) {
            if (_offers[i].nftContract == nftContract && 
                _offers[i].tokenId == tokenId && 
                _offers[i].isActive) {
                count++;
            }
        }
        
        Offer[] memory offers = new Offer[](count);
        uint256 index = 0;
        
        for (uint256 i = 1; i < current && index < count; i++) {
            if (_offers[i].nftContract == nftContract && 
                _offers[i].tokenId == tokenId && 
                _offers[i].isActive) {
                offers[index] = _offers[i];
                index++;
            }
        }
        
        return offers;
    }

    function getPlatformFee() external view override returns (uint256) {
        return platformFeeBps;
    }

    function isListingActive(uint256 listingId) external view override returns (bool) {
        Listing memory listing = _listings[listingId];
        return listing.status == ListingStatus.ACTIVE && 
               (listing.endTime == 0 || block.timestamp < listing.endTime);
    }

    // Admin functions
    function setPlatformFee(uint256 newFee) external override onlyRole(ADMIN_ROLE) {
        require(newFee <= MAX_PLATFORM_FEE, "Fee too high");
        uint256 oldFee = platformFeeBps;
        platformFeeBps = newFee;
        emit PlatformFeeUpdated(oldFee, newFee);
    }

    function setPaymentTokenStatus(address token, bool status) 
        external 
        override 
        onlyRole(ADMIN_ROLE) 
    {
        supportedPaymentTokens[token] = status;
    }

    function emergencyPause() external override onlyRole(ADMIN_ROLE) {
        _pause();
    }

    function emergencyUnpause() external override onlyRole(ADMIN_ROLE) {
        _unpause();
    }

    function _authorizeUpgrade(address newImplementation) 
        internal 
        onlyRole(UPGRADER_ROLE) 
        override 
    {}
} 