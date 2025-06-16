# Blockchain Smart Contracts

Enterprise-grade smart contracts for the art platform, built with Hardhat and following security best practices used by major companies like Robinhood.

## 🏗️ Architecture

Our smart contract system follows the **Hexagonal + DDD** architecture pattern:

- **Domain Layer**: Core business logic in Solidity contracts
- **Infrastructure Layer**: Hardhat setup, deployment scripts, testing
- **Ports & Adapters**: TypeScript interfaces for frontend integration

## 📁 Directory Structure

```
blockchain/
├── contracts/              # Smart contracts
│   ├── interfaces/         # Contract interfaces
│   │   ├── IArtNFT.sol
│   │   └── IArtMarketplace.sol
│   ├── ArtNFT.sol         # Main NFT contract
│   └── ArtMarketplace.sol # Marketplace contract
├── scripts/               # Deployment scripts
│   └── deploy.js
├── test/                  # Contract tests
│   └── ArtNFT.test.js
├── typechain-types/       # Generated TypeScript types
├── deployments/           # Deployment artifacts
├── hardhat.config.ts      # Hardhat configuration
└── package.json
```

## 🚀 Quick Start

### Prerequisites

- Node.js 18+
- npm or yarn
- MetaMask or other Web3 wallet

### Installation

```bash
cd blockchain
npm install
```

### Environment Setup

Create a `.env` file:

```bash
# Private key for deployment (NEVER commit real private keys!)
PRIVATE_KEY=your_private_key_here

# Alchemy API keys
ALCHEMY_API_KEY=your_alchemy_api_key

# Etherscan API key for verification
ETHERSCAN_API_KEY=your_etherscan_api_key

# Gas reporting
REPORT_GAS=false
```

### Compile Contracts

```bash
npm run compile
```

### Run Tests

```bash
npm test
npm run test:coverage
```

### Deploy to Local Network

Start local blockchain:
```bash
npm run node
```

Deploy contracts:
```bash
npm run deploy:local
```

### Deploy to Testnet

```bash
npm run deploy:testnet
```

## 📝 Smart Contracts

### ArtNFT Contract

The main NFT contract with enterprise-grade features:

- **ERC721 Compliant**: Standard NFT functionality
- **ERC2981 Royalties**: Automatic royalty payments
- **Upgradeable**: UUPS proxy pattern for future improvements
- **Access Control**: Role-based permissions (Admin, Minter, Verifier)
- **Pausable**: Emergency stop functionality
- **C2PA Integration**: Content authenticity verification
- **Gas Optimized**: Custom errors, packed structs

#### Key Features:

```solidity
// Mint new artwork NFT
function mintArtwork(
    address to,
    string memory title,
    string memory description,
    string memory imageURI,
    string memory metadataURI,
    uint256 royaltyBps
) external payable returns (uint256 tokenId)

// Verify artwork with C2PA hash
function verifyArtwork(
    uint256 tokenId,
    bytes32 c2paHash
) external

// Update royalty information
function updateRoyalty(
    uint256 tokenId,
    uint256 royaltyBps
) external
```

### ArtMarketplace Contract

Sophisticated marketplace with trading capabilities:

- **Multiple Listing Types**: Fixed price, auctions, Dutch auctions
- **Multi-Token Support**: ETH and ERC20 payments
- **Escrow System**: Secure bid and offer handling
- **Royalty Enforcement**: Automatic creator payments
- **Gas Efficient**: Optimized for high-volume trading

#### Key Features:

```solidity
// Create marketplace listing
function createListing(
    address nftContract,
    uint256 tokenId,
    uint256 price,
    address paymentToken,
    ListingType listingType,
    uint256 duration
) external returns (uint256 listingId)

// Buy NFT immediately
function buyNow(uint256 listingId) external payable

// Place bid on auction
function placeBid(uint256 listingId) external payable

// Make offer on any NFT
function makeOffer(
    address nftContract,
    uint256 tokenId,
    uint256 amount,
    address paymentToken,
    uint256 expiration
) external returns (uint256 offerId)
```

## 🔧 Configuration

### Network Configuration

Supports multiple networks:

