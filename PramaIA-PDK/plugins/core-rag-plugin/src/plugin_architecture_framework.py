"""
Plugin Architecture Framework

Framework estendibile per registrare dinamicamente nuovi connettori, provider e strategy
per tutti i processori generici senza modificare il codice core. Supporta hot-loading,
dependency injection e plugin discovery automatico.
"""

import logging
import os
import json
import importlib
import inspect
import asyncio
from typing import Dict, Any, List, Optional, Type, Callable, Union
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from pathlib import Path
import pkgutil
import sys
from datetime import datetime

logger = logging.getLogger(__name__)


# ============================================================================
# Plugin Registry Data Models
# ============================================================================

@dataclass
class PluginMetadata:
    """Metadata for a plugin."""
    id: str
    name: str
    version: str
    description: str
    author: str
    category: str  # text, document, vector, llm, system
    plugin_type: str  # provider, strategy, connector, formatter
    interface_type: str  # Class name it implements
    dependencies: List[str] = None
    config_schema: Dict[str, Any] = None
    entry_point: str = ""
    enabled: bool = True
    priority: int = 100
    created_at: str = ""
    updated_at: str = ""


@dataclass
class PluginInstance:
    """Instance of a loaded plugin."""
    metadata: PluginMetadata
    instance: Any
    module: Any
    loaded_at: datetime
    last_used: datetime
    usage_count: int = 0
    error_count: int = 0


@dataclass
class RegistrationRequest:
    """Request to register a new plugin."""
    plugin_path: str
    metadata: PluginMetadata
    auto_enable: bool = True
    validate_interface: bool = True


# ============================================================================
# Plugin Interface Definitions
# ============================================================================

class PluginInterface(ABC):
    """Base interface that all plugins must implement."""
    
    @abstractmethod
    def get_metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        pass
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the plugin with configuration."""
        pass
    
    @abstractmethod
    async def cleanup(self) -> bool:
        """Cleanup plugin resources."""
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check and return status."""
        pass


