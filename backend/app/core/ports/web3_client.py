"""
Web3 Client Port Interface

Defines the interface for blockchain interactions following the Ports & Adapters pattern.
This interface abstracts away the specific Web3 implementation details.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Any
from decimal import Decimal
from dataclasses import dataclass
from enum import Enum

from app.core.domain.asset import AssetId, C2PAHash


class NetworkType(str, Enum):
    """Supported blockchain networks"""
    MAINNET = "mainnet"
    SEPOLIA = "sepolia"
    POLYGON = "polygon"
    MUMBAI = "mumbai"
    LOCALHOST = "localhost"


class TransactionStatus(str, Enum):
    """Transaction status enumeration"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    DROPPED = "dropped"


@dataclass(frozen=True)
class TransactionHash:
    """Value object for transaction hash"""
    value: str
    
    def __post_init__(self):
        if not self.value.startswith('0x') or len(self.value) != 66:
            raise ValueError("Invalid transaction hash format")
    
    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class ContractAddress:
    """Value object for smart contract address"""
    value: str
    
    def __post_init__(self):
        if not self.value.startswith('0x') or len(self.value) != 42:
            raise ValueError("Invalid contract address format")
    
    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class WalletAddress:
    """Value object for wallet address"""
    value: str
    
    def __post_init__(self):
        if not self.value.startswith('0x') or len(self.value) != 42:
            raise ValueError("Invalid wallet address format")
    
    def __str__(self) -> str:
        return self.value.lower()


@dataclass
class GasEstimate:
    """Gas estimation result"""
    gas_limit: int
    gas_price: int
    estimated_cost: Decimal  # In ETH
    
    @property
    def total_cost_wei(self) -> int:
        return self.gas_limit * self.gas_price


@dataclass
class TransactionReceipt:
    """Transaction receipt data"""
    transaction_hash: TransactionHash
    block_number: int
    gas_used: int
    status: TransactionStatus
    contract_address: Optional[ContractAddress] = None
    logs: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.logs is None:
            self.logs = []


@dataclass
class NFTMetadata:
    """NFT metadata for minting"""
    title: str
    description: str
    image_uri: str
    metadata_uri: str
    royalty_bps: int  # Basis points (100 = 1%)


@dataclass
class ListingInfo:
    """Marketplace listing information"""
    listing_id: int
    nft_contract: ContractAddress
    token_id: int
    seller: WalletAddress
    price: Decimal
    payment_token: Optional[ContractAddress]
    listing_type: str
    is_active: bool


