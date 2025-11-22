# Plugin Templates

This directory contains templates for creating new plugins quickly.

## Available Templates

### Basic Processing Plugin
- **File**: `basic-processing/`
- **Type**: Processing node
- **Description**: Simple data transformation plugin template

### AI Integration Plugin  
- **File**: `ai-integration/`
- **Type**: Processing node
- **Description**: Template for AI/LLM integration plugins

### File Input Plugin
- **File**: `file-input/`
- **Type**: Input node
- **Description**: Template for file reading plugins

### API Output Plugin
- **File**: `api-output/`
- **Type**: Output node
- **Description**: Template for API integration output plugins

### Control Flow Plugin
- **File**: `control-flow/`
- **Type**: Control node
- **Description**: Template for conditional logic plugins

## Usage

Use the PDK CLI to create plugins from these templates:

```bash
pramaia-pdk create my-plugin --type processing --template basic-processing
```

Or customize them manually by copying the template directory and modifying the files.

## Template Structure

Each template contains:
- `plugin.json` - Plugin manifest
- `package.json` - NPM package configuration
- `src/processor.ts` - Main processor implementation
- `src/index.ts` - Plugin entry point
- `tests/` - Test files
- `README.md` - Documentation
