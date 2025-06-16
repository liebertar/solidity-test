# Python Blockchain Backend Rules

Apply to: `wallet/**/*.py`, `chains/**/*.py`, `transactions/**/*.py`, `api/**/*.py`

## Blockchain-Specific Code Style

### Type Hints for Blockchain Types
```python
from typing import Optional, List, Dict, Any, Union, Tuple
from dataclasses import dataclass
from abc import ABC, abstractmethod
from eth_typing import Address, Hash32, ChecksumAddress
from web3.types import TxParams, TxReceipt

# Blockchain-specific types
TokenId = int
ChainId = int  
BlockNumber = int
GasPrice = int
Nonce = int
TransactionHash = str
PrivateKey = str  # Never log this!
```

### Wallet Management Patterns
```python
@dataclass(frozen=True)
class WalletAddress:
    """Wallet address with validation"""
    value: ChecksumAddress
    
    def __post_init__(self):
        if not self.value.startswith('0x') or len(self.value) != 42:
            raise ValueError("Invalid address format")

@dataclass(frozen=True)
class Wallet:
    """Wallet with private key (NEVER LOG!)"""
    address: WalletAddress
    private_key: PrivateKey  # Mark as sensitive
    chain_id: ChainId
    
    def __repr__(self) -> str:
        # Never expose private key in repr
        return f"Wallet(address={self.address.value}, chain_id={self.chain_id})"

class WalletManager:
    """Enterprise wallet management"""
    
    async def create_wallet(self, chain_id: ChainId, password: str) -> Wallet:
        """Create new HD wallet"""
        # Implementation with secure key generation
        pass
    
    async def import_wallet(
        self, 
        private_key: PrivateKey, 
        chain_id: ChainId
    ) -> Wallet:
        """Import existing wallet"""
        # Validate private key format
        pass
    
    async def sign_transaction(
        self, 
        wallet: Wallet, 
        tx_params: TxParams
    ) -> bytes:
        """Sign transaction with wallet"""
        # Never log private keys!
        pass
```

### Smart Contract Interaction
```python
@dataclass(frozen=True)
class ContractAddress:
    """Smart contract address"""
    value: ChecksumAddress
    chain_id: ChainId
    
@dataclass
class ContractCall:
    """Contract method call parameters"""
    contract_address: ContractAddress
    method_name: str
    args: List[Any]
    gas_limit: Optional[int] = None
    gas_price: Optional[GasPrice] = None

class ContractManager:
    """Smart contract interaction"""
    
    async def deploy_contract(
        self,
        bytecode: str,
        constructor_args: List[Any],
        deployer_wallet: Wallet
    ) -> Tuple[ContractAddress, TransactionHash]:
        """Deploy new contract"""
        pass
    
    async def call_contract_method(
        self,
        contract_call: ContractCall,
        caller_wallet: Optional[Wallet] = None
    ) -> Any:
        """Call contract method (read or write)"""
        pass
    
    async def estimate_gas(self, contract_call: ContractCall) -> int:
        """Estimate gas for contract call"""
        pass
```

### Transaction Processing
```python
@dataclass
class TransactionBuilder:
    """Build blockchain transactions"""
    chain_id: ChainId
    
    def to_address(self, address: WalletAddress) -> 'TransactionBuilder':
        self._to = address.value
        return self
    
    def value(self, amount_wei: int) -> 'TransactionBuilder':
        self._value = amount_wei
        return self
    
    def gas_limit(self, limit: int) -> 'TransactionBuilder':
        self._gas = limit
        return self
    
    def gas_price(self, price: GasPrice) -> 'TransactionBuilder':
        self._gas_price = price
        return self
    
    async def build(self) -> TxParams:
        """Build transaction parameters"""
        return {
            'to': self._to,
            'value': self._value,
            'gas': self._gas,
            'gasPrice': self._gas_price,
            'chainId': self.chain_id,
            'nonce': await self._get_nonce()
        }

class TransactionProcessor:
    """Handle transaction lifecycle"""
    
    async def build_transaction(
        self, 
        tx_data: Dict[str, Any]
    ) -> TxParams:
        """Build transaction from data"""
        pass
    
    async def broadcast_transaction(
        self, 
        signed_tx: bytes
    ) -> TransactionHash:
        """Broadcast to network"""
        pass
    
    async def monitor_transaction(
        self, 
        tx_hash: TransactionHash
    ) -> TxReceipt:
        """Monitor transaction status"""
        pass
```

