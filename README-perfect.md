![Dot Matrix OCR Pipeline](uploads/5d3e695b-0d9f-4d65-826e-632c3923174b/4_clustered.png)

---

# 🔍 Dot Matrix OCR Enterprise System

An advanced OCR system for reading dot matrix printed text in industrial environments. This system uses computer vision and AI-powered text recognition to extract digits from challenging dot matrix images.

## ✨ Features
- Specialized for dot matrix text recognition
- Adaptive illumination correction
- 7-step computer vision pipeline (DBSCAN clustering)
- AI-powered OCR (Vision Language Models via OpenRouter)
- Real-time visualization of each processing stage
- Modern dark-themed UI
- Batch processing ready

## 🚀 Live Demo
Upload a dot matrix image and watch the system:
1. Upload your image
2. Process through 7 stages
3. Display intermediate results
4. Show extracted digits

## 🛠️ How It Works
The pipeline includes:
1. Original Image
2. Illumination Correction
3. Thresholding
4. Cluster Detection
5. DBSCAN Filtering
6. Deskewing
7. VLM OCR

## 📋 Usage
### Web Interface
- Choose or drag & drop an image
- View real-time processing
- Copy extracted digits
- Analyze new images

### API Usage
```bash
curl -X POST "http://localhost:8000/api/process" -F "file=@your_image.png"
```
Response:
```json
{
  "success": true,
  "session_id": "uuid-string",
  "images": { ... },
  "ocr_result": "1234567890"
}
```

## 🐳 Local Development
```bash
pip install -r requirements.txt
export OPENROUTER_API_KEY="your-api-key-here"
python app.py
```

## 🔧 API Documentation
- POST `/api/process`: Process image
- GET `/`: Web interface
- GET `/styles.css`, `/script.js`, `/favicon.ico`: Static assets

## 🧪 Testing
- Test with low-contrast, rotated, uneven lighting, and broken dot matrix images

## 🚨 Error Handling
- Rate limiting, API failures, invalid images, network issues

## 📊 Performance
- Processing time: ~10-30 seconds
- Optimized for dot matrix images
- Session-based concurrency

## 🤝 Contributing
- Fork, branch, PR

## 📄 License
MIT License

## 🙏 Credits
- FastAPI, OpenCV, OpenRouter

---

*Built with ❤️ for industrial OCR applications*
