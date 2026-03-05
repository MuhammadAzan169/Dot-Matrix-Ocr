// DOM Elements
const uploadSection = document.getElementById('uploadSection');
const processingSection = document.getElementById('processingSection');
const resultsSection = document.getElementById('resultsSection');
const errorSection = document.getElementById('errorSection');

const fileInput = document.getElementById('fileInput');
const uploadBtn = document.getElementById('uploadBtn');
const fileInfo = document.getElementById('fileInfo');

const processingStatus = document.getElementById('processingStatus');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');

const ocrResult = document.getElementById('ocrResult');
const copyBtn = document.getElementById('copyBtn');
const newAnalysisBtn = document.getElementById('newAnalysisBtn');
const retryBtn = document.getElementById('retryBtn');

const errorMessage = document.getElementById('errorMessage');
const toast = document.getElementById('toast');
const toastMessage = document.getElementById('toastMessage');

// Image elements
const imgOriginal = document.getElementById('imgOriginal');
const imgIllumination = document.getElementById('imgIllumination');
const imgThreshold = document.getElementById('imgThreshold');
const imgClustered = document.getElementById('imgClustered');
const imgDbscan = document.getElementById('imgDbscan');
const imgDeskewed = document.getElementById('imgDeskewed');
const imgFinal = document.getElementById('imgFinal');

let selectedFile = null;

// Event Listeners
uploadBtn.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', handleFileSelect);
copyBtn.addEventListener('click', copyToClipboard);
newAnalysisBtn.addEventListener('click', resetApp);
retryBtn.addEventListener('click', resetApp);

// Drag and drop
const uploadCard = document.querySelector('.upload-card');
uploadCard.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadCard.style.borderColor = 'var(--primary)';
});

uploadCard.addEventListener('dragleave', () => {
    uploadCard.style.borderColor = 'var(--border)';
});

uploadCard.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadCard.style.borderColor = 'var(--border)';
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
});

// File Selection
function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) {
        handleFile(file);
    }
}

function handleFile(file) {
    if (!file.type.startsWith('image/')) {
        showToast('Please select an image file', 'error');
        return;
    }

    selectedFile = file;
    fileInfo.textContent = `Selected: ${file.name} (${formatFileSize(file.size)})`;
    
    // Auto-process after selection
    processImage();
}

// Process Image
async function processImage() {
    if (!selectedFile) {
        showToast('Please select an image first', 'error');
        return;
    }

    // Show processing section
    uploadSection.classList.add('hidden');
    processingSection.classList.remove('hidden');
    resultsSection.classList.add('hidden');
    errorSection.classList.add('hidden');

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
        // Simulate progress steps
        updateProgress(0, 'Uploading image...');
        await sleep(300);
        
        updateProgress(15, 'Starting OCR pipeline...');
        await sleep(300);

        // Make API call
        const response = await fetch('/api/process', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }

        updateProgress(30, 'Applying illumination correction...');
        await sleep(500);

        updateProgress(45, 'Performing thresholding...');
        await sleep(500);

        updateProgress(60, 'Detecting clusters...');
        await sleep(500);

        updateProgress(75, 'Running DBSCAN analysis...');
        await sleep(500);

        updateProgress(85, 'Deskewing image...');
        await sleep(500);

        const data = await response.json();

        if (!data.success) {
            throw new Error(data.error || 'Processing failed');
        }

        updateProgress(95, 'Performing VLM OCR...');
        await sleep(500);

        updateProgress(100, 'Complete!');
        await sleep(300);

        // Display results
        displayResults(data);

    } catch (error) {
        console.error('Error:', error);
        showError(error.message);
    }
}

// Update Progress
function updateProgress(percent, status) {
    progressFill.style.width = `${percent}%`;
    progressText.textContent = `${percent}%`;
    processingStatus.textContent = status;
}

// Display Results
function displayResults(data) {
    // Hide processing, show results
    processingSection.classList.add('hidden');
    resultsSection.classList.remove('hidden');

    // Set OCR result
    ocrResult.textContent = data.ocr_result || 'No digits detected';

    // Set images
    imgOriginal.src = `data:image/png;base64,${data.images.original}`;
    imgIllumination.src = `data:image/png;base64,${data.images.illumination}`;
    imgThreshold.src = `data:image/png;base64,${data.images.threshold}`;
    imgClustered.src = `data:image/png;base64,${data.images.clustered}`;
    imgDbscan.src = `data:image/png;base64,${data.images.dbscan}`;
    imgDeskewed.src = `data:image/png;base64,${data.images.deskewed}`;
    imgFinal.src = `data:image/png;base64,${data.images.final}`;

    // Animate cards
    const cards = document.querySelectorAll('.pipeline-card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        setTimeout(() => {
            card.style.transition = 'all 0.5s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });

    showToast('Processing completed successfully!', 'success');
}

// Show Error
function showError(message) {
    processingSection.classList.add('hidden');
    errorSection.classList.remove('hidden');
    errorMessage.textContent = message;
}

// Copy to Clipboard
async function copyToClipboard() {
    const text = ocrResult.textContent;
    
    try {
        await navigator.clipboard.writeText(text);
        showToast('Copied to clipboard!', 'success');
        
        // Visual feedback
        copyBtn.style.transform = 'scale(0.9)';
        setTimeout(() => {
            copyBtn.style.transform = 'scale(1)';
        }, 150);
    } catch (error) {
        showToast('Failed to copy', 'error');
    }
}

// Reset App
function resetApp() {
    selectedFile = null;
    fileInput.value = '';
    fileInfo.textContent = '';
    
    uploadSection.classList.remove('hidden');
    processingSection.classList.add('hidden');
    resultsSection.classList.add('hidden');
    errorSection.classList.add('hidden');
    
    progressFill.style.width = '0%';
    progressText.textContent = '0%';
}

// Show Toast
function showToast(message, type = 'success') {
    toastMessage.textContent = message;
    toast.classList.remove('hidden');
    
    if (type === 'error') {
        toast.style.color = 'var(--error)';
    } else {
        toast.style.color = 'var(--success)';
    }
    
    setTimeout(() => {
        toast.classList.add('hidden');
    }, 3000);
}

// Utility Functions
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    console.log('Dot Matrix OCR Enterprise System initialized');
});
