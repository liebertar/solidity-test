# Testing Rules

Apply to: `tests/**/*.py`, `blockchain/test/**/*.js`

## Testing Philosophy

Follow enterprise testing standards like Robinhood/Binance:
- Unit tests for business logic  
- Integration tests for blockchain interactions
- End-to-end tests for complete workflows
- Security tests for vulnerability scanning
- Performance tests for gas optimization

## Smart Contract Testing (Hardhat/JavaScript)

### Test Structure
```javascript
const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("TokenContract", function () {
  let contract, owner, user1, user2;
  
  beforeEach(async function () {
    // Deploy fresh contract for each test
    const TokenContract = await ethers.getContractFactory("TokenContract");
    [owner, user1, user2] = await ethers.getSigners();
    
    contract = await TokenContract.deploy("TestToken", "TEST");
    await contract.deployed();
  });
  
  describe("Deployment", function () {
    it("should set the right owner", async function () {
      expect(await contract.owner()).to.equal(owner.address);
    });
    
    it("should assign total supply to owner", async function () {
      const ownerBalance = await contract.balanceOf(owner.address);
      expect(await contract.totalSupply()).to.equal(ownerBalance);
    });
  });
});
```

### Security Testing
```javascript
describe("Security", function () {
  it("should prevent unauthorized minting", async function () {
    await expect(
      contract.connect(user1).mint(user1.address, 100)
    ).to.be.revertedWith("AccessControl: account is missing role");
  });
  
  it("should prevent reentrancy attacks", async function () {
    // Deploy malicious contract that attempts reentrancy
    const MaliciousContract = await ethers.getContractFactory("MaliciousContract");
    const malicious = await MaliciousContract.deploy(contract.address);
    
    await expect(
      malicious.attack()
    ).to.be.revertedWith("ReentrancyGuard: reentrant call");
  });
  
  it("should handle zero address transfers", async function () {
    await expect(
      contract.transfer(ethers.constants.AddressZero, 100)
    ).to.be.revertedWithCustomError(contract, "InvalidAddress");
  });
});
```

### Gas Optimization Testing
```javascript
describe("Gas Optimization", function () {
  it("should use reasonable gas for minting", async function () {
    const tx = await contract.mint(user1.address, 1000);
    const receipt = await tx.wait();
    
    // Minting should use less than 100k gas
    expect(receipt.gasUsed).to.be.below(100000);
  });
  
  it("should batch operations efficiently", async function () {
    const addresses = [user1.address, user2.address];
    const amounts = [100, 200];
    
    const tx = await contract.batchMint(addresses, amounts);
    const receipt = await tx.wait();
    
    // Batch should be more efficient than individual calls
    expect(receipt.gasUsed).to.be.below(200000);
  });
});
```

## Python Backend Testing

### Pytest Configuration
```python
# conftest.py
import pytest
import asyncio
from unittest.mock import AsyncMock, Mock
from web3 import Web3

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def mock_web3():
    """Mock Web3 instance for testing"""
    web3 = Mock(spec=Web3)
    web3.eth = Mock()
    web3.eth.send_raw_transaction = AsyncMock(return_value="0xabc123")
    web3.eth.get_balance = AsyncMock(return_value=1000000000000000000)  # 1 ETH
    web3.eth.get_transaction_count = AsyncMock(return_value=1)
    return web3

@pytest.fixture
async def test_wallet():
    """Test wallet with fake private key"""
    return Wallet(
        address=WalletAddress("0x742d35Cc6634C0532925a3b8D91D3031AC7b15Bc"),
        private_key="0x" + "a" * 64,  # Fake key - safe for testing
        chain_id=1337  # Local testnet
    )
```

### Wallet Testing
```python
@pytest.mark.asyncio
async def test_wallet_creation():
    """Test wallet creation with proper validation"""
    wallet_manager = WalletManager()
    
    # Test successful creation
    wallet = await wallet_manager.create_wallet(
        chain_id=1337,
        password="test123"
    )
    
    assert wallet.address.value.startswith("0x")
    assert len(wallet.address.value) == 42
    assert wallet.chain_id == 1337
    assert len(wallet.private_key) == 66  # 0x + 64 chars

@pytest.mark.asyncio
async def test_wallet_validation():
    """Test wallet address validation"""
    with pytest.raises(ValueError, match="Invalid address format"):
        WalletAddress("invalid_address")
    
    with pytest.raises(ValueError, match="Invalid address format"):
        WalletAddress("0x123")  # Too short

@pytest.mark.asyncio
async def test_wallet_signing(test_wallet, mock_web3):
    """Test transaction signing"""
    wallet_manager = WalletManager(web3_client=mock_web3)
    
    tx_params = {
        'to': '0x742d35Cc6634C0532925a3b8D91D3031AC7b15Bc',
        'value': 1000000000000000000,  # 1 ETH
        'gas': 21000,
        'gasPrice': 20000000000,  # 20 gwei
        'nonce': 1
    }
    
    signed_tx = await wallet_manager.sign_transaction(test_wallet, tx_params)
    
    assert isinstance(signed_tx, bytes)
    assert len(signed_tx) > 0
```

