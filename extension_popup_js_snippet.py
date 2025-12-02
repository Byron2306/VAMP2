
# Chrome Extension popup.js - Main extension logic
popup_js = """
const BACKEND_URL = 'http://localhost:8000';

const startBtn = document.getElementById('startBtn');
const statusBtn = document.getElementById('statusBtn');
const statusMessage = document.getElementById('statusMessage');
const connectionStatus = document.getElementById('connectionStatus');

let currentScanId = null;

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
        
        const platforms = Array.from(
            document.querySelectorAll('input[name="platform"]:checked')
        ).map(el => el.value);
        
        if (platforms.length === 0) {
            showStatus('Select at least one platform', 'error');
            startBtn.disabled = false;
            return;
        }
        
        const startMonth = parseInt(document.getElementById('startMonth').value);
        const endMonth = parseInt(document.getElementById('endMonth').value);
        const startYear = parseInt(document.getElementById('startYear').value);
        const endYear = parseInt(document.getElementById('endYear').value);
        
        for (const platform of platforms) {
            const domain = getDomainForPlatform(platform);
            const cookies = await chrome.cookies.getAll({ domain: domain });
            
            if (cookies.length === 0) {
                showStatus(`No cookies found for ${platform}`, 'error');
                continue;
            }
            
            const payload = {
                platform: platform,
                cookies: cookies.map(c => ({
                    name: c.name,
                    value: c.value,
                    domain: c.domain,
                    path: c.path,
                    secure: c.secure,
                    httpOnly: c.httpOnly,
                    expires: c.expirationDate
                })),
                start_month: startMonth,
                end_month: endMonth,
                start_year: startYear,
                end_year: endYear
            };
            
            const response = await fetch(`${BACKEND_URL}/api/scrape`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            
            if (response.ok) {
                const result = await response.json();
                showStatus(`✓ ${platform}: ${result.total_items} items`, 'success');
            } else {
                const error = await response.json();
                showStatus(`✗ ${platform}: ${error.detail}`, 'error');
            }
        }
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
        showStatus(`Status: ${data.status}`, 'success');
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
print("CHROME EXTENSION - POPUP.JS")
print("="*80)
print(popup_js)
