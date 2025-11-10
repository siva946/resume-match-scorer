# Edge Add-ons Submission Guide

## Step 1: Create Extension Package

1. Navigate to `e:\Jobalytics\chrome-extension`
2. Select ALL files inside
3. Right-click → "Send to" → "Compressed (zipped) folder"
4. Name: `jobalytics-extension-v2.0.0.zip`

## Step 2: Register at Microsoft Partner Center

URL: https://partner.microsoft.com/dashboard/microsoftedge/public/login

- Sign in with Microsoft account (FREE - no payment)
- Accept Partner Center agreement
- Complete profile

## Step 3: Submit Extension

1. Click "Create new extension"
2. Upload `jobalytics-extension-v2.0.0.zip`
3. Fill in the details below

---

## COPY-PASTE CONTENT FOR SUBMISSION

### Display Name
```
Jobalytics - AI Resume Job Matcher
```

### Short Description (132 characters max)
```
AI-powered resume matching for Naukri, Indeed, LinkedIn. See match scores instantly on job pages.
```

### Long Description
```
Find your perfect job match with AI-powered semantic analysis.

✨ FEATURES
• AI matching using SentenceTransformers
• Automatic match scores on job pages
• Supports Naukri.com, Indeed.com, LinkedIn
• One-click job saving to dashboard
• Real-time semantic analysis

🚀 HOW IT WORKS
1. Upload your resume to Jobalytics platform
2. Browse jobs on supported job sites
3. See your match score automatically
4. Save promising jobs for review

⚙️ REQUIREMENTS
Requires Jobalytics backend running locally on localhost:8000
Setup instructions: https://github.com/YOUR_USERNAME/jobalytics

🔒 PRIVACY
All data processed locally on your machine
No data sent to external servers

📖 OPEN SOURCE
View source: https://github.com/YOUR_USERNAME/jobalytics
```

### Category
```
Productivity
```

### Privacy Policy URL
```
https://gist.github.com/YOUR_USERNAME/YOUR_GIST_ID
```
(Create gist using PRIVACY_POLICY.md below)

### Notes for Certification Team
```
This extension requires a local backend server running on localhost:8000.
Users must set up the Jobalytics platform separately (instructions on GitHub).

PERMISSIONS JUSTIFICATION:
- activeTab: Read job descriptions from current page for match calculation
- storage: Cache match scores locally for better performance
- host_permissions (naukri.com, indeed.com, linkedin.com): Extract job data from these sites
```

---

## Step 4: Prepare Screenshots

Take 2-3 screenshots (1280x800px or 640x400px):
1. Extension showing match score on a job page
2. Extension popup interface
3. Match score widget in action

Save as PNG or JPG

---

## Step 5: Submit for Review

1. Upload screenshots
2. Upload icon (icon.png from chrome-extension folder)
3. Review all information
4. Click "Submit for certification"
5. Wait 1-3 business days for approval

---

## After Approval

1. Receive approval email
2. Click "Publish to store"
3. Extension goes live immediately
4. Share URL: https://microsoftedge.microsoft.com/addons/detail/[YOUR_ID]

---

## Timeline

- Registration: 5 minutes
- Form filling: 15 minutes
- Review: 1-3 business days
- Total: ~2-4 days

## Cost

**100% FREE** - No fees required