class TextProcessorPlugin(PluginInterface):
    """Interface for text processing plugins."""
    
    @abstractmethod
    async def process_text(self, text: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Process text according to plugin functionality."""
        pass


class DocumentExtractorPlugin(PluginInterface):
    """Interface for document extraction plugins."""
    
    @abstractmethod
    async def extract_content(self, file_path: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Extract content from document."""
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """Return list of supported file formats."""
        pass


class VectorStorePlugin(PluginInterface):
    """Interface for vector store plugins."""
    
    @abstractmethod
    async def store_vectors(self, vectors: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, Any]:
        """Store vectors in the database."""
        pass
    
    @abstractmethod
    async def query_vectors(self, query_vector: List[float], config: Dict[str, Any]) -> Dict[str, Any]:
        """Query vectors from the database."""
        pass


class LLMProviderPlugin(PluginInterface):
    """Interface for LLM provider plugins."""
    
    @abstractmethod
    async def generate_response(self, messages: List[Dict[str, str]], config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate response using the LLM."""
        pass
    
    @abstractmethod
    def get_supported_models(self) -> List[str]:
        """Return list of supported models."""
        pass


class SystemOperationPlugin(PluginInterface):
    """Interface for system operation plugins."""
    
    @abstractmethod
    async def execute_operation(self, operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute system operation."""
        pass
    
    @abstractmethod
    def get_supported_operations(self) -> List[str]:
        """Return list of supported operations."""
        pass


# ============================================================================
# Plugin Discovery and Loading
# ============================================================================

class PluginDiscovery:
    """Automatic plugin discovery and loading."""
    
    def __init__(self, plugin_directories: List[str] = None):
        self.plugin_directories = plugin_directories or [
            "./plugins",
            "./extensions", 
            "./custom_plugins",
            os.path.expanduser("~/.pramaai/plugins")
        ]
        self.discovered_plugins = {}
    
    async def discover_plugins(self) -> Dict[str, PluginMetadata]:
        """Discover all available plugins."""
        discovered = {}
        
        for plugin_dir in self.plugin_directories:
            if not os.path.exists(plugin_dir):
                continue
            
            try:
                plugins_in_dir = await self._scan_directory(plugin_dir)
                discovered.update(plugins_in_dir)
                logger.info(f"Discovered {len(plugins_in_dir)} plugins in {plugin_dir}")
            except Exception as e:
                logger.error(f"Error scanning plugin directory {plugin_dir}: {e}")
        
        self.discovered_plugins = discovered
        return discovered
    
    async def _scan_directory(self, directory: str) -> Dict[str, PluginMetadata]:
        """Scan a directory for plugins."""
        plugins = {}
        
        for root, dirs, files in os.walk(directory):
            # Look for plugin.json files
            for file in files:
                if file == "plugin.json":
                    plugin_file = os.path.join(root, file)
                    try:
                        metadata = await self._load_plugin_metadata(plugin_file)
                        if metadata:
                            plugins[metadata.id] = metadata
                    except Exception as e:
                        logger.warning(f"Failed to load plugin metadata from {plugin_file}: {e}")
            
            # Look for Python modules with __plugin__ attribute
            for file in files:
                if file.endswith('.py') and not file.startswith('_'):
                    module_path = os.path.join(root, file)
                    try:
                        metadata = await self._inspect_python_module(module_path)
                        if metadata:
                            plugins[metadata.id] = metadata
                    except Exception as e:
                        logger.debug(f"Module {module_path} is not a plugin: {e}")
        
        return plugins
    
    async def _load_plugin_metadata(self, plugin_file: str) -> Optional[PluginMetadata]:
        """Load plugin metadata from plugin.json file."""
        try:
            with open(plugin_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate required fields
            required_fields = ['id', 'name', 'version', 'description', 'category', 'plugin_type', 'interface_type']
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Set entry point relative to plugin.json location
            plugin_dir = os.path.dirname(plugin_file)
            if 'entry_point' in data and not os.path.isabs(data['entry_point']):
                data['entry_point'] = os.path.join(plugin_dir, data['entry_point'])
            
            metadata = PluginMetadata(
                id=data['id'],
                name=data['name'],
                version=data['version'],
                description=data['description'],
                author=data.get('author', 'Unknown'),
                category=data['category'],
                plugin_type=data['plugin_type'],
                interface_type=data['interface_type'],
                dependencies=data.get('dependencies', []),
                config_schema=data.get('config_schema', {}),
                entry_point=data.get('entry_point', ''),
                enabled=data.get('enabled', True),
                priority=data.get('priority', 100),
                created_at=data.get('created_at', datetime.now().isoformat()),
                updated_at=data.get('updated_at', datetime.now().isoformat())
            )
            
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to load plugin metadata from {plugin_file}: {e}")
            return None
    
    async def _inspect_python_module(self, module_path: str) -> Optional[PluginMetadata]:
        """Inspect a Python module for plugin attributes."""
        try:
            # Add directory to Python path temporarily
            module_dir = os.path.dirname(module_path)
            module_name = os.path.splitext(os.path.basename(module_path))[0]
            
            if module_dir not in sys.path:
                sys.path.insert(0, module_dir)
            
            try:
                module = importlib.import_module(module_name)
                
                # Check if module has __plugin__ attribute
                if hasattr(module, '__plugin__'):
                    plugin_info = module.__plugin__
                    
                    if isinstance(plugin_info, dict):
                        metadata = PluginMetadata(
                            id=plugin_info.get('id', module_name),
                            name=plugin_info.get('name', module_name),
                            version=plugin_info.get('version', '1.0.0'),
                            description=plugin_info.get('description', ''),
                            author=plugin_info.get('author', 'Unknown'),
                            category=plugin_info.get('category', 'other'),
                            plugin_type=plugin_info.get('plugin_type', 'provider'),
                            interface_type=plugin_info.get('interface_type', 'PluginInterface'),
                            dependencies=plugin_info.get('dependencies', []),
                            config_schema=plugin_info.get('config_schema', {}),
                            entry_point=module_path,
                            enabled=plugin_info.get('enabled', True),
                            priority=plugin_info.get('priority', 100),
                            created_at=datetime.now().isoformat(),
                            updated_at=datetime.now().isoformat()
                        )
                        
                        return metadata
                
            finally:
                if module_dir in sys.path:
                    sys.path.remove(module_dir)
            
        except Exception as e:
            logger.debug(f"Module {module_path} inspection failed: {e}")
        
        return None


# ============================================================================
# Plugin Registry and Management
# ============================================================================

class PluginRegistry:
    """Central registry for managing plugins."""
    
    def __init__(self, registry_file: str = "./plugin_registry.json"):
        self.registry_file = registry_file
        self.plugins: Dict[str, PluginInstance] = {}
        self.interfaces: Dict[str, List[str]] = {}  # interface_type -> [plugin_ids]
        self.categories: Dict[str, List[str]] = {}  # category -> [plugin_ids]
        self.discovery = PluginDiscovery()
        self._load_registry()
    
    def _load_registry(self):
        """Load plugin registry from file."""
        try:
            if os.path.exists(self.registry_file):
                with open(self.registry_file, 'r') as f:
                    data = json.load(f)
                
                for plugin_id, plugin_data in data.get('plugins', {}).items():
                    metadata = PluginMetadata(**plugin_data['metadata'])
                    # Plugin instances will be loaded on-demand
                    self.plugins[plugin_id] = PluginInstance(
                        metadata=metadata,
                        instance=None,
                        module=None,
                        loaded_at=datetime.now(),
                        last_used=datetime.now(),
                        usage_count=plugin_data.get('usage_count', 0),
                        error_count=plugin_data.get('error_count', 0)
                    )
                
                self._rebuild_indices()
                
        except Exception as e:
            logger.warning(f"Failed to load plugin registry: {e}")
    
    def _save_registry(self):
        """Save plugin registry to file."""
        try:
            data = {
                'plugins': {},
                'last_updated': datetime.now().isoformat()
            }
            
            for plugin_id, plugin_instance in self.plugins.items():
                data['plugins'][plugin_id] = {
                    'metadata': asdict(plugin_instance.metadata),
                    'usage_count': plugin_instance.usage_count,
                    'error_count': plugin_instance.error_count
                }
            
            with open(self.registry_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save plugin registry: {e}")
    
    def _rebuild_indices(self):
        """Rebuild internal indices for fast lookup."""
        self.interfaces.clear()
        self.categories.clear()
        
        for plugin_id, plugin_instance in self.plugins.items():
            if not plugin_instance.metadata.enabled:
                continue
            
            # Interface index
            interface_type = plugin_instance.metadata.interface_type
            if interface_type not in self.interfaces:
                self.interfaces[interface_type] = []
            self.interfaces[interface_type].append(plugin_id)
            
            # Category index
            category = plugin_instance.metadata.category
            if category not in self.categories:
                self.categories[category] = []
            self.categories[category].append(plugin_id)
    
    async def register_plugin(self, request: RegistrationRequest) -> bool:
        """Register a new plugin."""
        try:
            metadata = request.metadata
            
            # Validate plugin doesn't already exist
            if metadata.id in self.plugins:
                logger.warning(f"Plugin {metadata.id} already registered")
                return False
            
            # Validate interface if requested
            if request.validate_interface:
                if not await self._validate_plugin_interface(request.plugin_path, metadata):
                    logger.error(f"Plugin {metadata.id} failed interface validation")
                    return False
            
            # Create plugin instance entry
            plugin_instance = PluginInstance(
                metadata=metadata,
                instance=None,
                module=None,
                loaded_at=datetime.now(),
                last_used=datetime.now(),
                usage_count=0,
                error_count=0
            )
            
            # Register plugin
            self.plugins[metadata.id] = plugin_instance
            
            # Enable if requested
            if request.auto_enable:
                metadata.enabled = True
            
            # Rebuild indices
            self._rebuild_indices()
            
            # Save registry
            self._save_registry()
            
            logger.info(f"Plugin {metadata.id} registered successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register plugin {request.metadata.id}: {e}")
            return False
    
    async def unregister_plugin(self, plugin_id: str) -> bool:
        """Unregister a plugin."""
        try:
            if plugin_id not in self.plugins:
                logger.warning(f"Plugin {plugin_id} not found")
                return False
            
            plugin_instance = self.plugins[plugin_id]
            
            # Cleanup loaded instance
            if plugin_instance.instance:
                try:
                    await plugin_instance.instance.cleanup()
                except Exception as e:
                    logger.warning(f"Failed to cleanup plugin {plugin_id}: {e}")
            
            # Remove from registry
            del self.plugins[plugin_id]
            
            # Rebuild indices
            self._rebuild_indices()
            
            # Save registry
            self._save_registry()
            
            logger.info(f"Plugin {plugin_id} unregistered successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unregister plugin {plugin_id}: {e}")
            return False
    
    async def load_plugin(self, plugin_id: str) -> Optional[Any]:
        """Load a plugin instance."""
        try:
            if plugin_id not in self.plugins:
                logger.error(f"Plugin {plugin_id} not found in registry")
                return None
            
            plugin_instance = self.plugins[plugin_id]
            metadata = plugin_instance.metadata
            
            if not metadata.enabled:
                logger.warning(f"Plugin {plugin_id} is disabled")
                return None
            
            # Return cached instance if already loaded
            if plugin_instance.instance:
                plugin_instance.last_used = datetime.now()
                plugin_instance.usage_count += 1
                return plugin_instance.instance
            
            # Load plugin module
            if not metadata.entry_point:
                logger.error(f"No entry point specified for plugin {plugin_id}")
                return None
            
            module = await self._load_plugin_module(metadata.entry_point)
            if not module:
                logger.error(f"Failed to load module for plugin {plugin_id}")
                return None
            
            # Find plugin class
            plugin_class = await self._find_plugin_class(module, metadata.interface_type)
            if not plugin_class:
                logger.error(f"Plugin class not found in module for plugin {plugin_id}")
                return None
            
            # Instantiate plugin
            instance = plugin_class()
            
            # Initialize plugin
            init_config = metadata.config_schema.get('default_config', {})
            if not await instance.initialize(init_config):
                logger.error(f"Failed to initialize plugin {plugin_id}")
                return None
            
            # Cache instance
            plugin_instance.instance = instance
            plugin_instance.module = module
            plugin_instance.loaded_at = datetime.now()
            plugin_instance.last_used = datetime.now()
            plugin_instance.usage_count += 1
            
            logger.info(f"Plugin {plugin_id} loaded successfully")
            return instance
            
        except Exception as e:
            logger.error(f"Failed to load plugin {plugin_id}: {e}")
            if plugin_id in self.plugins:
                self.plugins[plugin_id].error_count += 1
            return None
    
    async def _load_plugin_module(self, entry_point: str) -> Optional[Any]:
        """Load plugin module from entry point."""
        try:
            if entry_point.endswith('.py'):
                # Load Python file as module
                module_dir = os.path.dirname(entry_point)
                module_name = os.path.splitext(os.path.basename(entry_point))[0]
                
                if module_dir not in sys.path:
                    sys.path.insert(0, module_dir)
                
                try:
                    # Reload module if already imported
                    if module_name in sys.modules:
                        module = importlib.reload(sys.modules[module_name])
                    else:
                        module = importlib.import_module(module_name)
                    
                    return module
                finally:
                    if module_dir in sys.path:
                        sys.path.remove(module_dir)
            
            else:
                # Assume it's a module path
                module = importlib.import_module(entry_point)
                return module
                
        except Exception as e:
            logger.error(f"Failed to load module from {entry_point}: {e}")
            return None
    
    async def _find_plugin_class(self, module: Any, interface_type: str) -> Optional[Type]:
        """Find plugin class in module that implements the interface."""
        try:
            # Get the interface class
            interface_class = globals().get(interface_type)
            if not interface_class:
                logger.error(f"Interface type {interface_type} not found")
                return None
            
            # Find classes that inherit from the interface
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (obj != interface_class and 
                    issubclass(obj, interface_class) and
                    obj.__module__ == module.__name__):
                    return obj
            
            logger.error(f"No class implementing {interface_type} found in module")
            return None
            
        except Exception as e:
            logger.error(f"Failed to find plugin class: {e}")
            return None
    
    async def _validate_plugin_interface(self, plugin_path: str, metadata: PluginMetadata) -> bool:
        """Validate that plugin implements required interface."""
        try:
            module = await self._load_plugin_module(plugin_path)
            if not module:
                return False
            
            plugin_class = await self._find_plugin_class(module, metadata.interface_type)
            if not plugin_class:
                return False
            
            # Validate required methods exist
            interface_class = globals().get(metadata.interface_type)
            if interface_class:
                required_methods = [name for name, method in inspect.getmembers(interface_class, inspect.ismethod)
                                 if getattr(method, '__isabstractmethod__', False)]
                
                for method_name in required_methods:
                    if not hasattr(plugin_class, method_name):
                        logger.error(f"Plugin {metadata.id} missing required method: {method_name}")
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Plugin interface validation failed: {e}")
            return False
    
    def get_plugins_by_interface(self, interface_type: str) -> List[str]:
        """Get all plugin IDs that implement a specific interface."""
        return self.interfaces.get(interface_type, [])
    
    def get_plugins_by_category(self, category: str) -> List[str]:
        """Get all plugin IDs in a specific category."""
        return self.categories.get(category, [])
    
    def list_plugins(self, enabled_only: bool = True) -> List[PluginMetadata]:
        """List all registered plugins."""
        plugins = []
        for plugin_instance in self.plugins.values():
            if enabled_only and not plugin_instance.metadata.enabled:
                continue
            plugins.append(plugin_instance.metadata)
        
        # Sort by priority and name
        plugins.sort(key=lambda p: (p.priority, p.name))
        return plugins
    
    async def discover_and_register(self) -> int:
        """Discover and register all available plugins."""
        discovered = await self.discovery.discover_plugins()
        registered_count = 0
        
        for plugin_id, metadata in discovered.items():
            if plugin_id not in self.plugins:
                request = RegistrationRequest(
                    plugin_path=metadata.entry_point,
                    metadata=metadata,
                    auto_enable=True,
                    validate_interface=True
                )
                
                if await self.register_plugin(request):
                    registered_count += 1
        
        logger.info(f"Discovered and registered {registered_count} new plugins")
        return registered_count


# ============================================================================
# Plugin Architecture Framework Main Class
# ============================================================================

class PluginArchitectureFramework:
    """Main framework for plugin management and extension."""
    
    def __init__(self, registry_file: str = "./plugin_registry.json"):
        self.registry = PluginRegistry(registry_file)
        self.plugin_factories: Dict[str, Callable] = {}
        self.initialized = False
    
    async def initialize(self) -> bool:
        """Initialize the plugin framework."""
        try:
            logger.info("Initializing Plugin Architecture Framework")
            
            # Discover and register plugins
            await self.registry.discover_and_register()
            
            # Initialize built-in plugin factories
            await self._setup_built_in_factories()
            
            self.initialized = True
            logger.info("Plugin Architecture Framework initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Plugin Architecture Framework: {e}")
            return False
    
    async def _setup_built_in_factories(self):
        """Setup built-in plugin factories for generic processors."""
        self.plugin_factories.update({
            'text_processor': self._create_text_processor_plugin,
            'document_extractor': self._create_document_extractor_plugin,
            'vector_store': self._create_vector_store_plugin,
            'llm_provider': self._create_llm_provider_plugin,
            'system_operation': self._create_system_operation_plugin
        })
    
    async def get_plugin(self, plugin_id: str) -> Optional[Any]:
        """Get a loaded plugin instance."""
        if not self.initialized:
            await self.initialize()
        
        return await self.registry.load_plugin(plugin_id)
    
    async def get_plugins_by_interface(self, interface_type: str) -> List[Any]:
        """Get all loaded plugins that implement a specific interface."""
        if not self.initialized:
            await self.initialize()
        
        plugin_ids = self.registry.get_plugins_by_interface(interface_type)
        plugins = []
        
        for plugin_id in plugin_ids:
            plugin = await self.registry.load_plugin(plugin_id)
            if plugin:
                plugins.append(plugin)
        
        return plugins
    
    async def create_plugin_instance(self, plugin_type: str, config: Dict[str, Any]) -> Optional[Any]:
        """Create a plugin instance using registered factories."""
        if plugin_type in self.plugin_factories:
            factory = self.plugin_factories[plugin_type]
            return await factory(config)
        
        logger.error(f"No factory found for plugin type: {plugin_type}")
        return None
    
    async def _create_text_processor_plugin(self, config: Dict[str, Any]) -> Optional[Any]:
        """Factory for text processor plugins."""
        # This would create instances based on configuration
        # For now, return None as placeholder
        return None
    
    async def _create_document_extractor_plugin(self, config: Dict[str, Any]) -> Optional[Any]:
        """Factory for document extractor plugins."""
        return None
    
    async def _create_vector_store_plugin(self, config: Dict[str, Any]) -> Optional[Any]:
        """Factory for vector store plugins."""
        return None
    
    async def _create_llm_provider_plugin(self, config: Dict[str, Any]) -> Optional[Any]:
        """Factory for LLM provider plugins."""
        return None
    
    async def _create_system_operation_plugin(self, config: Dict[str, Any]) -> Optional[Any]:
        """Factory for system operation plugins."""
        return None
    
    def register_factory(self, plugin_type: str, factory: Callable):
        """Register a new plugin factory."""
        self.plugin_factories[plugin_type] = factory
        logger.info(f"Registered factory for plugin type: {plugin_type}")
    
    def list_available_plugins(self) -> List[PluginMetadata]:
        """List all available plugins."""
        return self.registry.list_plugins()
    
    def get_plugin_stats(self) -> Dict[str, Any]:
        """Get plugin usage statistics."""
        stats = {
            'total_plugins': len(self.registry.plugins),
            'enabled_plugins': len([p for p in self.registry.plugins.values() if p.metadata.enabled]),
            'loaded_plugins': len([p for p in self.registry.plugins.values() if p.instance is not None]),
            'categories': len(self.registry.categories),
            'interfaces': len(self.registry.interfaces),
            'total_usage': sum(p.usage_count for p in self.registry.plugins.values()),
            'total_errors': sum(p.error_count for p in self.registry.plugins.values())
        }
        return stats


# Global plugin framework instance
plugin_framework = PluginArchitectureFramework()


# ============================================================================
# Integration with Generic Processors
# ============================================================================

async def get_text_processor_plugin(provider_name: str) -> Optional[Any]:
    """Get a text processor plugin by name."""
    plugins = await plugin_framework.get_plugins_by_interface('TextProcessorPlugin')
    for plugin in plugins:
        if hasattr(plugin, 'provider_name') and plugin.provider_name == provider_name:
            return plugin
    return None


async def get_document_extractor_plugin(format_name: str) -> Optional[Any]:
    """Get a document extractor plugin for specific format."""
    plugins = await plugin_framework.get_plugins_by_interface('DocumentExtractorPlugin')
    for plugin in plugins:
        if hasattr(plugin, 'get_supported_formats'):
            supported = plugin.get_supported_formats()
            if format_name in supported:
                return plugin
    return None


async def get_vector_store_plugin(store_type: str) -> Optional[Any]:
    """Get a vector store plugin by type."""
    plugins = await plugin_framework.get_plugins_by_interface('VectorStorePlugin')
    for plugin in plugins:
        if hasattr(plugin, 'store_type') and plugin.store_type == store_type:
            return plugin
    return None


async def get_llm_provider_plugin(provider_name: str) -> Optional[Any]:
    """Get an LLM provider plugin by name."""
    plugins = await plugin_framework.get_plugins_by_interface('LLMProviderPlugin')
    for plugin in plugins:
        if hasattr(plugin, 'provider_name') and plugin.provider_name == provider_name:
            return plugin
    return None


async def get_system_operation_plugin(operation_type: str) -> Optional[Any]:
    """Get a system operation plugin by type."""
    plugins = await plugin_framework.get_plugins_by_interface('SystemOperationPlugin')
    for plugin in plugins:
        if hasattr(plugin, 'get_supported_operations'):
            supported = plugin.get_supported_operations()
            if operation_type in supported:
                return plugin
    return None


# Entry point function for PDK integration
async def initialize_plugin_framework():
    """Initialize the plugin framework for use in PDK."""
    return await plugin_framework.initialize()


async def process_node(context):
    """Entry point for plugin framework operations."""
    logger.info("[PluginArchitectureFramework] INGRESSO nodo: process")
    
    try:
        config = context.get('config', {})
        inputs = context.get('inputs', {})
        
        operation = config.get('operation', 'list_plugins')
        
        if operation == 'list_plugins':
            plugins = plugin_framework.list_available_plugins()
            return {
                "status": "success",
                "operation": "list_plugins",
                "output": {
                    "plugins": [asdict(p) for p in plugins],
                    "plugin_count": len(plugins)
                }
            }
        
        elif operation == 'get_stats':
            stats = plugin_framework.get_plugin_stats()
            return {
                "status": "success",
                "operation": "get_stats",
                "output": stats
            }
        
        elif operation == 'discover':
            count = await plugin_framework.registry.discover_and_register()
            return {
                "status": "success",
                "operation": "discover",
                "output": {
                    "newly_registered": count,
                    "message": f"Discovered and registered {count} new plugins"
                }
            }
        
        else:
            raise ValueError(f"Unsupported operation: {operation}")
            
    except Exception as e:
        logger.error(f"[PluginArchitectureFramework] USCITA nodo (errore): {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "operation": config.get('operation', 'unknown'),
            "output": None
        }