- **Mainnet**: Production Ethereum
- **Sepolia**: Ethereum testnet
- **Polygon**: Layer 2 scaling
- **Mumbai**: Polygon testnet
- **Localhost**: Local development

### Gas Optimization

- Custom errors instead of require strings
- Packed structs for storage efficiency
- Batch operations where possible
- Efficient event emission

### Security Features

- **Reentrancy Protection**: All state-changing functions
- **Access Control**: Role-based permissions
- **Input Validation**: Comprehensive parameter checking
- **Emergency Pause**: Circuit breaker pattern
- **Upgradeable Contracts**: Safe upgrade mechanism

## 🧪 Testing

Comprehensive test suite covering:

- **Unit Tests**: Individual function testing
- **Integration Tests**: Contract interaction testing
- **Security Tests**: Attack vector validation
- **Gas Tests**: Optimization verification

### Test Coverage

```bash
npm run test:coverage
```

Target: 100% line coverage, 95% branch coverage

### Security Testing

```bash
npm run lint          # Solidity linting
npm run size          # Contract size analysis
```

## 📊 Deployment

### Deployment Process

1. **Compile contracts**
2. **Run tests**
3. **Deploy with proxy**
4. **Verify on Etherscan**
5. **Configure permissions**
6. **Save deployment info**

### Deployment Artifacts

Deployment information is saved in `deployments/[network].json`:

```json
{
  "network": "sepolia",
  "deployer": "0x...",
  "contracts": {
    "ArtNFT": {
      "address": "0x...",
      "implementation": "0x...",
      "admin": "0x..."
    },
    "ArtMarketplace": {
      "address": "0x...",
      "implementation": "0x...",
      "admin": "0x..."
    }
  },
  "timestamp": "2024-01-01T00:00:00.000Z"
}
```

### Upgrading Contracts

```bash
# Upgrade NFT contract
npx hardhat run scripts/upgrade-nft.js --network sepolia

# Upgrade Marketplace contract
npx hardhat run scripts/upgrade-marketplace.js --network sepolia
```

## 🔐 Security

### Best Practices

- **Never commit private keys**
- **Use hardware wallets for mainnet**
- **Verify all deployments on Etherscan**
- **Test thoroughly on testnets**
- **Follow OpenZeppelin patterns**

### Security Checklist

- [ ] Reentrancy guards on all external calls
- [ ] Access control on admin functions
- [ ] Input validation on all parameters
- [ ] Emergency pause functionality
- [ ] Upgrade mechanism security
- [ ] Event emission for all state changes

## 🔗 Integration

### Backend Integration

The smart contracts integrate with the FastAPI backend through:

```python
# Web3 client implementation
from app.adapters.web3.web3_client_impl import Web3ClientImpl

# Create wallet
address, private_key = await web3_client.create_wallet("password")

# Mint NFT
token_id, tx_hash = await web3_client.mint_nft(
    contract_address,
    minter_private_key,
    to_address,
    metadata,
    asset_id
)
```

### Frontend Integration

TypeScript types are auto-generated for frontend integration:

```typescript
import { ArtNFT, ArtMarketplace } from './typechain-types'

// Contract instances
const artNFT = ArtNFT__factory.connect(address, provider)
const marketplace = ArtMarketplace__factory.connect(address, provider)
```

## 📈 Monitoring

### Events

All contracts emit comprehensive events for monitoring:

- **ArtworkMinted**: NFT creation
- **ArtworkVerified**: Authenticity confirmation
- **ListingCreated**: Marketplace listing
- **ListingSold**: Successful sale

### Metrics

Track important metrics:

- Total NFTs minted
- Marketplace volume
- Average sale price
- Gas usage trends

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add comprehensive tests
4. Run security analysis
5. Submit pull request

## 📞 Support

For technical support:

- GitHub Issues
- Documentation: [docs/](../docs/)
- Community Discord

## 📜 License

MIT License - see [LICENSE](../LICENSE) for details.

---

Built with ❤️ using enterprise-grade practices from companies like Robinhood, OpenSea, and Uniswap. 

# NEVER commit private keys, wallets, or secrets!
*.key
*.pem
*wallet*
*mnemonic*
*seed*
*private*
keystore/
wallets/
secrets/

.env
.env.*
!.env.example  # Allow example files
!.env.template 