### Smart Contract Testing
```python
@pytest.mark.asyncio
async def test_contract_deployment(test_wallet, mock_web3):
    """Test contract deployment"""
    contract_manager = ContractManager(web3_client=mock_web3)
    
    # Mock successful deployment
    mock_web3.eth.send_raw_transaction.return_value = "0xdeployment_hash"
    
    contract_addr, tx_hash = await contract_manager.deploy_contract(
        bytecode="0x608060405234801561001057600080fd5b50",
        constructor_args=[],
        deployer_wallet=test_wallet
    )
    
    assert isinstance(contract_addr, ContractAddress)
    assert contract_addr.chain_id == test_wallet.chain_id
    assert tx_hash == "0xdeployment_hash"

@pytest.mark.asyncio
async def test_contract_call(test_wallet, mock_web3):
    """Test contract method calls"""
    contract_manager = ContractManager(web3_client=mock_web3)
    
    contract_call = ContractCall(
        contract_address=ContractAddress(
            value="0x742d35Cc6634C0532925a3b8D91D3031AC7b15Bc",
            chain_id=1337
        ),
        method_name="mint",
        args=[test_wallet.address.value, 1000],
        gas_limit=100000
    )
    
    # Mock successful call
    mock_web3.eth.call.return_value = b'\x00' * 32  # Success response
    
    result = await contract_manager.call_contract_method(contract_call)
    assert result is not None
```

### Error Handling Testing
```python
@pytest.mark.asyncio
async def test_insufficient_balance_error():
    """Test insufficient balance handling"""
    with pytest.raises(InsufficientBalanceError) as exc_info:
        await transfer_tokens(
            from_wallet=test_wallet,
            to_address=WalletAddress("0x" + "b" * 40),
            amount=2000000000000000000  # 2 ETH (more than balance)
        )
    
    assert "Balance 1000000000000000000 < required 2000000000000000000" in str(exc_info.value)

@pytest.mark.asyncio
async def test_network_connection_error(mock_web3):
    """Test network connection error handling"""
    mock_web3.eth.send_raw_transaction.side_effect = ConnectionError("Network unavailable")
    
    transaction_processor = TransactionProcessor(web3_client=mock_web3)
    
    with pytest.raises(NetworkConnectionError):
        await transaction_processor.broadcast_transaction(b"signed_tx_data")
```

### Security Testing
```python
@pytest.mark.asyncio
async def test_private_key_never_logged(caplog):
    """Test that private keys are never logged"""
    wallet = Wallet(
        address=WalletAddress("0x742d35Cc6634C0532925a3b8D91D3031AC7b15Bc"),
        private_key="0x" + "secret" * 10,
        chain_id=1337
    )
    
    # Trigger logging
    logger.info("Wallet created", wallet=wallet)
    
    # Check logs don't contain private key
    for record in caplog.records:
        assert "secret" not in record.getMessage()
        assert wallet.private_key not in record.getMessage()

@pytest.mark.asyncio 
async def test_rate_limiting():
    """Test rate limiting for blockchain operations"""
    rate_limiter = BlockchainRateLimiter()
    
    # First 60 requests should pass
    for i in range(60):
        assert await rate_limiter.check_rate_limit("test_key") == True
    
    # 61st request should fail
    assert await rate_limiter.check_rate_limit("test_key") == False

@pytest.mark.asyncio
async def test_input_validation():
    """Test input validation for API requests"""
    # Test invalid address
    with pytest.raises(ValueError, match="Invalid Ethereum address"):
        TransferRequest(
            from_address="invalid",
            to_address="0x742d35Cc6634C0532925a3b8D91D3031AC7b15Bc",
            amount=100,
            chain_id=1
        )
    
    # Test invalid amount
    with pytest.raises(ValueError, match="Amount must be positive"):
        TransferRequest(
            from_address="0x742d35Cc6634C0532925a3b8D91D3031AC7b15Bc",
            to_address="0x742d35Cc6634C0532925a3b8D91D3031AC7b15Bc",
            amount=-100,
            chain_id=1
        )
```

