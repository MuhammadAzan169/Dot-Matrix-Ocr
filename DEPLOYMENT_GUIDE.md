# 🚀 Hugging Face Spaces Deployment Guide

## Complete Step-by-Step Guide for Deploying Dot Matrix OCR System

---

## 📋 Prerequisites

Before you begin, make sure you have:

1. **Hugging Face Account**: Sign up at [huggingface.co](https://huggingface.co)
2. **OpenRouter API Key**: Get one from [openrouter.ai](https://openrouter.ai)
3. **Git Installed**: Download from [git-scm.com](https://git-scm.com)
4. **Git LFS Installed**: Download from [git-lfs.github.com](https://git-lfs.github.com)

---

## 🎯 Deployment Steps

### Step 1: Create a New Hugging Face Space

1. Go to [huggingface.co/spaces](https://huggingface.co/spaces)
2. Click **"Create new Space"**
3. Configure your Space:
   - **Space name**: `dot-matrix-ocr` (or your preferred name)
   - **License**: MIT
   - **Select SDK**: **Docker**
   - **Space hardware**: CPU basic (free) - upgradable later if needed
   - **Visibility**: Public or Private (your choice)
4. Click **"Create Space"**

### Step 2: Clone Your New Space Repository

Open your terminal/PowerShell and run:

```bash
# Clone the empty space repository
git clone https://huggingface.co/spaces/YOUR_USERNAME/dot-matrix-ocr
cd dot-matrix-ocr
```

Replace `YOUR_USERNAME` with your Hugging Face username.

### Step 3: Copy Application Files

Copy all files from your current app directory to the cloned repository:

```powershell
# From PowerShell (Windows)
Copy-Item "D:\Metal OCR\app\*" -Destination ".\dot-matrix-ocr\" -Recurse -Force -Exclude @("__pycache__", "*.pyc", ".env", "uploads\*")
```

Or manually copy these files:
- `app.py`
- `index.html`
- `requirements.txt`
- `Dockerfile`
- `README.md`
- `.gitignore`
- `static/` folder (with all contents)
- `uploads/` folder (only `.gitkeep` file, not the uploaded images)

### Step 4: Configure Environment Variables

⚠️ **IMPORTANT**: DO NOT commit your actual API key to the repository!

1. Go to your Space on Hugging Face
2. Click on **"Settings"** tab
3. Scroll to **"Repository secrets"**
4. Click **"New secret"**
5. Add secret:
   - **Name**: `OPENROUTER_API_KEY`
   - **Value**: Your actual OpenRouter API key (e.g., `sk-or-v1-...`)
6. Click **"Add"**

### Step 5: Initialize Git and Push

```bash
cd dot-matrix-ocr

# Initialize Git LFS (for large files)
git lfs install

# Add all files
git add .

# Commit changes
git commit -m "Initial deployment of Dot Matrix OCR System"

# Push to Hugging Face
git push
```

### Step 6: Wait for Build

1. Go to your Space page on Hugging Face
2. Watch the **"Building"** status at the top
3. The Docker image will build (takes 2-5 minutes)
4. Status will change to **"Running"** when ready

### Step 7: Test Your Deployment

1. Once running, your Space will be available at:
   ```
   https://huggingface.co/spaces/YOUR_USERNAME/dot-matrix-ocr
   ```

2. Test the application:
   - Upload a dot matrix image
   - Verify the processing pipeline works
   - Check that OCR results are displayed

---

## 🔧 Troubleshooting

### Build Fails

**Issue**: Docker build fails during deployment

**Solution**:
- Check the **"Logs"** tab in your Space
- Ensure all dependencies in `requirements.txt` are correct
- Verify `Dockerfile` syntax is correct

### API Key Error

**Issue**: "OPENROUTER_API_KEY environment variable not set"

**Solution**:
1. Go to Space Settings → Repository secrets
2. Ensure `OPENROUTER_API_KEY` is added correctly
3. Restart the Space (Settings → Factory reboot)

### App Not Loading

**Issue**: Space shows "Building" indefinitely

**Solution**:
- Check if Docker SDK was selected (not Gradio or Streamlit)
- Ensure port 7860 is exposed in Dockerfile
- Review logs for specific errors

### Images Not Processing

**Issue**: Upload works but processing fails

**Solution**:
- Check if OpenRouter API key is valid
- Upgrade to paid hardware (free tier has limitations)
- Check logs for `opencv` or dependency errors

---

## 🎨 Customization

### Change the Theme

Edit [`static/styles.css`](static/styles.css) to modify colors:

```css
:root {
    --primary: #667eea;  /* Change to your brand color */
    --secondary: #764ba2;
}
```

### Use Different AI Model

Edit [`app.py`](app.py) line 337:

```python
model="mistralai/mistral-small-3.1-24b-instruct:free"
# Change to any OpenRouter-supported model
```

### Adjust Processing Parameters

In [`app.py`](app.py), modify `ImageProcessor` class parameters (lines 64-73):

```python
self.threshold_value = 80  # Adjust thresholding
self.min_cluster_size = 13  # Minimum dot size
self.eps = 50  # DBSCAN epsilon
```

---

## 📊 Monitoring & Updates

### View Logs

```bash
# In your Space, go to:
# Settings → View logs
```

### Update Deployment

```bash
# Make changes locally
git add .
git commit -m "Update description"
git push

# Space automatically rebuilds
```

### Scale Up (if needed)

1. Go to Space Settings
2. Change hardware to:
   - **CPU Upgrade**: Better performance
   - **GPU**: For heavy processing loads
3. Note: Upgraded hardware requires payment

---

## 🔒 Security Best Practices

1. ✅ **NEVER** commit API keys directly in code
2. ✅ Always use environment variables/secrets
3. ✅ Keep `.env` in `.gitignore`
4. ✅ Rotate API keys periodically
5. ✅ Set Space to Private if handling sensitive data

---

## 📚 Additional Resources

- **Hugging Face Spaces Docs**: [huggingface.co/docs/hub/spaces](https://huggingface.co/docs/hub/spaces)
- **Docker Spaces Guide**: [huggingface.co/docs/hub/spaces-sdks-docker](https://huggingface.co/docs/hub/spaces-sdks-docker)
- **OpenRouter API Docs**: [openrouter.ai/docs](https://openrouter.ai/docs)

---

## 🆘 Getting Help

If you encounter issues:

1. Check the **Logs** tab in your Space
2. Review this deployment guide again
3. Visit [Hugging Face Forums](https://discuss.huggingface.co)
4. Check Space settings for proper configuration

---

## ✅ Deployment Checklist

Before going live, verify:

- [ ] All files copied to repository
- [ ] `OPENROUTER_API_KEY` added to Space secrets
- [ ] `.gitignore` excludes sensitive files
- [ ] Dockerfile builds successfully
- [ ] Space status shows "Running"
- [ ] Can access Space URL
- [ ] Image upload works
- [ ] OCR processing completes successfully
- [ ] Results display correctly

---

## 🎉 Success!

Your Dot Matrix OCR system is now deployed and publicly accessible!

Share your Space: `https://huggingface.co/spaces/YOUR_USERNAME/dot-matrix-ocr`

---

**Need help?** Feel free to reach out on the Hugging Face forums or check the documentation.

**Happy deploying! 🚀**
