"""
Base Domain Classes

Foundation classes for the smart contract platform following DDD principles.
Designed for maximum extensibility and following Robinhood/Binance patterns.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any, Optional, TypeVar, Generic
from uuid import UUID, uuid4
from dataclasses import dataclass, field
from enum import Enum


class DomainEvent(ABC):
    """Base class for all domain events"""
    
    def __init__(self):
        self.event_id = uuid4()
        self.occurred_at = datetime.utcnow()
        self.event_version = 1
    
    @property
    @abstractmethod
    def event_type(self) -> str:
        """Unique identifier for this event type"""
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization"""
        return {
            "event_id": str(self.event_id),
            "event_type": self.event_type,
            "occurred_at": self.occurred_at.isoformat(),
            "event_version": self.event_version,
            "payload": self._get_payload()
        }
    
    @abstractmethod
    def _get_payload(self) -> Dict[str, Any]:
        """Get event-specific payload data"""
        pass


@dataclass(frozen=True)
class EntityId:
    """Base value object for entity identifiers"""
    value: UUID = field(default_factory=uuid4)
    
    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class Address:
    """Blockchain address value object"""
    value: str
    
    def __post_init__(self):
        if not self.value.startswith('0x') or len(self.value) != 42:
            raise ValueError(f"Invalid address format: {self.value}")
    
    def __str__(self) -> str:
        return self.value.lower()


@dataclass(frozen=True)
class Amount:
    """Value object for monetary amounts"""
    value: int  # Amount in smallest unit (wei for ETH)
    decimals: int = 18
    
    def __post_init__(self):
        if self.value < 0:
            raise ValueError("Amount cannot be negative")
    
    @property
    def normalized(self) -> float:
        """Get amount as float with decimal places"""
        return self.value / (10 ** self.decimals)
    
    def __str__(self) -> str:
        return f"{self.normalized:.{self.decimals}f}"


class NetworkType(str, Enum):
    """Supported blockchain networks"""
    ETHEREUM = "ethereum"
    POLYGON = "polygon"
    ARBITRUM = "arbitrum"
    OPTIMISM = "optimism"
    BSC = "bsc"
    AVALANCHE = "avalanche"
    LOCALHOST = "localhost"


class TransactionStatus(str, Enum):
    """Transaction processing status"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    DROPPED = "dropped"
    REPLACED = "replaced"


T = TypeVar('T', bound='AggregateRoot')


class AggregateRoot(ABC, Generic[T]):
    """
    Base class for aggregate roots in DDD
    
    Provides domain event handling and entity management.
    """
    
    def __init__(self, entity_id: EntityId):
        self._id = entity_id
        self._version = 1
        self._created_at = datetime.utcnow()
        self._updated_at = self._created_at
        self._domain_events: List[DomainEvent] = []
    
    @property
    def id(self) -> EntityId:
        return self._id
    
    @property
    def version(self) -> int:
        return self._version
    
    @property
    def created_at(self) -> datetime:
        return self._created_at
    
    @property
    def updated_at(self) -> datetime:
        return self._updated_at
    
    def get_domain_events(self) -> List[DomainEvent]:
        """Get and clear domain events"""
        events = self._domain_events.copy()
        self._domain_events.clear()
        return events
    
    def mark_as_modified(self) -> None:
        """Mark aggregate as modified"""
        self._updated_at = datetime.utcnow()
        self._version += 1
    
    def _add_domain_event(self, event: DomainEvent) -> None:
        """Add domain event to be published"""
        self._domain_events.append(event)
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self._id == other._id
    
    def __hash__(self) -> int:
        return hash(self._id)


class Repository(ABC, Generic[T]):
    """
    Base repository interface for aggregate roots
    
    Follows the Repository pattern from DDD.
    """
    
    @abstractmethod
    async def save(self, aggregate: T) -> None:
        """Save aggregate to storage"""
        pass
    
    @abstractmethod
    async def find_by_id(self, entity_id: EntityId) -> Optional[T]:
        """Find aggregate by ID"""
        pass
    
    @abstractmethod
    async def find_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """Find all aggregates with pagination"""
        pass
    
    @abstractmethod
    async def delete(self, entity_id: EntityId) -> None:
        """Delete aggregate"""
        pass


class DomainService(ABC):
    """
    Base class for domain services
    
    For business logic that doesn't belong to a single aggregate.
    """
    pass


class ApplicationService(ABC):
    """
    Base class for application services
    
    Orchestrates use cases and coordinates between aggregates.
    """
    pass


class EventHandler(ABC):
    """
    Base class for domain event handlers
    
    Implements the Observer pattern for domain events.
    """
    
    @property
    @abstractmethod
    def handled_event_types(self) -> List[str]:
        """List of event types this handler processes"""
        pass
    
    @abstractmethod
    async def handle(self, event: DomainEvent) -> None:
        """Handle the domain event"""
        pass


class Specification(ABC, Generic[T]):
    """
    Base class for business rule specifications
    
    Implements the Specification pattern for complex business rules.
    """
    
    @abstractmethod
    def is_satisfied_by(self, candidate: T) -> bool:
        """Check if candidate satisfies this specification"""
        pass
    
    def and_(self, other: 'Specification[T]') -> 'AndSpecification[T]':
        """Combine specifications with AND logic"""
        return AndSpecification(self, other)
    
    def or_(self, other: 'Specification[T]') -> 'OrSpecification[T]':
        """Combine specifications with OR logic"""
        return OrSpecification(self, other)
    
    def not_(self) -> 'NotSpecification[T]':
        """Negate this specification"""
        return NotSpecification(self)


class AndSpecification(Specification[T]):
    """AND combination of specifications"""
    
    def __init__(self, left: Specification[T], right: Specification[T]):
        self.left = left
        self.right = right
    
    def is_satisfied_by(self, candidate: T) -> bool:
        return self.left.is_satisfied_by(candidate) and self.right.is_satisfied_by(candidate)


class OrSpecification(Specification[T]):
    """OR combination of specifications"""
    
    def __init__(self, left: Specification[T], right: Specification[T]):
        self.left = left
        self.right = right
    
    def is_satisfied_by(self, candidate: T) -> bool:
        return self.left.is_satisfied_by(candidate) or self.right.is_satisfied_by(candidate)


class NotSpecification(Specification[T]):
    """NOT negation of specification"""
    
    def __init__(self, spec: Specification[T]):
        self.spec = spec
    
    def is_satisfied_by(self, candidate: T) -> bool:
        return not self.spec.is_satisfied_by(candidate)


class Factory(ABC, Generic[T]):
    """
    Base factory interface for creating domain objects
    
    Encapsulates complex object creation logic.
    """
    
    @abstractmethod
    def create(self, **kwargs) -> T:
        """Create a new instance"""
        pass


class DomainException(Exception):
    """Base exception for domain-related errors"""
    
    def __init__(self, message: str, error_code: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.timestamp = datetime.utcnow()


class BusinessRuleViolationError(DomainException):
    """Raised when a business rule is violated"""
    pass


class InvalidOperationError(DomainException):
    """Raised when an invalid operation is attempted"""
    pass


class ResourceNotFoundError(DomainException):
    """Raised when a required resource is not found"""
    pass


class ConcurrencyError(DomainException):
    """Raised when a concurrency conflict occurs"""
    pass 