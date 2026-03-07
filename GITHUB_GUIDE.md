# Push to GitHub - Simple Guide

## Option 1: Automatic (Easiest)

```powershell
# Run the setup script with your repo URL
.\GITHUB_SETUP.ps1 -RepoUrl "https://github.com/YOUR_USERNAME/trustgraph-engine.git"
```

## Option 2: Manual Steps

### Step 1: Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `trustgraph-engine`
3. Description: "AI-powered intent classification prototype"
4. Public or Private (your choice)
5. **Don't** initialize with README (we already have one)
6. Click "Create repository"

### Step 2: Get Your Repository URL

Copy the URL shown (looks like):
```
https://github.com/YOUR_USERNAME/trustgraph-engine.git
```

### Step 3: Run Commands

```powershell
# Initialize and commit
git init
git add server_with_ui.py index.html styles.css script.js README.md LICENSE .gitignore PROTOTYPE_README.md
git commit -m "Initial commit: TrustGraph Engine working prototype"

# Connect to GitHub
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/trustgraph-engine.git

# Push
git push -u origin main
```

## What Gets Pushed

Only these essential files:
- ✅ `server_with_ui.py` - Complete backend
- ✅ `index.html` - UI structure
- ✅ `styles.css` - Styling
- ✅ `script.js` - Frontend logic
- ✅ `README.md` - Documentation
- ✅ `LICENSE` - MIT License
- ✅ `.gitignore` - Git ignore rules
- ✅ `PROTOTYPE_README.md` - Technical details

All other files are ignored (logs, temp files, etc.)

## Verify

After pushing, check:
1. Go to your GitHub repository URL
2. You should see all 8 files
3. README.md will display automatically
4. Try cloning: `git clone YOUR_REPO_URL`

## Update Later

To push changes:
```powershell
git add .
git commit -m "Your change description"
git push
```

## Troubleshooting

### "Git not found"
Install Git: https://git-scm.com/download/win

### "Permission denied"
Set up SSH keys or use HTTPS with token:
https://docs.github.com/en/authentication

### "Remote already exists"
```powershell
git remote set-url origin YOUR_NEW_URL
```

### "Nothing to commit"
All files already committed, just push:
```powershell
git push
```

---

**That's it! Your clean prototype is now on GitHub!** 🚀