### Multi-Chain Support
```python
@dataclass(frozen=True)
class ChainConfig:
    """Blockchain configuration"""
    chain_id: ChainId
    name: str
    rpc_url: str
    explorer_url: str
    native_token: str
    gas_price_gwei: float

class ChainProvider:
    """Multi-chain abstraction"""
    
    async def get_chain_config(self, chain_id: ChainId) -> ChainConfig:
        """Get chain configuration"""
        pass
    
    async def get_supported_chains(self) -> List[ChainConfig]:
        """List all supported chains"""
        pass
    
    async def switch_chain(self, chain_id: ChainId) -> bool:
        """Switch to different chain"""
        pass

# Chain adapters for different protocols
class ChainAdapter(ABC):
    """Abstract chain adapter"""
    
    @abstractmethod
    async def send_transaction(self, tx_params: TxParams) -> TransactionHash:
        pass
    
    @abstractmethod
    async def get_balance(self, address: WalletAddress) -> int:
        pass

class EthereumAdapter(ChainAdapter):
    """Ethereum-specific implementation"""
    
    async def send_transaction(self, tx_params: TxParams) -> TransactionHash:
        # Ethereum-specific logic
        pass

class PolygonAdapter(ChainAdapter):
    """Polygon-specific implementation"""
    
    async def send_transaction(self, tx_params: TxParams) -> TransactionHash:
        # Polygon-specific logic (similar to Ethereum but different gas)
        pass
```

## Security Patterns

### Private Key Handling
```python
import os
from cryptography.fernet import Fernet

class SecureKeyStore:
    """Secure private key storage"""
    
    def __init__(self):
        self.encryption_key = os.environ['KEY_ENCRYPTION_SECRET']
        self.fernet = Fernet(self.encryption_key)
    
    async def store_private_key(
        self, 
        address: WalletAddress, 
        private_key: PrivateKey
    ) -> None:
        """Store encrypted private key"""
        encrypted_key = self.fernet.encrypt(private_key.encode())
        # Store in secure database
        # NEVER log private key!
        
    async def retrieve_private_key(
        self, 
        address: WalletAddress
    ) -> PrivateKey:
        """Retrieve and decrypt private key"""
        # Get from secure database
        # Decrypt and return
        # NEVER log private key!
        pass
```

### Rate Limiting
```python
from asyncio import sleep
from typing import Dict
import time

class BlockchainRateLimiter:
    """Rate limit blockchain operations"""
    
    def __init__(self):
        self._request_counts: Dict[str, List[float]] = {}
        self._max_requests_per_minute = 60
    
    async def check_rate_limit(self, key: str) -> bool:
        """Check if request is within rate limit"""
        now = time.time()
        minute_ago = now - 60
        
        if key not in self._request_counts:
            self._request_counts[key] = []
        
        # Remove old requests
        self._request_counts[key] = [
            req_time for req_time in self._request_counts[key] 
            if req_time > minute_ago
        ]
        
        if len(self._request_counts[key]) >= self._max_requests_per_minute:
            return False
        
        self._request_counts[key].append(now)
        return True
```

### Input Validation
```python
from pydantic import BaseModel, validator

class TransferRequest(BaseModel):
    """Validate transfer requests"""
    from_address: str
    to_address: str
    amount: int
    chain_id: int
    
    @validator('from_address', 'to_address')
    def validate_address(cls, v):
        if not v.startswith('0x') or len(v) != 42:
            raise ValueError('Invalid Ethereum address')
        return v.lower()
    
    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be positive')
        return v
    
    @validator('chain_id')
    def validate_chain_id(cls, v):
        if v not in [1, 5, 137, 80001]:  # Mainnet, Goerli, Polygon, Mumbai
            raise ValueError('Unsupported chain ID')
        return v
```

## Error Handling

### Blockchain-Specific Exceptions
```python
class BlockchainError(Exception):
    """Base blockchain error"""
    pass

class InsufficientBalanceError(BlockchainError):
    """Not enough balance for transaction"""
    pass

class TransactionFailedError(BlockchainError):
    """Transaction failed on blockchain"""
    
    def __init__(self, tx_hash: TransactionHash, reason: str):
        self.tx_hash = tx_hash
        self.reason = reason
        super().__init__(f"Transaction {tx_hash} failed: {reason}")

class ContractCallError(BlockchainError):
    """Contract call failed"""
    pass

class NetworkConnectionError(BlockchainError):
    """Network connection issues"""
    pass

# Usage in services
async def transfer_tokens(
    from_wallet: Wallet,
    to_address: WalletAddress, 
    amount: int
) -> TransactionHash:
    """Transfer tokens with proper error handling"""
    try:
        balance = await get_balance(from_wallet.address)
        if balance < amount:
            raise InsufficientBalanceError(
                f"Balance {balance} < required {amount}"
            )
        
        # Build and send transaction
        tx_hash = await send_transaction(...)
        return tx_hash
        
    except Exception as e:
        logger.error(
            "Transfer failed",
            from_address=from_wallet.address.value,
            to_address=to_address.value,
            amount=amount,
            error=str(e)
        )
        raise
```

