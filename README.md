---
title: Dot Matrix OCR Enterprise System
emoji: 🔍
colorFrom: purple
colorTo: blue
sdk: docker
pinned: false
license: mit
app_port: 7860
---

# 🔍 Dot Matrix OCR Enterprise System

[![Hugging Face Spaces](https://img.shields.io/badge/Hugging%20Face-Spaces-blue)](https://huggingface.co/spaces)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green)](https://fastapi.tiangolo.com)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.8.1-red)](https://opencv.org)

An advanced OCR system specifically designed for reading dot matrix printed text commonly found in industrial and manufacturing environments. This system uses sophisticated computer vision techniques combined with AI-powered text recognition to accurately extract digits from challenging dot matrix images.

## ✨ Features

- **🎯 Specialized for Dot Matrix**: Optimized specifically for dot matrix text recognition
- **💡 Adaptive Illumination Correction**: Normalizes uneven lighting conditions
- **🔬 Advanced Computer Vision Pipeline**: 7-step processing with DBSCAN clustering
- **🤖 AI-Powered OCR**: Leverages Vision Language Models via OpenRouter
- **📊 Real-time Visualization**: View each processing stage with beautiful UI
- **🎨 Modern Dark Theme**: Clean, professional interface with smooth animations
- **🔄 Batch Processing Ready**: Easily extendable for bulk OCR operations

## 🚀 Live Demo

Simply upload a dot matrix image and watch the magic happen! The system will:
1. Upload your image
2. Process it through 7 stages
3. Display intermediate results
4. Show extracted digits

## 🛠️ How It Works

The system processes images through a sophisticated 7-stage pipeline:

| Step | Process | Description |
|------|---------|-------------|
| 1️⃣ | **Original Image** | Input image uploaded for processing |
| 2️⃣ | **Illumination Correction** | Adaptive brightness normalization |
| 3️⃣ | **Thresholding** | Binary conversion for feature extraction |
| 4️⃣ | **Cluster Detection** | Connected component analysis |
| 5️⃣ | **DBSCAN Filtering** | Density-based spatial clustering |
| 6️⃣ | **Deskewing** | Automatic rotation correction |
| 7️⃣ | **VLM OCR** | AI-powered text extraction |

## 📋 Usage

### Web Interface
1. Click "Choose Image" or drag & drop a dot matrix image
2. Watch real-time processing through 7 stages
3. View extracted digits with copy-to-clipboard functionality
4. Click "New Analysis" to process another image

### API Usage
```bash
curl -X POST "https://your-space.hf.space/api/process" \
  -F "file=@your_image.png"
```

**Response:**
```json
{
  "success": true,
  "session_id": "uuid-string",
  "images": {
    "original": "base64-string",
    "illumination": "base64-string",
    "threshold": "base64-string",
    "clustered": "base64-string",
    "dbscan": "base64-string",
    "deskewed": "base64-string",
    "final": "base64-string"
  },
  "ocr_result": "1234567890"
}
```

## 🏗️ Technical Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Backend** | FastAPI (Python) | REST API server |
| **Image Processing** | OpenCV, scikit-learn, NumPy | Computer vision pipeline |
| **AI/ML** | OpenAI VLM via OpenRouter | Text recognition |
| **Frontend** | Vanilla JS + Modern CSS | Interactive UI |
| **Deployment** | Docker + Hugging Face Spaces | Cloud hosting |
| **Storage** | Session-based file system | Temporary image storage |

## ⚙️ Configuration

### Hugging Face Spaces Setup
1. **Create a new Space** with Docker SDK
2. **Upload all files** from this repository
3. **Set Repository Secrets** in Space Settings:
   - `OPENROUTER_API_KEY`: Your OpenRouter API key
   - `OCR_MODEL`: `openrouter/free` (default, optional)

### Get OpenRouter API Key
1. Visit [OpenRouter](https://openrouter.ai)
2. Sign up and get your API key
3. Add $1 credit for 10,000+ free requests

### Environment Variables
| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `7860` | Server port (auto-set by Hugging Face) |
| `OPENROUTER_API_KEY` | Required | Your OpenRouter API key |
| `OCR_MODEL` | `openrouter/free` | Model to use for OCR |

## 🐳 Local Development

### Quick Start
```bash
# 1. Clone repository
git clone https://huggingface.co/spaces/your-username/dot-matrix-ocr
cd dot-matrix-ocr

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set environment variable
export OPENROUTER_API_KEY="your-api-key-here"

# 4. Run the application
python app.py
```

### Docker Development
```bash
# Build and run with Docker
docker build -t dot-matrix-ocr .
docker run -p 7860:7860 -e OPENROUTER_API_KEY="your-key" dot-matrix-ocr
```

## 📁 Project Structure
```
.
├── app.py                  # FastAPI application
├── index.html             # Main HTML page
├── styles.css             # CSS styles
├── script.js              # Frontend JavaScript
├── README.md              # This documentation
├── requirements.txt       # Python dependencies
├── Dockerfile            # Container configuration
├── .dockerignore         # Docker ignore rules
└── uploads/              # Temporary uploads (auto-created)
```

## 🔧 API Documentation

### POST `/api/process`
Process an image through the OCR pipeline.

**Request:**
- Content-Type: `multipart/form-data`
- Body: `file` (image file)

**Response:**
- Status: `200 OK` on success
- Content-Type: `application/json`
- Body: Processing results with base64 images

### GET `/`
Serve the web interface.

### GET `/styles.css`
Serve CSS styles.

### GET `/script.js`
Serve JavaScript code.

### GET `/favicon.ico`
Serve favicon.

## 🧪 Testing

Test with sample dot matrix images:
- Low-contrast images
- Rotated/angled text
- Uneven lighting conditions
- Broken/dotted characters

## 🚨 Error Handling

The system includes comprehensive error handling:
- **Rate limiting**: Automatic retry with exponential backoff
- **API failures**: Graceful degradation with user-friendly messages
- **Invalid images**: Early validation and helpful error messages
- **Network issues**: Connection timeout and retry logic

## 📊 Performance

- **Processing time**: ~10-30 seconds depending on image complexity
- **Image size**: Optimized for typical dot matrix images
- **Concurrency**: Session-based processing prevents conflicts
- **Memory usage**: Efficient processing with intermediate cleanup

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details.

## 🙏 Credits

- **FastAPI**: Modern web framework for building APIs
- **OpenCV**: Industry-standard computer vision library
- **OpenRouter**: Unified API for AI models
- **Hugging Face**: For providing free hosting on Spaces

## 🌟 Support

For issues, feature requests, or questions:
1. Check the [FAQ](#) section
2. Open an issue on the Hugging Face Space
3. Contact the maintainer

---

**Built with ❤️ for industrial OCR applications**

*Perfect for manufacturing, logistics, inventory management, and any application requiring dot matrix text recognition.*