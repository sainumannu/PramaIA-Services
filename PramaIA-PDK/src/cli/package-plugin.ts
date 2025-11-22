/**
 * Plugin packaging utility
 */

import { promises as fs } from 'fs';
import path from 'path';
import { validatePlugin } from './validate-plugin.js';

interface PackageOptions {
  output?: string;
  registry?: string;
}

interface PackageResult {
  packagePath: string;
  manifest: any;
  size: number;
}

export async function packagePlugin(pluginPath: string, options: PackageOptions = {}): Promise<PackageResult> {
  // First validate the plugin
  const validation = await validatePlugin(pluginPath, { strict: true });
  if (!validation.valid) {
    throw new Error(`Plugin validation failed:\n${validation.errors.map(e => `  • ${e.message}`).join('\n')}`);
  }

  // Read plugin manifest
  const manifestPath = path.join(pluginPath, 'plugin.json');
  const manifestContent = await fs.readFile(manifestPath, 'utf-8');
  const manifest = JSON.parse(manifestContent);

  // Read package.json
  const packageJsonPath = path.join(pluginPath, 'package.json');
  const packageContent = await fs.readFile(packageJsonPath, 'utf-8');
  const packageJson = JSON.parse(packageContent);

  // Create package directory structure
  const tempDir = path.join(pluginPath, '.pramaia-temp');
  await fs.mkdir(tempDir, { recursive: true });

  try {
    // Copy necessary files
    await copyFiles(pluginPath, tempDir, manifest);

    // Generate package metadata
    const packageMetadata = generatePackageMetadata(manifest, packageJson);
    await fs.writeFile(
      path.join(tempDir, 'pramaia-package.json'),
      JSON.stringify(packageMetadata, null, 2)
    );

    // Create the package archive
    const outputPath = options.output || path.join(
      path.dirname(pluginPath),
      `${manifest.name}-${manifest.version}.pramaia-plugin`
    );

    await createPackageArchive(tempDir, outputPath);

    // Get package size
    const stats = await fs.stat(outputPath);

    return {
      packagePath: outputPath,
      manifest,
      size: stats.size
    };

  } finally {
    // Cleanup temp directory
    await fs.rm(tempDir, { recursive: true, force: true });
  }
}

async function copyFiles(sourcePath: string, destPath: string, manifest: any): Promise<void> {
  // Files to always include
  const alwaysInclude = [
    'plugin.json',
    'package.json',
    'README.md',
    'LICENSE'
  ];

  // Copy always included files
  for (const file of alwaysInclude) {
    const srcFile = path.join(sourcePath, file);
    const destFile = path.join(destPath, file);
    
    try {
      await fs.copyFile(srcFile, destFile);
    } catch (error: any) {
      if (error.code !== 'ENOENT' || file === 'plugin.json' || file === 'package.json') {
        throw error;
      }
      // Optional files can be missing
    }
  }

  // Copy dist directory (built plugin)
  const distPath = path.join(sourcePath, 'dist');
  try {
    await copyDirectory(distPath, path.join(destPath, 'dist'));
  } catch (error: any) {
    if (error.code === 'ENOENT') {
      throw new Error('dist directory not found. Please build the plugin first with: npm run build');
    }
    throw error;
  }

  // Copy additional files specified in manifest
  if (manifest.files) {
    for (const file of manifest.files) {
      const srcPath = path.join(sourcePath, file);
      const destPath_local = path.join(destPath, file);
      
      try {
        const stats = await fs.stat(srcPath);
        if (stats.isDirectory()) {
          await copyDirectory(srcPath, destPath_local);
        } else {
          await fs.mkdir(path.dirname(destPath_local), { recursive: true });
          await fs.copyFile(srcPath, destPath_local);
        }
      } catch (error: any) {
        if (error.code !== 'ENOENT') {
          throw error;
        }
        // File specified in manifest but doesn't exist
        console.warn(`Warning: File specified in manifest not found: ${file}`);
      }
    }
  }
}

async function copyDirectory(src: string, dest: string): Promise<void> {
  await fs.mkdir(dest, { recursive: true });
  const entries = await fs.readdir(src, { withFileTypes: true });

  for (const entry of entries) {
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);

    if (entry.isDirectory()) {
      await copyDirectory(srcPath, destPath);
    } else {
      await fs.copyFile(srcPath, destPath);
    }
  }
}

function generatePackageMetadata(manifest: any, packageJson: any) {
  return {
    format_version: '1.0.0',
    package_type: 'pramaia-plugin',
    created_at: new Date().toISOString(),
    
    // Plugin information
    plugin: {
      name: manifest.name,
      version: manifest.version,
      description: manifest.description,
      author: manifest.author,
      license: manifest.license,
      pdk_version: manifest.pdk_version,
      engine_compatibility: manifest.engine_compatibility
    },
    
    // Node definitions
    nodes: manifest.nodes,
    
    // Dependencies
    dependencies: packageJson.dependencies || {},
    peer_dependencies: packageJson.peerDependencies || {},
    
    // Package metadata
    npm_package: packageJson.name,
    homepage: manifest.homepage || packageJson.homepage,
    repository: manifest.repository || packageJson.repository,
    keywords: packageJson.keywords || [],
    
    // Installation info
    installation: {
      type: 'npm',
      command: `npm install ${packageJson.name}`,
      registry: packageJson.registry || 'https://registry.npmjs.org'
    }
  };
}

async function createPackageArchive(sourceDir: string, outputPath: string): Promise<void> {
  // For now, we'll create a simple tar.gz-like structure
  // In a real implementation, you might use a proper archiving library
  
  // Create output directory if it doesn't exist
  await fs.mkdir(path.dirname(outputPath), { recursive: true });
  
  // For simplicity, we'll create a JSON package for now
  // In production, this would be a proper archive format
  const files: Record<string, string> = {};
  
  await collectFiles(sourceDir, sourceDir, files);
  
  const packageData = {
    format: 'pramaia-plugin-v1',
    created: new Date().toISOString(),
    files
  };
  
  await fs.writeFile(outputPath, JSON.stringify(packageData, null, 2));
}

async function collectFiles(baseDir: string, currentDir: string, files: Record<string, string>): Promise<void> {
  const entries = await fs.readdir(currentDir, { withFileTypes: true });
  
  for (const entry of entries) {
    const fullPath = path.join(currentDir, entry.name);
    const relativePath = path.relative(baseDir, fullPath).replace(/\\/g, '/');
    
    if (entry.isDirectory()) {
      await collectFiles(baseDir, fullPath, files);
    } else {
      const content = await fs.readFile(fullPath, 'utf-8');
      files[relativePath] = content;
    }
  }
}