## Logging Standards

### Structured Logging for Blockchain
```python
import structlog

logger = structlog.get_logger(__name__)

# Transaction logging
logger.info(
    "Transaction processed",
    transaction_hash=tx_hash,
    from_address=from_addr.value,
    to_address=to_addr.value,
    amount=amount,
    gas_used=gas_used,
    block_number=block_number,
    chain_id=chain_id
)

# Wallet operations (NEVER log private keys!)
logger.info(
    "Wallet created",
    address=wallet.address.value,
    chain_id=wallet.chain_id,
    # private_key=wallet.private_key  # NEVER DO THIS!
)

# Contract interactions
logger.info(
    "Contract deployed",
    contract_address=contract_addr.value,
    deployer=deployer.value,
    gas_used=gas_used,
    transaction_hash=tx_hash
)
```

## Testing Patterns

### Blockchain Testing
```python
import pytest
from unittest.mock import Mock, AsyncMock

@pytest.fixture
async def mock_wallet():
    """Mock wallet for testing"""
    return Wallet(
        address=WalletAddress("0x742d35Cc6634C0532925a3b8D91D3031AC7b15Bc"),
        private_key="0x" + "a" * 64,  # Fake key for testing
        chain_id=1337  # Local testnet
    )

@pytest.mark.asyncio
async def test_wallet_creation():
    """Test wallet creation"""
    wallet_manager = WalletManager()
    
    wallet = await wallet_manager.create_wallet(
        chain_id=1337,
        password="test123"
    )
    
    assert wallet.address.value.startswith("0x")
    assert len(wallet.address.value) == 42
    assert wallet.chain_id == 1337

@pytest.mark.asyncio
async def test_contract_deployment():
    """Test contract deployment"""
    contract_manager = ContractManager()
    
    # Mock Web3 client
    mock_web3 = Mock()
    mock_web3.eth.send_raw_transaction = AsyncMock(return_value="0xabc123")
    
    contract_addr, tx_hash = await contract_manager.deploy_contract(
        bytecode="0x608060405234801561001057600080fd5b50",
        constructor_args=[],
        deployer_wallet=mock_wallet
    )
    
    assert isinstance(contract_addr, ContractAddress)
    assert tx_hash.startswith("0x")
```

## Performance Optimization

### Connection Pooling
```python
from web3 import Web3
from web3.providers import HTTPProvider

class Web3Pool:
    """Connection pool for Web3 instances"""
    
    def __init__(self, rpc_url: str, pool_size: int = 10):
        self.rpc_url = rpc_url
        self.pool_size = pool_size
        self._pool = []
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Initialize connection pool"""
        for _ in range(self.pool_size):
            provider = HTTPProvider(self.rpc_url)
            web3 = Web3(provider)
            self._pool.append(web3)
    
    async def get_connection(self) -> Web3:
        """Get Web3 connection from pool"""
        return self._pool.pop() if self._pool else Web3(HTTPProvider(self.rpc_url))
    
    async def return_connection(self, web3: Web3):
        """Return connection to pool"""
        if len(self._pool) < self.pool_size:
            self._pool.append(web3)
```

## Security Requirements

### Critical Security Rules
- [ ] NEVER log private keys anywhere
- [ ] Always encrypt private keys at rest
- [ ] Validate all addresses before use
- [ ] Rate limit all blockchain operations
- [ ] Use environment variables for sensitive config
- [ ] Implement proper error handling for failed transactions
- [ ] Always estimate gas before sending transactions
- [ ] Validate chain IDs for all operations

### Never Allow
- Private keys in logs, responses, or error messages
- Hardcoded RPC URLs or contract addresses
- Missing rate limiting on expensive operations
- Unsigned transactions being broadcast
- Missing input validation on addresses/amounts
- Synchronous blockchain calls in request handlers

## Naming Conventions
- Files: `snake_case.py`
- Classes: `PascalCase`  
- Functions/methods: `snake_case`
- Constants: `UPPER_CASE`
- Private methods: `_snake_case` 