class Web3ClientPort(ABC):
    """
    Port interface for Web3 blockchain interactions
    
    This interface defines all the blockchain operations needed by the application
    following the Hexagonal Architecture pattern.
    """
    
    # Network and Connection Management
    
    @abstractmethod
    async def connect(self, network: NetworkType) -> bool:
        """Connect to the specified blockchain network"""
        pass
    
    @abstractmethod
    async def is_connected(self) -> bool:
        """Check if connected to blockchain network"""
        pass
    
    @abstractmethod
    async def get_network_info(self) -> Dict[str, Any]:
        """Get current network information"""
        pass
    
    @abstractmethod
    async def get_latest_block_number(self) -> int:
        """Get the latest block number"""
        pass
    
    # Wallet Management
    
    @abstractmethod
    async def create_wallet(self, password: str) -> Tuple[WalletAddress, str]:
        """Create a new wallet and return address and private key"""
        pass
    
    @abstractmethod
    async def import_wallet(self, private_key: str) -> WalletAddress:
        """Import wallet from private key"""
        pass
    
    @abstractmethod
    async def get_balance(self, address: WalletAddress) -> Decimal:
        """Get ETH balance for an address"""
        pass
    
    @abstractmethod
    async def get_token_balance(
        self, 
        address: WalletAddress, 
        token_contract: ContractAddress
    ) -> Decimal:
        """Get ERC20 token balance for an address"""
        pass
    
    # Transaction Management
    
    @abstractmethod
    async def estimate_gas(
        self, 
        to: WalletAddress, 
        data: str = "0x", 
        value: int = 0
    ) -> GasEstimate:
        """Estimate gas for a transaction"""
        pass
    
    @abstractmethod
    async def send_transaction(
        self,
        from_address: WalletAddress,
        to_address: WalletAddress,
        value: Decimal,
        private_key: str,
        gas_limit: Optional[int] = None,
        gas_price: Optional[int] = None
    ) -> TransactionHash:
        """Send ETH transaction"""
        pass
    
    @abstractmethod
    async def get_transaction_receipt(
        self, 
        tx_hash: TransactionHash
    ) -> Optional[TransactionReceipt]:
        """Get transaction receipt"""
        pass
    
    @abstractmethod
    async def wait_for_transaction(
        self, 
        tx_hash: TransactionHash, 
        timeout: int = 300
    ) -> TransactionReceipt:
        """Wait for transaction confirmation"""
        pass
    
    # NFT Contract Interactions
    
    @abstractmethod
    async def deploy_nft_contract(
        self,
        deployer_private_key: str,
        name: str,
        symbol: str,
        platform_treasury: WalletAddress,
        minting_fee: Decimal
    ) -> Tuple[ContractAddress, TransactionHash]:
        """Deploy a new NFT contract"""
        pass
    
    @abstractmethod
    async def mint_nft(
        self,
        contract_address: ContractAddress,
        minter_private_key: str,
        to_address: WalletAddress,
        metadata: NFTMetadata,
        asset_id: AssetId
    ) -> Tuple[int, TransactionHash]:
        """Mint a new NFT and return token ID"""
        pass
    
    @abstractmethod
    async def verify_nft(
        self,
        contract_address: ContractAddress,
        verifier_private_key: str,
        token_id: int,
        c2pa_hash: C2PAHash
    ) -> TransactionHash:
        """Verify NFT with C2PA hash"""
        pass
    
    @abstractmethod
    async def get_nft_owner(
        self,
        contract_address: ContractAddress,
        token_id: int
    ) -> WalletAddress:
        """Get NFT owner address"""
        pass
    
    @abstractmethod
    async def get_nft_metadata(
        self,
        contract_address: ContractAddress,
        token_id: int
    ) -> Dict[str, Any]:
        """Get NFT metadata"""
        pass
    
    @abstractmethod
    async def get_royalty_info(
        self,
        contract_address: ContractAddress,
        token_id: int,
        sale_price: Decimal
    ) -> Tuple[WalletAddress, Decimal]:
        """Get royalty recipient and amount"""
        pass
    
    # Marketplace Contract Interactions
    
    @abstractmethod
    async def deploy_marketplace_contract(
        self,
        deployer_private_key: str,
        platform_treasury: WalletAddress,
        platform_fee_bps: int
    ) -> Tuple[ContractAddress, TransactionHash]:
        """Deploy marketplace contract"""
        pass
    
    @abstractmethod
    async def create_listing(
        self,
        marketplace_address: ContractAddress,
        seller_private_key: str,
        nft_contract: ContractAddress,
        token_id: int,
        price: Decimal,
        payment_token: Optional[ContractAddress] = None,
        listing_type: str = "FIXED_PRICE",
        duration: Optional[int] = None
    ) -> Tuple[int, TransactionHash]:
        """Create marketplace listing"""
        pass
    
    @abstractmethod
    async def buy_nft(
        self,
        marketplace_address: ContractAddress,
        buyer_private_key: str,
        listing_id: int,
        price: Decimal
    ) -> TransactionHash:
        """Buy NFT from marketplace"""
        pass
    
    @abstractmethod
    async def place_bid(
        self,
        marketplace_address: ContractAddress,
        bidder_private_key: str,
        listing_id: int,
        bid_amount: Decimal
    ) -> TransactionHash:
        """Place bid on auction"""
        pass
    
    @abstractmethod
    async def finalize_auction(
        self,
        marketplace_address: ContractAddress,
        finalizer_private_key: str,
        listing_id: int
    ) -> TransactionHash:
        """Finalize auction"""
        pass
    
    @abstractmethod
    async def get_listing_info(
        self,
        marketplace_address: ContractAddress,
        listing_id: int
    ) -> ListingInfo:
        """Get marketplace listing information"""
        pass
    
    @abstractmethod
    async def get_active_listings(
        self,
        marketplace_address: ContractAddress,
        offset: int = 0,
        limit: int = 20
    ) -> List[ListingInfo]:
        """Get active marketplace listings"""
        pass
    
    # Event Monitoring
    
    @abstractmethod
    async def get_nft_events(
        self,
        contract_address: ContractAddress,
        from_block: int,
        to_block: Optional[int] = None,
        event_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Get NFT contract events"""
        pass
    
    @abstractmethod
    async def get_marketplace_events(
        self,
        contract_address: ContractAddress,
        from_block: int,
        to_block: Optional[int] = None,
        event_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Get marketplace contract events"""
        pass
    
    @abstractmethod
    async def subscribe_to_events(
        self,
        contract_address: ContractAddress,
        event_name: str,
        callback: callable
    ) -> str:
        """Subscribe to contract events"""
        pass
    
    @abstractmethod
    async def unsubscribe_from_events(self, subscription_id: str) -> bool:
        """Unsubscribe from contract events"""
        pass
    
    # Utility Methods
    
    @abstractmethod
    async def is_valid_address(self, address: str) -> bool:
        """Check if address is valid Ethereum address"""
        pass
    
    @abstractmethod
    async def to_checksum_address(self, address: str) -> str:
        """Convert address to checksum format"""
        pass
    
    @abstractmethod
    async def wei_to_ether(self, wei_amount: int) -> Decimal:
        """Convert Wei to Ether"""
        pass
    
    @abstractmethod
    async def ether_to_wei(self, ether_amount: Decimal) -> int:
        """Convert Ether to Wei"""
        pass 