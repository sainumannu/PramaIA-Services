# Copilot Instructions for PramaIA Plugin Development Kit (PDK)

<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

## Project Overview
This is the **PramaIA Plugin Development Kit (PDK)** - a TypeScript toolkit for creating workflow node plugins for the PramaIA system.

## Key Concepts
- **Node Plugins**: Self-contained modules that define workflow processing nodes
- **Plugin Architecture**: Hot-loadable, validatable, and distributable plugin system
- **Type Safety**: Full TypeScript support with strict typing for plugin interfaces
- **Development Tools**: Built-in testing, validation, and development utilities

## Development Guidelines

### Plugin Structure
- Use the `BaseNodePlugin` class as the foundation for all node plugins
- Implement the `INodeProcessor` interface for processing logic
- Follow the plugin manifest schema for metadata
- Use the provided validation utilities before building

### Code Style
- Follow TypeScript strict mode conventions
- Use async/await for all asynchronous operations
- Implement proper error handling with typed exceptions
- Use dependency injection patterns for external services

### Testing
- Write unit tests for all plugin processors using the PDK testing utilities
- Use the mock workflow context for isolated testing
- Test plugin validation and configuration schemas
- Include integration tests with the plugin loader

### Plugin Types
When creating plugins, consider these common node categories:
- **Input Nodes**: File readers, API consumers, data sources
- **Processing Nodes**: Data transformers, content processors, AI integrations
- **Output Nodes**: File writers, API publishers, notification senders
- **Control Nodes**: Conditional logic, loops, workflow orchestration

## Available Utilities
- `PluginValidator`: Validates plugin structure and compatibility
- `MockWorkflowContext`: Testing utility for isolated plugin testing
- `PluginBuilder`: Packages plugins for distribution
- `HotReloader`: Development-time plugin reloading
- `ConfigurationSchema`: Type-safe configuration validation

## Integration Points
- Main workflow engine compatibility layer
- Plugin registry and discovery system
- Runtime plugin loading and unloading
- Configuration validation and type checking
