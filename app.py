from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
import cv2
import numpy as np
from sklearn.cluster import DBSCAN
import base64
from openai import OpenAI
import os
import uuid
from pathlib import Path
import shutil
import logging
import time

# Initialize FastAPI app FIRST
app = FastAPI(title="Dot Matrix OCR Enterprise System")

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info("Checking environment variables...")

# Get environment variables directly (Hugging Face sets these)
api_key = os.getenv("OPENROUTER_API_KEY")
model = os.getenv("OCR_MODEL", "openrouter/free")  # Default to free

if not api_key:
    logger.warning("OPENROUTER_API_KEY environment variable not set")
else:
    logger.info(f"API key found: {bool(api_key)}")
    logger.info(f"OCR model configured: {model}")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
logger.info(f"Upload directory created/verified: {UPLOAD_DIR.absolute()}")

# Serve static files (CSS, JS) from root
# app.mount("/static", StaticFiles(directory="."), name="static")
logger.info("Static files mounted at /static")

logger.info("FastAPI app initialized successfully")

# =============================================================================
# ILLUMINATION CORRECTION
# =============================================================================

class AdaptiveDotMatrixOCR:
    def adaptive_illumination_correction(self, gray):
        """Advanced illumination correction that handles both bright and dim regions"""
        blurred = cv2.GaussianBlur(gray, (0, 0), sigmaX=50, sigmaY=50)
        blurred = np.where(blurred == 0, 1, blurred)
        normalized = cv2.divide(gray.astype(np.float32), blurred.astype(np.float32))
        normalized = cv2.normalize(normalized, None, 0, 255, cv2.NORM_MINMAX)
        normalized = normalized.astype(np.uint8)
        return normalized
    
    def process_illumination(self, image_path, output_path):
        """Process image and save illumination corrected version"""
        logger.debug(f"Loading image for illumination correction: {image_path}")
        img = cv2.imread(str(image_path))
        if img is None:
            logger.error(f"Could not read image from {image_path}")
            raise ValueError(f"Could not read image from {image_path}")
        
        logger.debug(f"Image loaded successfully, shape: {img.shape}")
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        logger.debug("Converted to grayscale")
        illumination_corrected = self.adaptive_illumination_correction(gray)
        logger.debug("Applied illumination correction")
        cv2.imwrite(str(output_path), illumination_corrected)
        logger.debug(f"Saved illumination corrected image to: {output_path}")
        return output_path

# =============================================================================
# IMAGE PROCESSING
# =============================================================================

