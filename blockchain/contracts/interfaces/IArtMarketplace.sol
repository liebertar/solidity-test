// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title IArtMarketplace
 * @dev Interface for Art Marketplace with enterprise trading features
 * @author Art Platform Team
 */
interface IArtMarketplace {
    /**
     * @dev Listing types supported by the marketplace
     */
    enum ListingType {
        FIXED_PRICE,
        AUCTION,
        DUTCH_AUCTION
    }

    /**
     * @dev Listing status
     */
    enum ListingStatus {
        ACTIVE,
        SOLD,
        CANCELLED,
        EXPIRED
    }

    /**
     * @dev Struct for marketplace listings
     */
    struct Listing {
        uint256 listingId;
        address nftContract;
        uint256 tokenId;
        address seller;
        uint256 price;
        address paymentToken; // Address(0) for ETH
        ListingType listingType;
        ListingStatus status;
        uint256 startTime;
        uint256 endTime;
        uint256 minBidIncrement;
        address highestBidder;
        uint256 highestBid;
        bool royaltyPaid;
    }

    /**
     * @dev Struct for offers
     */
    struct Offer {
        uint256 offerId;
        address nftContract;
        uint256 tokenId;
        address offerer;
        uint256 amount;
        address paymentToken;
        uint256 expiration;
        bool isActive;
    }

    // Events
    event ListingCreated(
        uint256 indexed listingId,
        address indexed nftContract,
        uint256 indexed tokenId,
        address seller,
        uint256 price,
        ListingType listingType
    );

    event ListingSold(
        uint256 indexed listingId,
        address indexed buyer,
        uint256 price,
        uint256 royaltyAmount,
        uint256 platformFee
    );

    event BidPlaced(
        uint256 indexed listingId,
        address indexed bidder,
        uint256 bidAmount
    );

    event OfferMade(
        uint256 indexed offerId,
        address indexed nftContract,
        uint256 indexed tokenId,
        address offerer,
        uint256 amount
    );

    event OfferAccepted(
        uint256 indexed offerId,
        address indexed seller
    );

    event ListingCancelled(
        uint256 indexed listingId,
        address indexed seller
    );

    event PlatformFeeUpdated(
        uint256 oldFee,
        uint256 newFee
    );

    // Core Functions
    function createListing(
        address nftContract,
        uint256 tokenId,
        uint256 price,
        address paymentToken,
        ListingType listingType,
        uint256 duration
    ) external returns (uint256 listingId);

    function buyNow(uint256 listingId) external payable;

    function placeBid(uint256 listingId) external payable;

    function finalizeAuction(uint256 listingId) external;

    function cancelListing(uint256 listingId) external;

    function makeOffer(
        address nftContract,
        uint256 tokenId,
        uint256 amount,
        address paymentToken,
        uint256 expiration
    ) external returns (uint256 offerId);

    function acceptOffer(uint256 offerId) external;

    function cancelOffer(uint256 offerId) external;

    // View Functions
    function getListing(uint256 listingId) 
        external 
        view 
        returns (Listing memory);

    function getOffer(uint256 offerId) 
        external 
        view 
        returns (Offer memory);

    function getActiveListings(uint256 offset, uint256 limit) 
        external 
        view 
        returns (Listing[] memory);

    function getListingsByNFT(address nftContract, uint256 tokenId) 
        external 
        view 
        returns (Listing[] memory);

    function getListingsBySeller(address seller) 
        external 
        view 
        returns (Listing[] memory);

    function getOffersByNFT(address nftContract, uint256 tokenId) 
        external 
        view 
        returns (Offer[] memory);

    function getPlatformFee() external view returns (uint256);

    function isListingActive(uint256 listingId) external view returns (bool);

    // Admin Functions
    function setPlatformFee(uint256 newFee) external;

    function setPaymentTokenStatus(address token, bool status) external;

    function emergencyPause() external;

    function emergencyUnpause() external;
} 