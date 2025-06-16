"""
Asset Domain Model

This module contains the core Asset domain entity and related value objects.
Following DDD principles with rich domain models.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from uuid import UUID, uuid4
from dataclasses import dataclass, field
from decimal import Decimal


class AssetStatus(str, Enum):
    """Asset status enumeration"""
    DRAFT = "draft"
    MINTING = "minting"
    MINTED = "minted"
    LISTED = "listed"
    SOLD = "sold"
    BURNED = "burned"


class VerificationStatus(str, Enum):
    """Verification status enumeration"""
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass(frozen=True)
class AssetId:
    """Value object for Asset ID"""
    value: UUID = field(default_factory=uuid4)
    
    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class IPFSHash:
    """Value object for IPFS hash"""
    value: str
    
    def __post_init__(self):
        if not self.value.startswith(('Qm', 'bafy')):
            raise ValueError("Invalid IPFS hash format")
    
    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class C2PAHash:
    """Value object for C2PA verification hash"""
    value: str
    
    def __post_init__(self):
        if len(self.value) != 66 or not self.value.startswith('0x'):
            raise ValueError("Invalid C2PA hash format")
    
    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class RoyaltyInfo:
    """Value object for royalty information"""
    recipient: str  # Ethereum address
    percentage: Decimal  # 0-100
    
    def __post_init__(self):
        if not (0 <= self.percentage <= 100):
            raise ValueError("Royalty percentage must be between 0 and 100")
        if not self.recipient.startswith('0x') or len(self.recipient) != 42:
            raise ValueError("Invalid Ethereum address format")


@dataclass
class AssetMetadata:
    """Asset metadata value object"""
    title: str
    description: str
    image_uri: IPFSHash
    metadata_uri: IPFSHash
    tags: List[str] = field(default_factory=list)
    attributes: dict = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.title.strip():
            raise ValueError("Title cannot be empty")
        if len(self.title) > 200:
            raise ValueError("Title cannot exceed 200 characters")
        if len(self.description) > 2000:
            raise ValueError("Description cannot exceed 2000 characters")


class Asset:
    """
    Asset domain entity - represents a digital artwork in the platform
    
    This is the core domain entity that encapsulates all business logic
    related to digital art assets including minting, verification, and trading.
    """
    
    def __init__(
        self,
        asset_id: AssetId,
        creator_address: str,
        metadata: AssetMetadata,
        royalty_info: RoyaltyInfo,
        created_at: Optional[datetime] = None
    ):
        self._asset_id = asset_id
        self._creator_address = self._validate_ethereum_address(creator_address)
        self._metadata = metadata
        self._royalty_info = royalty_info
        self._created_at = created_at or datetime.utcnow()
        
        # Mutable state
        self._status = AssetStatus.DRAFT
        self._verification_status = VerificationStatus.PENDING
        self._token_id: Optional[int] = None
        self._contract_address: Optional[str] = None
        self._c2pa_hash: Optional[C2PAHash] = None
        self._verification_attempts: int = 0
        self._updated_at = self._created_at
        
        # Domain events (for event sourcing if needed)
        self._domain_events: List[dict] = []
    
    @property
    def asset_id(self) -> AssetId:
        return self._asset_id
    
    @property
    def creator_address(self) -> str:
        return self._creator_address
    
    @property
    def metadata(self) -> AssetMetadata:
        return self._metadata
    
    @property
    def royalty_info(self) -> RoyaltyInfo:
        return self._royalty_info
    
    @property
    def status(self) -> AssetStatus:
        return self._status
    
    @property
    def verification_status(self) -> VerificationStatus:
        return self._verification_status
    
    @property
    def token_id(self) -> Optional[int]:
        return self._token_id
    
    @property
    def contract_address(self) -> Optional[str]:
        return self._contract_address
    
    @property
    def c2pa_hash(self) -> Optional[C2PAHash]:
        return self._c2pa_hash
    
    @property
    def created_at(self) -> datetime:
        return self._created_at
    
    @property
    def updated_at(self) -> datetime:
        return self._updated_at
    
    @property
    def is_minted(self) -> bool:
        return self._token_id is not None and self._contract_address is not None
    
    @property
    def is_verified(self) -> bool:
        return self._verification_status == VerificationStatus.VERIFIED
    
    @property
    def can_be_minted(self) -> bool:
        return (
            self._status == AssetStatus.DRAFT and 
            self._verification_status == VerificationStatus.VERIFIED
        )
    
    def update_metadata(self, new_metadata: AssetMetadata) -> None:
        """Update asset metadata (only allowed before minting)"""
        if self.is_minted:
            raise ValueError("Cannot update metadata after minting")
        
        self._metadata = new_metadata
        self._updated_at = datetime.utcnow()
        self._add_domain_event("asset_metadata_updated", {
            "asset_id": str(self._asset_id),
            "new_metadata": {
                "title": new_metadata.title,
                "description": new_metadata.description
            }
        })
    
    def update_royalty_info(self, new_royalty_info: RoyaltyInfo) -> None:
        """Update royalty information (only creator can do this)"""
        if new_royalty_info.recipient != self._creator_address:
            raise ValueError("Only creator can update royalty info")
        
        self._royalty_info = new_royalty_info
        self._updated_at = datetime.utcnow()
        self._add_domain_event("asset_royalty_updated", {
            "asset_id": str(self._asset_id),
            "new_percentage": float(new_royalty_info.percentage)
        })
    
    def start_verification(self) -> None:
        """Start the verification process"""
        if self._verification_status != VerificationStatus.PENDING:
            raise ValueError("Asset verification already in progress or completed")
        
        self._verification_attempts += 1
        self._updated_at = datetime.utcnow()
        self._add_domain_event("asset_verification_started", {
            "asset_id": str(self._asset_id),
            "attempt": self._verification_attempts
        })
    
    def verify(self, c2pa_hash: C2PAHash, verifier_address: str) -> None:
        """Mark asset as verified with C2PA hash"""
        if self._verification_status == VerificationStatus.VERIFIED:
            raise ValueError("Asset already verified")
        
        self._verification_status = VerificationStatus.VERIFIED
        self._c2pa_hash = c2pa_hash
        self._updated_at = datetime.utcnow()
        self._add_domain_event("asset_verified", {
            "asset_id": str(self._asset_id),
            "c2pa_hash": str(c2pa_hash),
            "verifier": verifier_address
        })
    
    def reject_verification(self, reason: str) -> None:
        """Reject asset verification"""
        self._verification_status = VerificationStatus.REJECTED
        self._updated_at = datetime.utcnow()
        self._add_domain_event("asset_verification_rejected", {
            "asset_id": str(self._asset_id),
            "reason": reason
        })
    
    def start_minting(self) -> None:
        """Start the minting process"""
        if not self.can_be_minted:
            raise ValueError("Asset cannot be minted in current state")
        
        self._status = AssetStatus.MINTING
        self._updated_at = datetime.utcnow()
        self._add_domain_event("asset_minting_started", {
            "asset_id": str(self._asset_id)
        })
    
    def complete_minting(self, token_id: int, contract_address: str) -> None:
        """Complete the minting process"""
        if self._status != AssetStatus.MINTING:
            raise ValueError("Asset is not in minting state")
        
        self._token_id = token_id
        self._contract_address = self._validate_ethereum_address(contract_address)
        self._status = AssetStatus.MINTED
        self._updated_at = datetime.utcnow()
        self._add_domain_event("asset_minted", {
            "asset_id": str(self._asset_id),
            "token_id": token_id,
            "contract_address": contract_address
        })
    
    def list_for_sale(self) -> None:
        """List asset for sale on marketplace"""
        if not self.is_minted:
            raise ValueError("Asset must be minted before listing")
        
        self._status = AssetStatus.LISTED
        self._updated_at = datetime.utcnow()
        self._add_domain_event("asset_listed", {
            "asset_id": str(self._asset_id),
            "token_id": self._token_id
        })
    
    def mark_as_sold(self) -> None:
        """Mark asset as sold"""
        if self._status != AssetStatus.LISTED:
            raise ValueError("Asset is not listed for sale")
        
        self._status = AssetStatus.SOLD
        self._updated_at = datetime.utcnow()
        self._add_domain_event("asset_sold", {
            "asset_id": str(self._asset_id),
            "token_id": self._token_id
        })
    
    def get_domain_events(self) -> List[dict]:
        """Get domain events for event sourcing"""
        events = self._domain_events.copy()
        self._domain_events.clear()
        return events
    
    def _validate_ethereum_address(self, address: str) -> str:
        """Validate Ethereum address format"""
        if not address.startswith('0x') or len(address) != 42:
            raise ValueError(f"Invalid Ethereum address: {address}")
        return address.lower()
    
    def _add_domain_event(self, event_type: str, event_data: dict) -> None:
        """Add domain event"""
        self._domain_events.append({
            "event_type": event_type,
            "event_data": event_data,
            "timestamp": datetime.utcnow().isoformat(),
            "aggregate_id": str(self._asset_id)
        })
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, Asset):
            return False
        return self._asset_id == other._asset_id
    
    def __hash__(self) -> int:
        return hash(self._asset_id)
    
    def __repr__(self) -> str:
        return f"Asset(id={self._asset_id}, status={self._status}, verified={self.is_verified})" 