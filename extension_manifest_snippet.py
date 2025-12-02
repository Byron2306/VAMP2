
# Chrome Extension snippet
chrome_extension = '''"""
CHROME EXTENSION - VAMP Cookie Collector & WebSocket Client
manifest.json, popup.html, popup.js
"""

# manifest.json
manifest_json = {
    "manifest_version": 3,
    "name": "VAMP Evidence Collector",
    "version": "1.0.0",
    "description": "Collect session cookies and send to VAMP backend",
    "permissions": ["cookies", "activeTab", "scripting"],
    "host_permissions": [
        "*://*.outlook.com/*",
        "*://*.onedrive.live.com/*",
        "*://*.drive.google.com/*",
        "*://*.nextcloud.nwu.ac.za/*",
        "*://*.efundi.nwu.ac.za/*"
    ],
    "action": {
        "default_popup": "popup.html",
        "default_title": "VAMP Evidence Collector"
    },
    "background": {
        "service_worker": "background.js"
    }
}

# popup.html
popup_html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {
            width: 400px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            padding: 16px;
            background: #f5f5f5;
        }
        .header {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 20px;
        }
        .header h1 {
            margin: 0;
            font-size: 18px;
            color: #333;
        }
        .section {
            background: white;
            padding: 16px;
            border-radius: 8px;
            margin-bottom: 12px;
            border: 1px solid #e0e0e0;
        }
        .section h2 {
            margin: 0 0 12px 0;
            font-size: 14px;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .month-selector {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
            margin-bottom: 12px;
        }
        .month-selector label {
            display: block;
            font-size: 12px;
            margin-bottom: 4px;
            color: #555;
        }
        .month-selector input {
            width: 100%;
            padding: 6px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 12px;
        }
        .platform-selector {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
            margin-bottom: 12px;
        }
        .platform-selector label {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 12px;
            cursor: pointer;
            padding: 6px;
            border-radius: 4px;
            background: #f9f9f9;
        }
        .platform-selector input[type="checkbox"] {
            margin: 0;
            cursor: pointer;
        }
        .button-group {
            display: flex;
            gap: 8px;
            margin-bottom: 12px;
        }
        button {
            flex: 1;
            padding: 8px;
            border: none;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn-primary {
            background: #0078d4;
            color: white;
        }
        .btn-primary:hover {
            background: #106ebe;
        }
        .btn-secondary {
            background: #e5e5e5;
            color: #333;
        }
        .btn-secondary:hover {
            background: #d5d5d5;
        }
        .status {
            font-size: 12px;
            padding: 8px;
            border-radius: 4px;
            margin-bottom: 8px;
        }
        .status.success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .status.error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .status.loading {
            background: #d1ecf1;
            color: #0c5460;
            border: 1px solid #bee5eb;
        }
        #connectionStatus {
            font-size: 11px;
            color: #666;
            text-align: center;
            margin-top: 8px;
        }
        #connectionStatus.connected {
            color: #28a745;
            font-weight: 500;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🧛 VAMP</h1>
    </div>
    
    <div class="section">
        <h2>Date Range</h2>
        <div class="month-selector">
            <div>
                <label for="startMonth">Start Month</label>
                <input type="number" id="startMonth" min="1" max="12" value="1">
            </div>
            <div>
                <label for="startYear">Year</label>
                <input type="number" id="startYear" value="2025">
            </div>
            <div>
                <label for="endMonth">End Month</label>
                <input type="number" id="endMonth" min="1" max="12" value="12">
            </div>
            <div>
                <label for="endYear">Year</label>
                <input type="number" id="endYear" value="2025">
            </div>
        </div>
    </div>
    
    <div class="section">
        <h2>Platforms</h2>
        <div class="platform-selector">
            <label>
                <input type="checkbox" name="platform" value="outlook" checked>
                Outlook
            </label>
            <label>
                <input type="checkbox" name="platform" value="onedrive" checked>
                OneDrive
            </label>
            <label>
                <input type="checkbox" name="platform" value="google_drive" checked>
                Google Drive
            </label>
            <label>
                <input type="checkbox" name="platform" value="nextcloud" checked>
                Nextcloud
            </label>
            <label>
                <input type="checkbox" name="platform" value="efundi" checked>
                eFundi
            </label>
        </div>
    </div>
    
    <div class="section">
        <div class="button-group">
            <button class="btn-primary" id="startBtn">Start Scan</button>
            <button class="btn-secondary" id="statusBtn">Status</button>
        </div>
        <div id="statusMessage"></div>
        <div id="connectionStatus">Connecting...</div>
    </div>
    
    <script src="popup.js"></script>
</body>
</html>
"""

# popup.js - Main extension logic
popup_js = """
const BACKEND_URL = 'http://localhost:8000';

// Get DOM elements
const startBtn = document.getElementById('startBtn');
const statusBtn = document.getElementById('statusBtn');
const statusMessage = document.getElementById('statusMessage');
const connectionStatus = document.getElementById('connectionStatus');

let currentScanId = null;
let ws = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    startBtn.addEventListener('click', startScan);
    statusBtn.addEventListener('click', checkStatus);
    checkBackendConnection();
});

async function checkBackendConnection() {
    try {
        const response = await fetch(`${BACKEND_URL}/health`);
        if (response.ok) {
            connectionStatus.textContent = '✓ Backend Connected';
            connectionStatus.classList.add('connected');
        }
    } catch (e) {
        connectionStatus.textContent = '✗ Backend Offline';
    }
}

async function startScan() {
    try {
        startBtn.disabled = true;
        showStatus('Collecting cookies...', 'loading');
        
        // Get selected platforms
        const platforms = Array.from(
            document.querySelectorAll('input[name="platform"]:checked')
        ).map(el => el.value);
        
        if (platforms.length === 0) {
            showStatus('Please select at least one platform', 'error');
            startBtn.disabled = false;
            return;
        }
        
        const startMonth = parseInt(document.getElementById('startMonth').value);
        const endMonth = parseInt(document.getElementById('endMonth').value);
        const startYear = parseInt(document.getElementById('startYear').value);
        const endYear = parseInt(document.getElementById('endYear').value);
        
        // Collect cookies for each platform
        const cookiesByPlatform = {};
        
        for (const platform of platforms) {
            const domain = getDomainForPlatform(platform);
            try {
                const cookies = await chrome.cookies.getAll({
                    domain: domain
                });
                
                cookiesByPlatform[platform] = cookies.map(c => ({
                    name: c.name,
                    value: c.value,
                    domain: c.domain,
                    path: c.path,
                    secure: c.secure,
                    httpOnly: c.httpOnly,
                    expires: c.expirationDate
                }));
                
                console.log(`Collected ${cookies.length} cookies for ${platform}`);
            } catch (e) {
                console.warn(`Failed to collect cookies for ${platform}:`, e);
            }
        }
        
        // Start scraping for each platform
        for (const [platform, cookies] of Object.entries(cookiesByPlatform)) {
            if (cookies.length === 0) {
                showStatus(`No cookies found for ${platform}`, 'error');
                continue;
            }
            
            const payload = {
                platform: platform,
                cookies: cookies,
                start_month: startMonth,
                end_month: endMonth,
                start_year: startYear,
                end_year: endYear
            };
            
            console.log(`Sending scrape request for ${platform}...`);
            
            try {
                const response = await fetch(`${BACKEND_URL}/api/scrape`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                });
                
                if (response.ok) {
                    const result = await response.json();
                    showStatus(
                        `✓ ${platform}: ${result.total_items} items collected`,
                        'success'
                    );
                } else {
                    const error = await response.json();
                    showStatus(
                        `✗ ${platform}: ${error.detail || 'Error'}`,
                        'error'
                    );
                }
            } catch (e) {
                showStatus(`✗ ${platform}: ${e.message}`, 'error');
            }
        }
        
        showStatus('Scan completed!', 'success');
    } catch (e) {
        showStatus(`Error: ${e.message}`, 'error');
    } finally {
        startBtn.disabled = false;
    }
}

async function checkStatus() {
    try {
        const response = await fetch(`${BACKEND_URL}/health`);
        const data = await response.json();
        showStatus(`Backend Status: ${data.status}`, 'success');
    } catch (e) {
        showStatus(`Error: ${e.message}`, 'error');
    }
}

function getDomainForPlatform(platform) {
    const domains = {
        'outlook': '.outlook.com',
        'onedrive': '.onedrive.live.com',
        'google_drive': '.drive.google.com',
        'nextcloud': 'nextcloud.nwu.ac.za',
        'efundi': 'efundi.nwu.ac.za'
    };
    return domains[platform] || '';
}

function showStatus(message, type) {
    statusMessage.textContent = message;
    statusMessage.className = `status ${type}`;
}
"""

print("="*80)
print("CHROME EXTENSION FILES")
print("="*80)
print("\nmanifest.json:")
import json as json_module
print(json_module.dumps(manifest_json, indent=2))
print("\n\npopup.html (first 1500 chars):")
print(popup_html[:1500])
print("\n\npopup.js (first 1500 chars):")
print(popup_js[:1500])
