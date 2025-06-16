# Blockchain Architecture Rules

## Project Vision
Enterprise-grade blockchain wallet and smart contract system following patterns from Robinhood, Binance, and Coinbase. Focus on blockchain-native architecture, not generic application patterns.

## Blockchain-Native Architecture

### Layer Structure (Like Coinbase/Binance)
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

### Core Components

#### 1. Wallet Management
```python
class WalletManager:
    async def create_wallet(self, chain: Chain) -> Wallet
    async def import_wallet(self, private_key: str, chain: Chain) -> Wallet
    async def sign_transaction(self, wallet: Wallet, tx: Transaction) -> SignedTx
    async def get_balance(self, wallet: Wallet, token: Optional[Token]) -> Balance
```

#### 2. Smart Contract Interface
```python
class ContractManager:
    async def deploy_contract(self, bytecode: str, args: List) -> Contract
    async def call_contract(self, contract: Contract, method: str, args: List) -> Any
    async def estimate_gas(self, contract: Contract, method: str, args: List) -> int
```

#### 3. Transaction Processing
```python
class TransactionProcessor:
    async def build_transaction(self, tx_data: TxData) -> Transaction
    async def broadcast_transaction(self, signed_tx: SignedTx) -> TxHash
    async def monitor_transaction(self, tx_hash: TxHash) -> TxStatus
```

#### 4. Multi-Chain Support
```python
class ChainProvider:
    async def get_chain_config(self, chain_id: int) -> ChainConfig
    async def switch_chain(self, chain: Chain) -> bool
    async def get_supported_chains() -> List[Chain]
```

## Directory Structure (Blockchain-Focused)
```
project/
├── blockchain/              # Smart contracts
│   ├── contracts/          # Solidity contracts
│   ├── deployments/        # Deployment configs
│   └── tests/              # Contract tests
├── wallet/                 # Wallet management
│   ├── keystore/           # Key management
│   ├── signing/            # Transaction signing
│   └── recovery/           # Wallet recovery
├── chains/                 # Multi-chain support
│   ├── ethereum/           # Ethereum specific
│   ├── polygon/            # Polygon specific
│   └── arbitrum/           # Arbitrum specific
├── transactions/           # Transaction processing
│   ├── builder/            # TX building
│   ├── broadcaster/        # TX broadcasting
│   └── monitor/            # TX monitoring
└── api/                    # REST API endpoints
    ├── wallet/             # Wallet endpoints
    ├── contracts/          # Contract endpoints
    └── transactions/       # Transaction endpoints
```

## Blockchain Design Patterns

### 1. Chain Abstraction Pattern
```python
# Abstract away chain differences
class ChainAdapter(ABC):
    @abstractmethod
    async def send_transaction(self, tx: Transaction) -> TxResult
    
class EthereumAdapter(ChainAdapter):
    async def send_transaction(self, tx: Transaction) -> TxResult:
        # Ethereum-specific implementation
        
class PolygonAdapter(ChainAdapter):
    async def send_transaction(self, tx: Transaction) -> TxResult:
        # Polygon-specific implementation
```

### 2. Wallet Provider Pattern
```python
# Support multiple wallet types
class WalletProvider(ABC):
    @abstractmethod
    async def create_wallet(self) -> Wallet

class HDWalletProvider(WalletProvider):
    # Hierarchical Deterministic wallets
    
class HardwareWalletProvider(WalletProvider):
    # Hardware wallet integration
```

### 3. Transaction Builder Pattern
```python
# Build complex transactions
class TransactionBuilder:
    def __init__(self, chain: Chain):
        self.chain = chain
        self.tx_data = {}
    
    def to(self, address: Address) -> 'TransactionBuilder':
        self.tx_data['to'] = address
        return self
    
    def value(self, amount: Amount) -> 'TransactionBuilder':
        self.tx_data['value'] = amount
        return self
    
    def gas_limit(self, limit: int) -> 'TransactionBuilder':
        self.tx_data['gas'] = limit
        return self
    
    async def build(self) -> Transaction:
        return Transaction(self.tx_data)
```

## Security Patterns (Robinhood/Binance Level)

### 1. Multi-Signature Security
```solidity
contract MultiSigWallet {
    mapping(address => bool) public isOwner;
    uint256 public required;
    
    modifier onlyOwner() {
        require(isOwner[msg.sender], "Not owner");
        _;
    }
    
    function executeTransaction(
        address to,
        uint256 value,
        bytes memory data,
        bytes[] memory signatures
    ) external {
        require(signatures.length >= required, "Not enough signatures");
        // Execute after validation
    }
}
```

### 2. Rate Limiting for Blockchain Operations
```python
class RateLimiter:
    async def check_transaction_rate(self, address: Address) -> bool:
        # Prevent spam transactions
        
    async def check_wallet_creation_rate(self, ip: str) -> bool:
        # Prevent wallet spam
```

## Performance Patterns

### 1. Transaction Batching
```python
class TransactionBatcher:
    async def batch_transactions(self, txs: List[Transaction]) -> BatchedTx:
        # Combine multiple transactions for gas efficiency
```

### 2. Chain Data Caching
```python
class ChainDataCache:
    async def cache_block_data(self, block: Block) -> None:
        # Cache blockchain data for faster access
        
    async def cache_contract_state(self, contract: Contract) -> None:
        # Cache contract state
```

## Quality Gates

### Blockchain-Specific Requirements
- [ ] All transactions properly signed
- [ ] Gas estimation implemented
- [ ] Chain compatibility verified
- [ ] Private keys never logged
- [ ] Smart contracts audited
- [ ] Multi-chain support tested

### Never Allow
- Private keys in logs or responses
- Unsigned transactions
- Hardcoded gas prices
- Missing error handling for chain failures
- Unbounded loops in contracts
- Missing access controls

Remember: We're building blockchain infrastructure like Robinhood and Binance - focus on blockchain-native patterns, not generic application architecture. 