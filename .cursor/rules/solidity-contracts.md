# Solidity Smart Contract Rules

Apply to: `blockchain/**/*.sol`

## Contract Structure (Robinhood/Binance Standard)

### License and Pragma
```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

// Import OpenZeppelin for security
import "@openzeppelin/contracts-upgradeable/security/ReentrancyGuardUpgradeable.sol";
import "@openzeppelin/contracts-upgradeable/access/AccessControlUpgradeable.sol";
import "@openzeppelin/contracts-upgradeable/security/PausableUpgradeable.sol";
```

### Interface Naming
```solidity
// Interface naming: I + PascalCase
interface ITokenContract {
    function mint(address to, uint256 amount) external;
    function transfer(address to, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
}

// Contract naming: PascalCase
contract TokenContract is ITokenContract, ReentrancyGuardUpgradeable {
    // Implementation
}
```

## Security Patterns (Enterprise-Grade)

### 1. Access Control
```solidity
contract SecureContract is AccessControlUpgradeable {
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");
    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");
    
    modifier onlyMinter() {
        require(hasRole(MINTER_ROLE, msg.sender), "Not authorized");
        _;
    }
    
    modifier onlyAdmin() {
        require(hasRole(ADMIN_ROLE, msg.sender), "Not admin");
        _;
    }
}
```

### 2. Reentrancy Protection
```solidity
// Always use reentrancy guards on external calls
function withdraw(uint256 amount) external nonReentrant {
    require(balances[msg.sender] >= amount, "Insufficient balance");
    
    balances[msg.sender] -= amount;
    
    (bool success, ) = msg.sender.call{value: amount}("");
    require(success, "Transfer failed");
}
```

### 3. Custom Errors (Gas Optimization)
```solidity
// Use custom errors instead of require strings
error InsufficientBalance(uint256 available, uint256 requested);
error InvalidAddress();
error TransferFailed();

function transfer(address to, uint256 amount) external {
    if (to == address(0)) revert InvalidAddress();
    if (amount > balanceOf[msg.sender]) {
        revert InsufficientBalance(balanceOf[msg.sender], amount);
    }
    
    balanceOf[msg.sender] -= amount;
    balanceOf[to] += amount;
    
    emit Transfer(msg.sender, to, amount);
}
```

## Naming Conventions

### State Variables
```solidity
contract TokenContract {
    // Constants: UPPER_CASE
    uint256 public constant MAX_SUPPLY = 1000000;
    uint256 public constant DECIMALS = 18;
    
    // State variables: camelCase
    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;
    
    // Private variables: _camelCase
    uint256 private _totalSupply;
    address private _owner;
}
```

### Functions and Modifiers
```solidity
contract TokenContract {
    // Public functions: camelCase
    function mintTokens(address to, uint256 amount) external onlyMinter {
        _mint(to, amount);
    }
    
    // Internal functions: _camelCase
    function _mint(address to, uint256 amount) internal {
        balanceOf[to] += amount;
        _totalSupply += amount;
    }
    
    // Modifiers: camelCase
    modifier onlyOwner() {
        require(msg.sender == _owner, "Not owner");
        _;
    }
}
```

## Gas Optimization Patterns

### 1. Packed Structs
```solidity
// Pack structs to minimize storage slots
struct TokenInfo {
    uint128 price;        // 16 bytes
    uint64 timestamp;     // 8 bytes
    uint32 royaltyBps;    // 4 bytes
    bool isActive;        // 1 byte
    // Total: 29 bytes = 1 storage slot (32 bytes)
}
```

### 2. Efficient Loops
```solidity
// Avoid unbounded loops
function batchTransfer(
    address[] calldata recipients,
    uint256[] calldata amounts
) external {
    require(recipients.length <= 100, "Too many recipients");
    require(recipients.length == amounts.length, "Array length mismatch");
    
    uint256 length = recipients.length;
    for (uint256 i = 0; i < length; ) {
        _transfer(msg.sender, recipients[i], amounts[i]);
        unchecked { ++i; }
    }
}
```

### 3. Event Optimization
```solidity
// Use indexed parameters for filtering
event Transfer(
    address indexed from,
    address indexed to,
    uint256 amount
);

event TokenMinted(
    uint256 indexed tokenId,
    address indexed owner,
    uint256 indexed timestamp
);
```

## Upgradeability Patterns

### 1. UUPS Proxy Pattern
```solidity
contract TokenContract is 
    Initializable,
    UUPSUpgradeable,
    AccessControlUpgradeable 
{
    bytes32 public constant UPGRADER_ROLE = keccak256("UPGRADER_ROLE");
    
    /// @custom:oz-upgrades-unsafe-allow constructor
    constructor() {
        _disableInitializers();
    }
    
    function initialize(
        string memory name,
        string memory symbol
    ) public initializer {
        __UUPSUpgradeable_init();
        __AccessControl_init();
        
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(UPGRADER_ROLE, msg.sender);
    }
    
    function _authorizeUpgrade(address newImplementation) 
        internal 
        onlyRole(UPGRADER_ROLE) 
        override 
    {}
}
```

## Multi-Chain Compatibility

### 1. Chain ID Validation
```solidity
contract MultiChainContract {
    mapping(uint256 => bool) public supportedChains;
    
    modifier onlySupportedChain() {
        require(supportedChains[block.chainid], "Chain not supported");
        _;
    }
    
    function addSupportedChain(uint256 chainId) external onlyAdmin {
        supportedChains[chainId] = true;
    }
}
```

### 2. Cross-Chain Message Format
```solidity
struct CrossChainMessage {
    uint256 sourceChain;
    uint256 targetChain;
    address sender;
    address recipient;
    bytes data;
    uint256 nonce;
}
```

## Testing Patterns

### 1. Comprehensive Test Coverage
```solidity
// Test all edge cases
contract TokenContractTest {
    function testMintToZeroAddress() public {
        vm.expectRevert(InvalidAddress.selector);
        token.mint(address(0), 100);
    }
    
    function testMintExceedsSupply() public {
        vm.expectRevert(
            abi.encodeWithSelector(
                ExceedsMaxSupply.selector,
                MAX_SUPPLY,
                MAX_SUPPLY + 1
            )
        );
        token.mint(user, MAX_SUPPLY + 1);
    }
}
```

## Documentation Standards

### 1. NatSpec Documentation
```solidity
/**
 * @title TokenContract
 * @dev ERC20 token with minting and burning capabilities
 * @author Platform Team
 */
contract TokenContract {
    /**
     * @notice Mints new tokens to specified address
     * @dev Only accounts with MINTER_ROLE can call this function
     * @param to The address to mint tokens to
     * @param amount The amount of tokens to mint
     * @return success Whether the minting was successful
     */
    function mint(address to, uint256 amount) 
        external 
        onlyMinter 
        returns (bool success) 
    {
        _mint(to, amount);
        return true;
    }
}
```

## Security Checklist

### Before Deployment
- [ ] All functions have proper access control
- [ ] Reentrancy guards on external calls
- [ ] Input validation on all parameters
- [ ] Custom errors for gas optimization
- [ ] Events emitted for all state changes
- [ ] No unbounded loops
- [ ] Proper upgrade mechanism
- [ ] Multi-signature for admin functions
- [ ] Emergency pause functionality
- [ ] Comprehensive test coverage

### Never Allow
- Hardcoded addresses (except well-known contracts)
- Missing access control on sensitive functions
- Unbounded loops that can cause gas limit issues
- External calls without reentrancy protection
- Missing input validation
- Upgrades without proper authorization 