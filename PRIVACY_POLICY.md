# Privacy Policy - Jobalytics

**Last Updated:** January 2025

## Overview
Jobalytics is a browser extension that helps match your resume with job postings using AI-powered semantic analysis.

## Data Collection
The extension collects:
- Job descriptions from pages you visit on Naukri.com, Indeed.com, and LinkedIn.com
- Job titles and company names from these pages
- No personal information, browsing history, or credentials are collected

## Data Usage
Collected job data is:
- Sent to your local Jobalytics backend server (localhost:8000)
- Used to calculate match scores between your resume and job descriptions
- Stored locally in your PostgreSQL database on your machine

## Data Storage
- All data is stored locally on your computer
- No data is transmitted to external servers or third parties
- No cloud storage or remote databases are used
- You have full control over your data

## Third-Party Services
- No third-party analytics or tracking services
- No data sharing with external parties
- No advertisements or tracking cookies

## Permissions Explanation
The extension requires the following permissions:

- **activeTab**: To read job descriptions from the current page you're viewing
- **storage**: To cache match scores locally in your browser for better performance
- **host_permissions** (naukri.com, indeed.com, linkedin.com): To access and extract job information from these specific job sites only

## User Control
You can:
- Uninstall the extension at any time
- Delete all stored data by removing the extension
- Control which sites the extension runs on through browser settings

## Security
- All communication happens between your browser and your local backend
- No external API calls or data transmission
- Open source code available for review

## Changes to Privacy Policy
We may update this policy. Changes will be posted with a new "Last Updated" date.

## Contact
For questions or concerns:
- GitHub Issues: https://github.com/YOUR_USERNAME/jobalytics/issues
- Email: your.email@example.com

## Compliance
This extension complies with:
- Microsoft Edge Add-ons policies
- Chrome Web Store policies
- GDPR principles (data minimization, user control)
