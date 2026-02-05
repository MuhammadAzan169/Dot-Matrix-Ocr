---
title: Dot Matrix OCR Enterprise System
emoji: 🔍
colorFrom: purple
colorTo: blue
sdk: docker
pinned: false
license: mit
---

# Dot Matrix OCR Enterprise System

An advanced OCR system specifically designed for reading dot matrix printed text commonly found in industrial and manufacturing environments. This system uses sophisticated computer vision techniques combined with AI-powered text recognition to accurately extract digits from challenging dot matrix images.

## Features

- **🎯 Specialized Processing**: Optimized for dot matrix text recognition
- **💡 Illumination Correction**: Automatically normalizes brightness across images
- **🔬 Advanced Computer Vision**: Uses DBSCAN clustering and morphological operations
- **🤖 AI-Powered OCR**: Leverages Vision Language Models for accurate text extraction
- **📊 Pipeline Visualization**: View each processing stage in real-time
- **🎨 Modern UI**: Beautiful, responsive interface with dark theme

## How It Works

The system processes images through a 7-stage pipeline:

1. **Original Image Upload**: User uploads a dot matrix image
2. **Illumination Correction**: Normalizes brightness using adaptive algorithms
3. **Thresholding**: Converts to binary image
4. **Clustering**: Groups related pixel clusters using connected components
5. **DBSCAN Analysis**: Filters and refines clusters
6. **Deskewing**: Automatically straightens rotated text
7. **Final Processing**: Connects broken characters and performs VLM OCR

## Usage

1. Click "Choose Image" or drag and drop an image of dot matrix text
2. The system automatically processes the image through all stages
3. View the extracted text and intermediate processing steps
4. Copy the result to your clipboard with one click

## Technical Stack

- **Backend**: FastAPI (Python)
- **Image Processing**: OpenCV, scikit-learn, NumPy
- **AI/ML**: OpenAI Vision Models via OpenRouter
- **Frontend**: Vanilla JavaScript with modern CSS

## Configuration

This application requires an OpenRouter API key to function. Set your API key in the Space's Settings under "Repository secrets":

- **Variable Name**: `OPENROUTER_API_KEY`
- **Value**: Your OpenRouter API key (get one at [openrouter.ai](https://openrouter.ai))

## API Endpoint

The application exposes a REST API endpoint:

```
POST /api/process
- Accepts: multipart/form-data with 'file' field
- Returns: JSON with OCR results and intermediate images (base64)
```

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variable
export OPENROUTER_API_KEY="your-api-key-here"

# Run the application
python app.py
```

Visit `http://localhost:7860` in your browser.

## License

MIT License - Feel free to use this for your projects!

## Credits

Built with ❤️ for industrial OCR applications
