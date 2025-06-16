"""
Plugin Manager for Smart Contract Platform

Enterprise-grade plugin system for extending platform functionality.
Allows adding new features without modifying core code.
"""

import importlib
import inspect
from abc import ABC, abstractmethod
from typing import Dict, List, Type, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from app.core.domain.base import DomainEvent, ApplicationService


class PluginType(str, Enum):
    """Types of plugins supported by the platform"""
    TOKEN_HANDLER = "token_handler"
    PAYMENT_PROCESSOR = "payment_processor"
    VERIFICATION_SERVICE = "verification_service"
    NOTIFICATION_SERVICE = "notification_service"
    ANALYTICS_SERVICE = "analytics_service"
    INTEGRATION_SERVICE = "integration_service"


@dataclass
class PluginMetadata:
    """Metadata for a plugin"""
    name: str
    version: str
    description: str
    author: str
    plugin_type: PluginType
    dependencies: List[str]
    enabled: bool = True


class Plugin(ABC):
    """Base class for all platform plugins"""
    
    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Plugin metadata"""
        pass
    
    @abstractmethod
    async def initialize(self, context: 'PluginContext') -> None:
        """Initialize the plugin with platform context"""
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Cleanup when plugin is being shut down"""
        pass
    
    async def on_event(self, event: DomainEvent) -> None:
        """Handle domain events (optional)"""
        pass


