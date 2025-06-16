# Enterprise Smart Contract & Wallet Platform

A production-ready blockchain wallet and smart contract platform built with **blockchain-native architecture**, featuring enterprise-grade wallet management, smart contract deployment, and multi-chain support like Robinhood, Binance, and Coinbase.

## 🏗️ Blockchain-Native Architecture

This platform follows **blockchain-native patterns** used by major financial platforms:

```
┌─────────────────────────────────────┐
│           API Layer                 │  ← REST/GraphQL endpoints
├─────────────────────────────────────┤
│         Wallet Layer                │  ← Wallet management, signing
├─────────────────────────────────────┤
│       Smart Contract Layer         │  ← Contract deployment, interaction
├─────────────────────────────────────┤
│       Transaction Layer             │  ← TX building, broadcasting, monitoring
├─────────────────────────────────────┤
│         Network Layer               │  ← Multi-chain abstraction
├─────────────────────────────────────┤
│        Protocol Layer               │  ← Ethereum, Polygon, Arbitrum, etc.
└─────────────────────────────────────┘
```

## 🛠️ Tech Stack

### Backend
- **FastAPI**: High-performance async Python framework
- **Web3.py**: Ethereum blockchain interaction
- **SQLAlchemy**: Database ORM with async support
- **Pydantic**: Data validation and blockchain types
- **Redis**: Caching and rate limiting

### Blockchain
- **Hardhat**: Ethereum development environment
- **Solidity**: Smart contract language
- **OpenZeppelin**: Secure, upgradeable contracts
- **Ethers.js**: Ethereum library for testing

### Security & Infrastructure
- **Private Key Encryption**: Fernet encryption for key storage
- **Rate Limiting**: Blockchain operation throttling
- **Multi-Signature**: Enterprise-grade access control
- **Docker**: Containerized deployment

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 18+
- Docker & Docker Compose
- Git
- **uv** (fast Python package installer): `curl -LsSf https://astral.sh/uv/install.sh | sh`

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd smart-contract-platform
```

2. **Setup Environment**
```bash
# Copy environment files
cp .env.example .env
cp blockchain/.env.example blockchain/.env

# Configure your settings (RPC URLs, private keys, etc.)
```

3. **Setup Backend**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
uv pip install -r requirements.txt
```

4. **Setup Smart Contracts**
```bash
cd blockchain
npm install
```

5. **Start Services**
```bash
# Start database and Redis
docker-compose up -d postgres redis

# Start backend
cd backend && uvicorn app.main:app --reload

# Compile contracts
cd blockchain && npx hardhat compile
```

## 🧪 Testing Guide

### Prerequisites
- Local blockchain node (Hardhat Network)
- Test wallets with testnet ETH
- All dependencies installed
- **Python virtual environment activated** (required for all backend tests)

### Smart Contract Testing

```bash
cd blockchain

# Run all tests
npm test

# Run specific test file
npm test test/TokenContract.test.js

# Run with gas reporting
npm run test:gas

# Run with coverage
npm run coverage

# Test on specific network
npm test --network goerli
```

**What gets tested:**
- Contract deployment and initialization
- Token minting and burning
- Access control and permissions
- Reentrancy protection
- Gas optimization
- Upgrade mechanisms

### Python Backend Testing

```bash
cd backend

# Activate virtual environment first
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test categories
pytest tests/unit/                    # Unit tests only
pytest tests/integration/             # Integration tests only
pytest tests/security/                # Security tests only
pytest -m "not slow"                  # Skip slow tests

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_wallet_manager.py

# Run specific test function
pytest tests/unit/test_wallet_manager.py::test_create_wallet
```

**What gets tested:**
- Wallet creation and management
- Transaction signing and broadcasting
- Smart contract interactions
- Multi-chain operations
- Error handling and validation
- Security (private key protection)
- Rate limiting
- Input validation

### Integration Testing

```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Full end-to-end tests (requires testnet)
pytest tests/integration/ -m integration

# Test with real blockchain (slow)
pytest tests/integration/test_e2e_transfer.py
```

**What gets tested:**
- Complete wallet-to-wallet transfers
- Contract deployment workflows
- Multi-chain compatibility
- Real blockchain interactions

### Performance Testing

```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Load testing
pytest tests/performance/ -m performance

# Concurrent operations test
pytest tests/performance/test_concurrent_wallets.py

# Transaction throughput test
pytest tests/performance/test_transaction_throughput.py
```

### Security Testing

```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Security vulnerability tests
pytest tests/security/ -m security

# Private key protection test
pytest tests/security/test_private_key_security.py

# Rate limiting test
pytest tests/security/test_rate_limiting.py
```

### Test Configuration

The project uses `pytest.ini` with these markers:
- `unit`: Fast unit tests
- `integration`: Tests requiring external services
- `performance`: Load and performance tests
- `security`: Security vulnerability tests
- `slow`: Tests taking >30 seconds

Run specific test types:
```bash
cd backend && source venv/bin/activate  # Activate venv first

pytest -m unit          # Only unit tests
pytest -m "not slow"    # Skip slow tests
pytest -m security      # Only security tests
```

### Adding New Tests

1. **Smart Contract Tests** (JavaScript/Hardhat):
```javascript
// test/YourContract.test.js
describe("YourContract", function () {
  let contract, owner, user1;
  
  beforeEach(async function () {
    [owner, user1] = await ethers.getSigners();
    const Contract = await ethers.getContractFactory("YourContract");
    contract = await Contract.deploy();
  });
  
  it("should do something", async function () {
    // Test implementation
  });
});
```