### Integration Testing
```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_end_to_end_transfer():
    """Test complete transfer workflow"""
    # This test requires actual blockchain connection
    # Only run in integration test environment
    
    # Create wallets
    wallet_manager = WalletManager()
    sender = await wallet_manager.create_wallet(chain_id=1337, password="test")
    receiver = await wallet_manager.create_wallet(chain_id=1337, password="test")
    
    # Fund sender wallet (in test environment)
    await fund_wallet(sender.address, amount=1000000000000000000)  # 1 ETH
    
    # Perform transfer
    tx_hash = await transfer_tokens(
        from_wallet=sender,
        to_address=receiver.address,
        amount=500000000000000000  # 0.5 ETH
    )
    
    # Verify transaction
    assert tx_hash.startswith("0x")
    
    # Wait for confirmation
    await wait_for_transaction_confirmation(tx_hash)
    
    # Check balances
    sender_balance = await get_balance(sender.address)
    receiver_balance = await get_balance(receiver.address)
    
    assert receiver_balance >= 500000000000000000
    assert sender_balance < 1000000000000000000  # Less due to transfer + gas
```

## Performance Testing

### Load Testing
```python
@pytest.mark.performance
@pytest.mark.asyncio
async def test_concurrent_wallet_creation():
    """Test concurrent wallet creation performance"""
    import time
    
    wallet_manager = WalletManager()
    start_time = time.time()
    
    # Create 100 wallets concurrently
    tasks = [
        wallet_manager.create_wallet(chain_id=1337, password="test")
        for _ in range(100)
    ]
    
    wallets = await asyncio.gather(*tasks)
    end_time = time.time()
    
    assert len(wallets) == 100
    assert all(wallet.address.value.startswith("0x") for wallet in wallets)
    
    # Should complete in reasonable time (adjust based on requirements)
    assert end_time - start_time < 10  # 10 seconds for 100 wallets

@pytest.mark.performance
@pytest.mark.asyncio
async def test_transaction_throughput():
    """Test transaction processing throughput"""
    transaction_processor = TransactionProcessor()
    
    # Mock fast processing
    transaction_processor.broadcast_transaction = AsyncMock(
        side_effect=lambda x: f"0x{hash(x):x}"
    )
    
    start_time = time.time()
    
    # Process 1000 transactions
    tasks = [
        transaction_processor.broadcast_transaction(f"tx_{i}".encode())
        for i in range(1000)
    ]
    
    results = await asyncio.gather(*tasks)
    end_time = time.time()
    
    assert len(results) == 1000
    throughput = 1000 / (end_time - start_time)
    
    # Should handle at least 100 tx/sec
    assert throughput > 100
```

## Test Organization

### Directory Structure
```
tests/
├── unit/                    # Unit tests
│   ├── wallet/             # Wallet unit tests
│   ├── contracts/          # Contract unit tests
│   └── transactions/       # Transaction unit tests
├── integration/            # Integration tests
│   ├── blockchain/         # Blockchain integration
│   └── api/                # API integration
├── performance/            # Performance tests
├── security/               # Security tests
└── fixtures/               # Test fixtures and data
```

### Test Markers
```python
# pytest.ini or pyproject.toml
[tool.pytest.ini_options]
markers = [
    "unit: Unit tests",
    "integration: Integration tests requiring external services",
    "performance: Performance and load tests",
    "security: Security vulnerability tests",
    "slow: Tests that take more than 30 seconds"
]
```

## Coverage Requirements

### Minimum Coverage
- Unit tests: 95% line coverage
- Integration tests: 80% feature coverage
- Security tests: 100% critical path coverage

### Critical Areas (Must be 100% tested)
- Private key handling
- Transaction signing
- Balance calculations
- Access control
- Input validation
- Error handling

## Test Data Management

### Test Fixtures
```python
# fixtures.py
@pytest.fixture
def sample_addresses():
    """Standard test addresses"""
    return [
        "0x742d35Cc6634C0532925a3b8D91D3031AC7b15Bc",
        "0x8ba1f109551bD432803012645Hac136c4e74bcC5",
        "0xdD2FD4581271e230360230F9337D5c0430Bf44C0"
    ]

@pytest.fixture
def sample_private_keys():
    """Fake private keys for testing (NEVER use in production!)"""
    return [
        "0x" + "a" * 64,
        "0x" + "b" * 64,
        "0x" + "c" * 64
    ]
```

## Testing Checklist

### Before Each Release
- [ ] All unit tests pass
- [ ] Integration tests pass on testnet
- [ ] Security tests detect no vulnerabilities
- [ ] Performance tests meet benchmarks
- [ ] Gas optimization tests pass
- [ ] Private key security verified
- [ ] Rate limiting tested
- [ ] Error handling verified
- [ ] Multi-chain compatibility tested 