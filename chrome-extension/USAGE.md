# Chrome Extension Usage Guide

## Features

1. **Auto Match Score on Job Pages** - Automatically shows match score when you visit Naukri or Indeed job pages
2. **Manual Match Check** - Use popup to check match score for any page
3. **Save Jobs** - Save interesting jobs to your database

## Setup

1. Reload the extension after installation:
   - Go to `chrome://extensions/`
   - Click the refresh icon on Jobalytics extension

2. Upload at least one resume via the web app (http://localhost:3000)

## How to Use

### On Naukri/Indeed Job Pages

1. Navigate to any job posting on:
   - https://www.naukri.com
   - https://www.indeed.com

2. Wait 2 seconds - a match score widget will appear in the top-right corner

3. The widget shows:
   - Match percentage (0-100%)
   - Match quality label
   - Save job button

### Using the Popup

1. Click the extension icon on any job page

2. Select your resume from the dropdown

3. Fill in job title and company (optional)

4. Click "Show Match Score" to see how well you match

5. Click "Save Job to Database" to save for later

## Tips

- The extension works best on actual job posting pages
- Make sure backend is running on localhost:8000
- Upload your most recent resume for accurate matches
- Higher scores (80%+) indicate excellent matches