class TokenHandlerPlugin(Plugin):
    """Base class for token handling plugins"""
    
    @abstractmethod
    async def can_handle_token_type(self, token_type: str) -> bool:
        """Check if this plugin can handle the token type"""
        pass
    
    @abstractmethod
    async def mint_token(self, token_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mint a new token"""
        pass
    
    @abstractmethod
    async def transfer_token(self, from_addr: str, to_addr: str, token_id: int) -> str:
        """Transfer token between addresses"""
        pass


class PaymentProcessorPlugin(Plugin):
    """Base class for payment processing plugins"""
    
    @abstractmethod
    async def process_payment(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a payment"""
        pass
    
    @abstractmethod
    async def get_supported_currencies(self) -> List[str]:
        """Get list of supported currencies"""
        pass


class VerificationServicePlugin(Plugin):
    """Base class for verification service plugins"""
    
    @abstractmethod
    async def verify_identity(self, identity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verify user identity"""
        pass
    
    @abstractmethod
    async def verify_document(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verify document authenticity"""
        pass


@dataclass
class PluginContext:
    """Context provided to plugins during initialization"""
    config: Dict[str, Any]
    database_session: Any
    cache_client: Any
    event_bus: Any
    logger: Any


class PluginRegistry:
    """Registry for managing plugin discovery and registration"""
    
    def __init__(self):
        self._plugins: Dict[str, Type[Plugin]] = {}
        self._metadata: Dict[str, PluginMetadata] = {}
    
    def register_plugin(self, plugin_class: Type[Plugin]) -> None:
        """Register a plugin class"""
        if not issubclass(plugin_class, Plugin):
            raise ValueError(f"Plugin {plugin_class} must inherit from Plugin")
        
        # Get metadata from plugin instance
        instance = plugin_class()
        metadata = instance.metadata
        
        self._plugins[metadata.name] = plugin_class
        self._metadata[metadata.name] = metadata
    
    def get_plugin(self, name: str) -> Optional[Type[Plugin]]:
        """Get plugin class by name"""
        return self._plugins.get(name)
    
    def get_plugins_by_type(self, plugin_type: PluginType) -> List[Type[Plugin]]:
        """Get all plugins of a specific type"""
        return [
            plugin_class for name, plugin_class in self._plugins.items()
            if self._metadata[name].plugin_type == plugin_type
        ]
    
    def list_plugins(self) -> List[PluginMetadata]:
        """List all registered plugins"""
        return list(self._metadata.values())


class PluginManager(ApplicationService):
    """
    Manages plugin lifecycle and execution
    
    Features:
    - Plugin discovery and loading
    - Dependency resolution
    - Event distribution
    - Plugin isolation
    """
    
    def __init__(self):
        self._registry = PluginRegistry()
        self._active_plugins: Dict[str, Plugin] = {}
        self._event_subscriptions: Dict[str, List[Plugin]] = {}
        self._context: Optional[PluginContext] = None
    
    async def initialize(self, context: PluginContext) -> None:
        """Initialize the plugin manager"""
        self._context = context
        await self._discover_plugins()
        await self._load_plugins()
    
    async def _discover_plugins(self) -> None:
        """Discover available plugins"""
        # Auto-discover plugins in plugins directory
        import pkgutil
        import app.plugins
        
        for importer, modname, ispkg in pkgutil.iter_modules(app.plugins.__path__, 
                                                             app.plugins.__name__ + "."):
            try:
                module = importlib.import_module(modname)
                
                # Find plugin classes in module
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        issubclass(obj, Plugin) and 
                        obj != Plugin):
                        self._registry.register_plugin(obj)
                        
            except ImportError as e:
                self._context.logger.warning(f"Failed to import plugin module {modname}: {e}")
    
    async def _load_plugins(self) -> None:
        """Load and initialize plugins"""
        # Sort plugins by dependencies
        plugins_to_load = self._resolve_dependencies()
        
        for plugin_class in plugins_to_load:
            try:
                plugin_instance = plugin_class()
                metadata = plugin_instance.metadata
                
                if metadata.enabled:
                    await plugin_instance.initialize(self._context)
                    self._active_plugins[metadata.name] = plugin_instance
                    
                    # Subscribe to events if plugin handles them
                    if hasattr(plugin_instance, 'on_event'):
                        event_types = getattr(plugin_instance, 'handled_event_types', [])
                        for event_type in event_types:
                            if event_type not in self._event_subscriptions:
                                self._event_subscriptions[event_type] = []
                            self._event_subscriptions[event_type].append(plugin_instance)
                    
                    self._context.logger.info(f"Loaded plugin: {metadata.name} v{metadata.version}")
                    
            except Exception as e:
                self._context.logger.error(f"Failed to load plugin {plugin_class}: {e}")
    
    def _resolve_dependencies(self) -> List[Type[Plugin]]:
        """Resolve plugin dependencies and return load order"""
        all_plugins = list(self._registry._plugins.values())
        loaded = []
        remaining = all_plugins.copy()
        
        while remaining:
            loaded_this_round = []
            
            for plugin_class in remaining:
                instance = plugin_class()
                metadata = instance.metadata
                
                # Check if all dependencies are loaded
                dependencies_met = all(
                    dep in [loaded_plugin().metadata.name for loaded_plugin in loaded]
                    for dep in metadata.dependencies
                )
                
                if dependencies_met:
                    loaded.append(plugin_class)
                    loaded_this_round.append(plugin_class)
            
            if not loaded_this_round:
                # Circular dependency or missing dependency
                remaining_names = [plugin_class().metadata.name for plugin_class in remaining]
                raise ValueError(f"Cannot resolve dependencies for plugins: {remaining_names}")
            
            for plugin_class in loaded_this_round:
                remaining.remove(plugin_class)
        
        return loaded
    
    async def execute_plugin_method(self, plugin_name: str, method_name: str, 
                                   *args, **kwargs) -> Any:
        """Execute a method on a specific plugin"""
        if plugin_name not in self._active_plugins:
            raise ValueError(f"Plugin {plugin_name} not found or not active")
        
        plugin = self._active_plugins[plugin_name]
        if not hasattr(plugin, method_name):
            raise ValueError(f"Plugin {plugin_name} does not have method {method_name}")
        
        method = getattr(plugin, method_name)
        return await method(*args, **kwargs)
    
    async def broadcast_event(self, event: DomainEvent) -> None:
        """Broadcast domain event to subscribed plugins"""
        event_type = event.event_type
        
        if event_type in self._event_subscriptions:
            for plugin in self._event_subscriptions[event_type]:
                try:
                    await plugin.on_event(event)
                except Exception as e:
                    self._context.logger.error(
                        f"Plugin {plugin.metadata.name} failed to handle event {event_type}: {e}"
                    )
    
    async def get_plugins_by_capability(self, capability: str) -> List[Plugin]:
        """Get plugins that support a specific capability"""
        capable_plugins = []
        
        for plugin in self._active_plugins.values():
            if hasattr(plugin, capability):
                capable_plugins.append(plugin)
        
        return capable_plugins
    
    def get_active_plugins(self) -> List[PluginMetadata]:
        """Get list of active plugin metadata"""
        return [plugin.metadata for plugin in self._active_plugins.values()]
    
    async def shutdown(self) -> None:
        """Shutdown all plugins"""
        for plugin in self._active_plugins.values():
            try:
                await plugin.shutdown()
            except Exception as e:
                self._context.logger.error(f"Error shutting down plugin {plugin.metadata.name}: {e}")
        
        self._active_plugins.clear()
        self._event_subscriptions.clear()


# Example plugin implementations

class ERC20TokenHandler(TokenHandlerPlugin):
    """Plugin for handling ERC20 tokens"""
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="erc20_handler",
            version="1.0.0",
            description="Handles ERC20 token operations",
            author="Platform Team",
            plugin_type=PluginType.TOKEN_HANDLER,
            dependencies=[]
        )
    
    async def initialize(self, context: PluginContext) -> None:
        self.context = context
        self.logger = context.logger
    
    async def shutdown(self) -> None:
        pass
    
    async def can_handle_token_type(self, token_type: str) -> bool:
        return token_type.lower() == "erc20"
    
    async def mint_token(self, token_data: Dict[str, Any]) -> Dict[str, Any]:
        # Implementation for ERC20 minting
        self.logger.info(f"Minting ERC20 token: {token_data}")
        return {"status": "success", "token_id": "erc20_123"}
    
    async def transfer_token(self, from_addr: str, to_addr: str, token_id: int) -> str:
        # Implementation for ERC20 transfer
        self.logger.info(f"Transferring ERC20 token {token_id} from {from_addr} to {to_addr}")
        return "0x123abc..."


class StripePaymentProcessor(PaymentProcessorPlugin):
    """Plugin for Stripe payment processing"""
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="stripe_payments",
            version="1.0.0",
            description="Stripe payment processing integration",
            author="Platform Team",
            plugin_type=PluginType.PAYMENT_PROCESSOR,
            dependencies=[]
        )
    
    async def initialize(self, context: PluginContext) -> None:
        self.context = context
        self.stripe_key = context.config.get("stripe_api_key")
    
    async def shutdown(self) -> None:
        pass
    
    async def process_payment(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        # Implementation for Stripe payment processing
        return {"status": "success", "transaction_id": "stripe_123"}
    
    async def get_supported_currencies(self) -> List[str]:
        return ["USD", "EUR", "GBP", "JPY"]


# Global plugin manager instance
plugin_manager = PluginManager() 