2. **Python Backend Tests**:
```python
# tests/unit/test_your_feature.py
@pytest.mark.asyncio
async def test_your_feature():
    # Test implementation
    pass
```

## 📁 Project Structure

```
project-root/
├── blockchain/                 # Smart contracts & Hardhat setup
│   ├── contracts/             # Solidity contracts
│   ├── test/                  # Contract tests
│   └── scripts/               # Deployment scripts
├── wallet/                    # Wallet management
├── chains/                    # Multi-chain support
├── transactions/              # Transaction processing
├── api/                       # REST API endpoints
├── tests/                     # Python tests
│   ├── unit/                  # Unit tests
│   ├── integration/           # Integration tests
│   ├── performance/           # Performance tests
│   └── security/              # Security tests
├── .cursor/                   # Modern Cursor IDE rules
│   └── rules/                 # Organized rule files
└── docs/                      # Documentation
```

## 🔗 Key Features

### Wallet Management
- **HD Wallet Creation**: Hierarchical deterministic wallets
- **Multi-Chain Support**: Ethereum, Polygon, Arbitrum
- **Private Key Security**: Encrypted storage with Fernet
- **Transaction Signing**: Secure transaction signing
- **Balance Tracking**: Real-time balance monitoring

### Smart Contract Platform
- **Contract Deployment**: Deploy contracts across chains
- **Method Interaction**: Call contract functions safely
- **Gas Optimization**: Efficient gas usage patterns
- **Upgradeable Contracts**: UUPS proxy pattern
- **Access Control**: Role-based permissions

### Enterprise Security
- **Rate Limiting**: Prevent spam and abuse
- **Input Validation**: Comprehensive parameter checking
- **Audit Logging**: Structured logging for compliance
- **Error Handling**: Graceful failure management
- **Multi-Signature**: Enterprise access controls

## 📊 Why Combine Smart Contracts + Wallets?

This is the **industry standard** approach used by major platforms:

- **Robinhood**: Unified wallet + trading interface
- **Binance**: Integrated wallet + DEX contracts  
- **Coinbase**: Wallet + DeFi protocol integration
- **MetaMask**: Wallet + dApp interaction layer

### Benefits:
- **Seamless UX**: One-click transactions
- **Security**: Controlled contract interactions
- **Scalability**: Shared blockchain infrastructure
- **Compliance**: Unified transaction monitoring
- **Revenue**: Platform fee integration

## 🔧 Expandability Features

### Chain Adapter Pattern
```python
# Easy to add new blockchains
class ArbitrumAdapter(ChainAdapter):
    async def send_transaction(self, tx_params: TxParams) -> TransactionHash:
        # Arbitrum-specific implementation
        pass

# Register new chains
NETWORKS = {
    "ethereum": EthereumAdapter(),
    "polygon": PolygonAdapter(),
    "arbitrum": ArbitrumAdapter(),  # Easy to add
}
```

### Wallet Provider System
```python
# Support different wallet types
class HardwareWalletProvider(WalletProvider):
    async def create_wallet(self) -> Wallet:
        # Hardware wallet integration
        pass
```

### Plugin Architecture
```python
# Add new features as plugins
class StakingPlugin(FeaturePlugin):
    async def execute(self, context: Context) -> Result:
        # Staking functionality
        pass
```

## 🚀 Blockchain-Native Patterns

### Transaction Builder Pattern
```python
# Fluent API for building transactions
tx = (TransactionBuilder(chain_id=1)
      .to_address(recipient)
      .value(amount_wei)
      .gas_limit(21000)
      .build())
```

### Multi-Chain Abstraction
```python
# Same interface across chains
class ChainProvider:
    async def get_balance(self, address: WalletAddress) -> int:
        # Works on any supported chain
        pass
```

### Secure Key Management
```python
# Never expose private keys
class SecureKeyStore:
    async def sign_transaction(self, address: Address, tx: TxParams) -> bytes:
        # Private key never leaves this class
        pass
```

## 📖 Documentation

- [Smart Contracts](./blockchain/README.md)
- [Wallet Management](./wallet/README.md)
- [API Documentation](./api/README.md)
- [Testing Guide](#-testing-guide)
- [Cursor IDE Rules](./.cursor/rules/)

## 🔐 Security Standards

Following **enterprise blockchain security**:

- Private keys encrypted with Fernet
- Rate limiting on all blockchain operations
- Input validation for all addresses/amounts
- Comprehensive error handling
- Audit trails for all operations
- Multi-signature for admin functions
- Reentrancy protection in contracts
- Access control with OpenZeppelin

## 🎯 Testing Checklist

Before deployment, ensure:
- [ ] All unit tests pass (>95% coverage)
- [ ] Integration tests pass on testnet
- [ ] Security tests detect no vulnerabilities
- [ ] Performance tests meet benchmarks
- [ ] Gas optimization verified
- [ ] Private key security confirmed
- [ ] Rate limiting functional
- [ ] Multi-chain compatibility tested

## 🤝 Contributing

1. Follow the [Cursor IDE Rules](./.cursor/rules/)
2. Create a feature branch
3. Add comprehensive tests (unit + integration)
4. Run full test suite: `npm test && (cd backend && source venv/bin/activate && pytest)`
5. Verify security tests pass
6. Submit pull request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Built for Enterprise**: Following blockchain-native patterns from Robinhood, Binance, and Coinbase for production-ready smart contract and wallet infrastructure. 