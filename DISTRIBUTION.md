# Chrome Extension Distribution Guide

## Method 1: ZIP Distribution (Easiest)

1. Zip the `chrome-extension` folder
2. Share the ZIP file with users
3. Users extract and load via `chrome://extensions/` → "Load unpacked"

## Method 2: GitHub Distribution

1. Push code to GitHub
2. Users clone/download repository
3. Install from `chrome-extension` folder

## Method 3: Self-Hosted Installation

### Create Installation Package:

1. Open Chrome: `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Pack extension"
4. Select `chrome-extension` folder
5. Click "Pack Extension"
6. Chrome creates `.crx` file

### Host the Extension:

Upload the `.crx` file to:
- Your website
- Google Drive (public link)
- Dropbox
- GitHub Releases

### User Installation:

1. Download the `.crx` file
2. Drag and drop into `chrome://extensions/`
3. Click "Add extension"

## Method 4: Microsoft Edge Add-ons (FREE)

Microsoft Edge Add-ons store is FREE (no $5 fee like Chrome Web Store):

1. Go to: https://partner.microsoft.com/dashboard
2. Register as developer (FREE)
3. Submit extension
4. Works on Edge and Chrome (same Chromium base)

## Installation Instructions for Users

**Step 1:** Download the extension
**Step 2:** Open `chrome://extensions/`
**Step 3:** Enable "Developer mode" (top right)
**Step 4:** Click "Load unpacked"
**Step 5:** Select the `chrome-extension` folder

## Notes

- Chrome Web Store requires $5 one-time fee
- Edge Add-ons store is completely FREE
- Manual installation works forever
- Extension auto-updates only work with store distribution