class ImageProcessor:
    def __init__(self):
        self.threshold_value = 80
        self.min_cluster_size = 10
        self.eps = 50
        self.min_samples = 8
        self.min_bbox_area = 20
        self.max_bbox_area = 650
        self.connection_radius = 22
        self.dilation_kernel_size = 5
        self.dilation_iterations = 1
        self.min_line_spacing = 20
    
    def cluster_diameter(self, mask):
        """Calculate the diameter of a cluster"""
        y_idxs, x_idxs = np.where(mask > 0)
        if len(y_idxs) == 0 or len(x_idxs) == 0:
            return 1
        x_range = x_idxs.max() - x_idxs.min()
        y_range = y_idxs.max() - y_idxs.min()
        return max(x_range, y_range)
    
    def draw_tapered_line(self, img, pt1, pt2, radius1, radius2, color=(255, 255, 255)):
        """Draw a tapered line between two points"""
        pt1 = np.array(pt1)
        pt2 = np.array(pt2)
        dist = np.linalg.norm(pt2 - pt1)
        steps = int(dist)
        if steps == 0:
            return
        for i in range(steps + 1):
            alpha = i / steps
            point = (1 - alpha) * pt1 + alpha * pt2
            radius = int((1 - alpha) * radius1 + alpha * radius2)
            cv2.circle(img, tuple(point.astype(int)), radius, color, -1)
    
    def find_vertical_separation_lines_all_possible(self, dilated_mask, min_spacing=20):
        """Find vertical separation lines between digit groups"""
        height, width = dilated_mask.shape
        vertical_proj = np.sum(dilated_mask, axis=0) // 255
        
        zero_columns = []
        for x in range(width):
            if vertical_proj[x] == 0:
                zero_columns.append(x)
        
        if len(zero_columns) == 0:
            return []
        
        groups = []
        current_group = [zero_columns[0]]
        
        for i in range(1, len(zero_columns)):
            if zero_columns[i] == zero_columns[i-1] + 1:
                current_group.append(zero_columns[i])
            else:
                groups.append(current_group)
                current_group = [zero_columns[i]]
        groups.append(current_group)
        
        candidate_lines = []
        for group in groups:
            if len(group) >= 3:
                mid = len(group) // 2
                candidate_lines.append(group[mid])
        
        if len(candidate_lines) == 0:
            return []
        
        separation_lines = [candidate_lines[0]]
        for line in candidate_lines[1:]:
            if line - separation_lines[-1] >= min_spacing:
                separation_lines.append(line)
        
        return separation_lines
    
    def process_single_digit_block(self, block_img, block_mask):
        """Process a single digit block to connect nearby clusters with tapered lines"""
        block_gray = cv2.cvtColor(block_img, cv2.COLOR_BGR2GRAY)
        _, block_thresh = cv2.threshold(block_gray, self.threshold_value, 255, cv2.THRESH_BINARY)
        
        kernel = np.ones((3, 3), np.uint8)
        block_thresh_closed = cv2.morphologyEx(block_thresh, cv2.MORPH_CLOSE, kernel)
        
        block_num_labels, block_labels, block_stats, block_centroids = cv2.connectedComponentsWithStats(
            block_thresh_closed, connectivity=8
        )
        
        block_valid_clusters = []
        block_cluster_centroids = []
        
        for i in range(1, block_num_labels):
            area = block_stats[i, cv2.CC_STAT_AREA]
            if area >= self.min_cluster_size:
                block_valid_clusters.append(i)
                block_cluster_centroids.append(block_centroids[i])
        
        if len(block_valid_clusters) == 0:
            return block_img
        
        block_cluster_centroids = np.array(block_cluster_centroids)
        block_dbscan = DBSCAN(eps=self.eps, min_samples=self.min_samples)
        block_mega_labels = block_dbscan.fit_predict(block_cluster_centroids)
        
        block_valid_cluster_indices = []
        for idx, mega_label in enumerate(block_mega_labels):
            if mega_label != -1:
                block_valid_cluster_indices.append(block_valid_clusters[idx])
        
        if len(block_valid_cluster_indices) < 2:
            return block_img
        
        block_output = block_img.copy()
        
        for i, id1 in enumerate(block_valid_cluster_indices):
            for j, id2 in enumerate(block_valid_cluster_indices):
                if j <= i:
                    continue
                c1 = block_centroids[id1]
                c2 = block_centroids[id2]
                dist = np.linalg.norm(np.array(c1) - np.array(c2))
                
                if dist <= self.connection_radius:
                    mask1 = (block_labels == id1).astype(np.uint8) * 255
                    mask2 = (block_labels == id2).astype(np.uint8) * 255
                    radius1 = self.cluster_diameter(mask1) // 2
                    radius2 = self.cluster_diameter(mask2) // 2
                    self.draw_tapered_line(block_output, c1, c2, radius1, radius2, color=(255, 255, 255))
        
        return block_output
    
    def process_image(self, illumination_corrected_path, session_dir):
        """Main image processing pipeline with intermediate outputs"""
        logger.debug(f"Starting image processing for: {illumination_corrected_path}")
        img = cv2.imread(str(illumination_corrected_path))
        if img is None:
            logger.error(f"Failed to load image: {illumination_corrected_path}")
            return None, None, None, None
        
        logger.debug(f"Image loaded, shape: {img.shape}")
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        logger.debug("Converted to grayscale")
        
        # Threshold
        logger.debug("Applying thresholding")
        _, thresh = cv2.threshold(gray, self.threshold_value, 255, cv2.THRESH_BINARY)
        thresh_path = session_dir / "3_thresholded.png"
        cv2.imwrite(str(thresh_path), thresh)
        logger.debug(f"Saved thresholded image: {thresh_path}")
        
        # Connected components
        kernel = np.ones((3, 3), np.uint8)
        thresh_closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(thresh_closed, connectivity=8)
        
        # Filter clusters
        valid_clusters = []
        cluster_centroids = []
        for i in range(1, num_labels):
            area = stats[i, cv2.CC_STAT_AREA]
            if area >= self.min_cluster_size:
                valid_clusters.append(i)
                cluster_centroids.append(centroids[i])
        
        if len(valid_clusters) == 0:
            return None, None, None, None
        
        # Visualize clustered image
        clustered_viz = np.zeros_like(img)
        for cluster_id in valid_clusters:
            mask = (labels == cluster_id).astype(np.uint8) * 255
            clustered_viz[mask > 0] = [0, 255, 0]  # Green clusters
        clustered_path = session_dir / "4_clustered.png"
        cv2.imwrite(str(clustered_path), clustered_viz)
        
        cluster_centroids = np.array(cluster_centroids)
        
        # DBSCAN
        dbscan = DBSCAN(eps=self.eps, min_samples=self.min_samples)
        mega_labels = dbscan.fit_predict(cluster_centroids)
        
        valid_cluster_indices = []
        for idx, mega_label in enumerate(mega_labels):
            if mega_label != -1:
                valid_cluster_indices.append(valid_clusters[idx])
        
        # Visualize DBSCAN result
        dbscan_viz = np.zeros_like(img)
        filtered_mask = np.zeros_like(thresh)
        for cluster_id in valid_cluster_indices:
            filtered_mask[labels == cluster_id] = 255
            dbscan_viz[labels == cluster_id] = [255, 0, 255]  # Magenta
        dbscan_path = session_dir / "5_dbscan.png"
        cv2.imwrite(str(dbscan_path), dbscan_viz)
        
        # Filter by bbox area
        contours, _ = cv2.findContours(filtered_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        final_mask = np.zeros_like(gray)
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            bbox_area = w * h
            if self.min_bbox_area <= bbox_area <= self.max_bbox_area:
                final_mask[y:y+h, x:x+w] = filtered_mask[y:y+h, x:x+w]
        
        # Dilation
        dilation_kernel = np.ones((self.dilation_kernel_size, self.dilation_kernel_size), np.uint8)
        dilated_mask = cv2.dilate(final_mask, dilation_kernel, iterations=self.dilation_iterations)
        
        # Deskewing
        coords = np.column_stack(np.where(dilated_mask > 0))
        if len(coords) == 0:
            return None, None, None, None
        
        rect = cv2.minAreaRect(coords)
        angle = rect[-1]
        
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
        
        (h_img, w_img) = img.shape[:2]
        center = (w_img // 2, h_img // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        
        cos = abs(M[0, 0])
        sin = abs(M[0, 1])
        new_w = int((h_img * sin) + (w_img * cos))
        new_h = int((h_img * cos) + (w_img * sin))
        
        M[0, 2] += (new_w / 2) - center[0]
        M[1, 2] += (new_h / 2) - center[1]
        
        rotated_img = cv2.warpAffine(img, M, (new_w, new_h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        rotated_final_mask = cv2.warpAffine(final_mask, M, (new_w, new_h), flags=cv2.INTER_NEAREST)
        rotated_dilated_mask = cv2.warpAffine(dilated_mask, M, (new_w, new_h), flags=cv2.INTER_NEAREST)
        
        y_idxs, x_idxs = np.where(rotated_dilated_mask > 0)
        x_min, x_max = x_idxs.min(), x_idxs.max()
        y_min, y_max = y_idxs.min(), y_idxs.max()
        
        cropped_img = rotated_img[y_min:y_max+1, x_min:x_max+1]
        cropped_final_mask = rotated_final_mask[y_min:y_max+1, x_min:x_max+1]
        cropped_dilated_mask = rotated_dilated_mask[y_min:y_max+1, x_min:x_max+1]
        
        deskewed_path = session_dir / "6_deskewed.png"
        cv2.imwrite(str(deskewed_path), cropped_img)
        
        # Find separation lines
        separation_lines = self.find_vertical_separation_lines_all_possible(cropped_dilated_mask, self.min_line_spacing)
        if len(separation_lines) < 3:
            separation_lines = self.find_vertical_separation_lines_all_possible(cropped_dilated_mask, min_spacing=10)
        
        # Process each digit block
        height, width = cropped_img.shape[:2]
        boundaries = [0] + separation_lines + [width]
        blocks_with_lines = cropped_img.copy()
        
        for i in range(len(boundaries)-1):
            left = boundaries[i]
            right = boundaries[i+1]
            if right - left < 5:
                continue
            
            block_img = cropped_img[:, left:right]
            block_mask = cropped_dilated_mask[:, left:right]
            processed_block = self.process_single_digit_block(block_img, block_mask)
            blocks_with_lines[:, left:right] = processed_block
        
        final_path = session_dir / "7_final.png"
        cv2.imwrite(str(final_path), blocks_with_lines)
        
        return thresh_path, clustered_path, dbscan_path, deskewed_path

# =============================================================================
# VLM OCR
# =============================================================================

class VLMOCR:
    def __init__(self, api_key):
        logger.info("Initializing VLMOCR with OpenAI client")
        try:
            import httpx

            # Create httpx client with no proxy support
            http_client = httpx.Client(
                timeout=60.0,
                follow_redirects=True,
                trust_env=False  # Don't trust environment variables for proxies
            )

            # Create OpenAI client with custom httpx client
            self.client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=api_key,
                http_client=http_client
            )
            logger.info("OpenAI client initialized successfully with custom httpx client")

        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {str(e)}", exc_info=True)
            logger.error(f"Exception type: {type(e).__name__}")
            raise
    
    def perform_ocr(self, image_path, max_retries=3):
        """Perform OCR using VLM with retry logic for rate limiting"""
        logger.debug(f"Starting VLM OCR for image: {image_path}")

        if not hasattr(self, 'client') or self.client is None:
            raise ValueError("OpenAI client not properly initialized")

        # Use environment variable directly
        model = os.getenv("OCR_MODEL", "openrouter/free")
        logger.info(f"Using OCR model: {model}")

        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')

        logger.debug(f"Image encoded to base64, length: {len(base64_image)} characters")

        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Making OpenAI API call to OpenRouter (attempt {attempt}/{max_retries}) with model: {model}")
                completion = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "What are the digits mentioned in the image? Answer in one line nothing else only digits."
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{base64_image}"
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=50  # Limit tokens for faster response
                )

                if not completion.choices or len(completion.choices) == 0:
                    logger.error(f"API response missing choices: {completion}")
                    raise ValueError("API response missing choices")

                choice = completion.choices[0]
                if not choice.message:
                    logger.error(f"API response choice missing message: {choice}")
                    raise ValueError("API response choice missing message")

                result = choice.message.content
                if not result or not result.strip():
                    logger.warning(f"API returned empty or whitespace-only result: '{result}'")
                    raise ValueError("API returned empty OCR result")
                
                # Clean up result - keep only digits
                cleaned_result = ''.join(filter(str.isdigit, result))
                if cleaned_result:
                    result = cleaned_result
                
                logger.info(f"OpenAI API call successful, result: '{result}'")
                return result

            except Exception as e:
                last_error = e
                logger.error(f"OpenAI API call failed (attempt {attempt}/{max_retries}): {str(e)}")
                logger.error(f"Error type: {type(e).__name__}")

                # Check if it's a rate limit error (429) - retry with backoff
                is_rate_limit = '429' in str(e) or 'rate' in str(e).lower() or 'quota' in str(e).lower()
                if is_rate_limit and attempt < max_retries:
                    wait_time = 2 ** attempt * 5  # 10s, 20s, 40s
                    logger.warning(f"Rate limited (429). Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    
                    # If rate limited on free model, you might want to switch to another free model
                    # but openrouter/free should handle this automatically
                    continue
                elif not is_rate_limit:
                    # Non-rate-limit error, don't retry
                    break

        # All retries exhausted
        logger.error(f"All {max_retries} attempts failed for OCR")
        raise HTTPException(
            status_code=503,
            detail="OCR service is temporarily unavailable. Free models might be rate-limited. Please try again in a minute or consider using a specific model."
        )

# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.get("/")
async def read_root():
    return FileResponse("index.html")

@app.get("/index.html")
async def read_index():
    return FileResponse("index.html")

@app.post("/api/process")
async def process_image(
    file: UploadFile = File(...),
):
    """Process uploaded image through the entire OCR pipeline"""
    logger.info(f"Received processing request for file: {file.filename}, size: {file.size} bytes")

    # Get API key from environment variable (set by Hugging Face Secrets)
    api_key = os.getenv("OPENROUTER_API_KEY")
    
    if not api_key:
        logger.error("OPENROUTER_API_KEY environment variable not set")
        logger.error("Please set OPENROUTER_API_KEY in Hugging Face Space Secrets")
        raise HTTPException(
            status_code=500, 
            detail="OCR service not configured. Please contact the administrator."
        )
    
    logger.info(f"API key present: {bool(api_key)}")
    
    try:
        logger.info("Starting image processing pipeline")

        # Create session directory
        session_id = str(uuid.uuid4())
        session_dir = UPLOAD_DIR / session_id
        session_dir.mkdir(exist_ok=True)
        logger.info(f"Created session directory: {session_dir}")

        # Save uploaded file
        original_path = session_dir / "1_original.png"
        logger.info(f"Saving uploaded file to: {original_path}")
        with open(original_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info(f"File saved successfully, size: {original_path.stat().st_size} bytes")
        
        # Step 1: Illumination Correction
        logger.info("Starting Step 1: Illumination Correction")
        illumination_path = session_dir / "2_illumination.png"
        ocr_processor = AdaptiveDotMatrixOCR()
        logger.info(f"Processing illumination correction: {original_path} -> {illumination_path}")
        ocr_processor.process_illumination(original_path, illumination_path)
        logger.info("Illumination correction completed successfully")
        
        # Step 2: Image Processing
        logger.info("Starting Step 2: Image Processing")
        image_processor = ImageProcessor()
        logger.info(f"Processing image: {illumination_path}")
        thresh_path, clustered_path, dbscan_path, deskewed_path = image_processor.process_image(
            illumination_path, session_dir
        )
        
        if thresh_path is None:
            logger.error("Image processing failed - no threshold path returned")
            raise HTTPException(status_code=400, detail="Image processing failed")
        logger.info("Image processing completed successfully")
        
        # Step 3: VLM OCR
        logger.info("Starting Step 3: VLM OCR")
        final_path = session_dir / "7_final.png"
        vlm_ocr = VLMOCR(api_key)
        logger.info(f"Performing OCR on: {final_path}")
        try:
            ocr_result = vlm_ocr.perform_ocr(final_path)
        except Exception as ocr_err:
            logger.error(f"OCR failed after retries: {ocr_err}")
            raise HTTPException(
                status_code=503,
                detail="OCR service is temporarily unavailable (rate limited). Please try again in a minute."
            )
        logger.info(f"OCR completed, result length: {len(ocr_result) if ocr_result else 0} characters")
        
        # Convert images to base64 for response
        logger.info("Converting images to base64 for response")
        def image_to_base64(path):
            with open(path, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode('utf-8')
        
        response_data = {
            "success": True,
            "session_id": session_id,
            "images": {
                "original": image_to_base64(original_path),
                "illumination": image_to_base64(illumination_path),
                "threshold": image_to_base64(thresh_path),
                "clustered": image_to_base64(clustered_path),
                "dbscan": image_to_base64(dbscan_path),
                "deskewed": image_to_base64(deskewed_path),
                "final": image_to_base64(final_path)
            },
            "ocr_result": ocr_result
        }
        logger.info(f"Response prepared successfully, session_id: {session_id}")
        return JSONResponse(response_data)
        
    except Exception as e:
        logger.error(f"Error in process_image: {str(e)}", exc_info=True)
        if 'session_dir' in locals():
            logger.error(f"Session directory: {session_dir}")
        if 'original_path' in locals():
            logger.error(f"Original file exists: {original_path.exists()}")
        raise HTTPException(status_code=500, detail=str(e))

# Serve CSS and JS files
@app.get("/styles.css")
async def get_css():
    return FileResponse("styles.css")

@app.get("/script.js")
async def get_js():
    return FileResponse("script.js")

@app.get("/favicon.ico")
async def get_favicon():
    return FileResponse("favicon.ico", media_type="image/x-icon")

if __name__ == "__main__":
    import uvicorn
    # Use PORT environment variable for Hugging Face Spaces compatibility
    port = int(os.getenv("PORT", 7860))  # HF Spaces uses port 7860 by default
    logger.info(f"Starting server on port {port}")
    logger.info(f"Upload directory: {UPLOAD_DIR.absolute()}")
    logger.info(f"Static directory: {Path('.').absolute()}")
    logger.info(f"Index file exists: {Path('index.html').exists()}")
    uvicorn.run(app, host="0.0.0.0", port=port)