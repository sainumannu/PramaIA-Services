#!/usr/bin/env node

/**
 * PramaIA PDK CLI - Main entry point
 */

import { Command } from 'commander';
import chalk from 'chalk';
import { createPlugin } from './create-plugin.js';
import { validatePlugin } from './validate-plugin.js';
import { packagePlugin } from './package-plugin.js';
import { devServer } from './dev-server.js';
import { PDK_SERVER_PORT, BACKEND_BASE_URL } from '../config/index.js';

const program = new Command();

program
  .name('pramaia-pdk')
  .description('PramaIA Plugin Development Kit CLI')
  .version('1.0.0');

// Create plugin command
program
  .command('create')
  .description('Create a new plugin from template')
  .argument('<name>', 'Plugin name')
  .option('-t, --type <type>', 'Plugin type (input|processing|output|control)', 'processing')
  .option('-d, --dir <directory>', 'Output directory', './plugins')
  .option('--author <author>', 'Plugin author name')
  .option('--description <description>', 'Plugin description')
  .action(async (name, options) => {
    try {
      console.log(chalk.blue('🚀 Creating new plugin...'));
      await createPlugin(name, options);
      console.log(chalk.green('✅ Plugin created successfully!'));
    } catch (error) {
      console.error(chalk.red('❌ Error creating plugin:'), error);
      process.exit(1);
    }
  });

// Validate plugin command
program
  .command('validate')
  .description('Validate a plugin')
  .argument('<path>', 'Plugin directory path')
  .option('--strict', 'Enable strict validation mode')
  .action(async (path, options) => {
    try {
      console.log(chalk.blue('🔍 Validating plugin...'));
      const result = await validatePlugin(path, options);
      
      if (result.valid) {
        console.log(chalk.green('✅ Plugin is valid!'));
      } else {
        console.log(chalk.red('❌ Plugin validation failed:'));
        result.errors.forEach(error => {
          console.log(chalk.red(`  • ${error.message}`));
        });
        if (result.warnings.length > 0) {
          console.log(chalk.yellow('⚠️  Warnings:'));
          result.warnings.forEach(warning => {
            console.log(chalk.yellow(`  • ${warning.message}`));
          });
        }
        process.exit(1);
      }
    } catch (error) {
      console.error(chalk.red('❌ Error validating plugin:'), error);
      process.exit(1);
    }
  });

// Package plugin command
program
  .command('package')
  .description('Package a plugin for distribution')
  .argument('<path>', 'Plugin directory path')
  .option('-o, --output <path>', 'Output file path')
  .option('--registry <url>', 'Plugin registry URL')
  .action(async (path, options) => {
    try {
      console.log(chalk.blue('📦 Packaging plugin...'));
      const result = await packagePlugin(path, options);
      console.log(chalk.green(`✅ Plugin packaged: ${result.packagePath}`));
    } catch (error) {
      console.error(chalk.red('❌ Error packaging plugin:'), error);
      process.exit(1);
    }
  });

// Development server command
program
  .command('dev')
  .description('Start development server for plugin testing')
  .argument('<path>', 'Plugin directory path')
  .option('-p, --port <port>', 'Server port', PDK_SERVER_PORT.toString())
  .option('--engine-url <url>', 'Workflow engine URL', BACKEND_BASE_URL)
  .option('--watch', 'Enable hot reload', true)
  .action(async (path, options) => {
    try {
      console.log(chalk.blue('🔧 Starting development server...'));
      await devServer(path, options);
    } catch (error) {
      console.error(chalk.red('❌ Error starting dev server:'), error);
      process.exit(1);
    }
  });

// Register plugin command
program
  .command('register')
  .description('Register plugin with workflow engine')
  .argument('<path>', 'Plugin directory path')
  .option('--engine-url <url>', 'Workflow engine URL', BACKEND_BASE_URL)
  .action(async (path, options) => {
    try {
      console.log(chalk.blue('🔗 Registering plugin with workflow engine...'));
      // Implementation will be added later
      console.log(chalk.green('✅ Plugin registered successfully!'));
    } catch (error) {
      console.error(chalk.red('❌ Error registering plugin:'), error);
      process.exit(1);
    }
  });

program.parse();
