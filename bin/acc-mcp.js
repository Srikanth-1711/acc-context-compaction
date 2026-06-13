#!/usr/bin/env node

const os = require('os');
const path = require('path');
const fs = require('fs');
const https = require('https');
const { spawn } = require('child_process');

const REPO_OWNER = 'USER'; // Replace with actual GitHub owner
const REPO_NAME = 'acc-context-compaction';
const VERSION = 'latest'; // Or a specific tag like 'v1.0.0'

function getBinaryName() {
    const platform = os.platform();
    const arch = os.arch();
    
    if (platform === 'linux' && arch === 'x64') {
        return 'acc-mcp-linux-x64';
    } else if (platform === 'darwin' && arch === 'x64') {
        return 'acc-mcp-macos-x64';
    } else if (platform === 'darwin' && arch === 'arm64') {
        return 'acc-mcp-macos-arm64';
    } else if (platform === 'win32' && arch === 'x64') {
        return 'acc-mcp-windows-x64.exe';
    }
    
    console.error(`Unsupported platform/architecture: ${platform}/${arch}`);
    console.error("Please install via Python: pip install acc-context-compaction");
    process.exit(1);
}

const binaryName = getBinaryName();
const cacheDir = path.join(os.homedir(), '.acc-mcp', 'bin');
const binaryPath = path.join(cacheDir, binaryName);

function downloadFile(url, dest) {
    return new Promise((resolve, reject) => {
        https.get(url, (response) => {
            if (response.statusCode === 301 || response.statusCode === 302) {
                return downloadFile(response.headers.location, dest).then(resolve).catch(reject);
            }
            if (response.statusCode !== 200) {
                return reject(new Error(`Failed to download: HTTP ${response.statusCode}`));
            }
            const file = fs.createWriteStream(dest);
            response.pipe(file);
            file.on('finish', () => {
                file.close(resolve);
            });
        }).on('error', (err) => {
            fs.unlink(dest, () => reject(err));
        });
    });
}

async function ensureBinary() {
    if (fs.existsSync(binaryPath)) {
        return binaryPath;
    }

    if (!fs.existsSync(cacheDir)) {
        fs.mkdirSync(cacheDir, { recursive: true });
    }

    const releaseUrl = `https://github.com/${REPO_OWNER}/${REPO_NAME}/releases/latest/download/${binaryName}`;
    console.error(`Downloading ACC binary for ${os.platform()} ${os.arch()}...`);
    
    try {
        await downloadFile(releaseUrl, binaryPath);
        if (os.platform() !== 'win32') {
            fs.chmodSync(binaryPath, 0o755);
        }
        console.error("Download complete.");
        return binaryPath;
    } catch (error) {
        console.error(`Failed to download binary: ${error.message}`);
        console.error(`\nPlease install manually via pip:`);
        console.error(`pip install acc-context-compaction`);
        console.error(`Or download the binary manually from GitHub Releases.`);
        if (fs.existsSync(binaryPath)) {
            fs.unlinkSync(binaryPath);
        }
        process.exit(1);
    }
}

async function main() {
    const binPath = await ensureBinary();
    
    const args = process.argv.slice(2);
    const child = spawn(binPath, args, {
        stdio: 'inherit'
    });
    
    child.on('exit', (code) => {
        process.exit(code !== null ? code : 1);
    });
    
    child.on('error', (err) => {
        console.error(`Failed to spawn ACC binary: ${err}`);
        process.exit(1);
    });
}

main();
