from ultralytics import YOLO
import cv2
import matplotlib.pyplot as plt
import numpy as np
import os

# Load your trained model
model = YOLO("runs/detect/metal-engraving-yolov83/weights/best.pt")

# Test on a sample image
def test_detection(image_path=None):
    """
    Test YOLO detection on an image
    
    Args:
        image_path: Path to image file. If None, will look for test images.
    """
    # If no path provided, look for test images
    if image_path is None:
        # Try to find any image in current directory
        possible_images = [f for f in os.listdir('.') 
                          if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))]
        
        if possible_images:
            image_path = possible_images[0]
            print(f"Using image: {image_path}")
        else:
            # Use one of your training images
            dataset_path = "metal-engraving-text/test/images"
            if os.path.exists(dataset_path):
                test_images = os.listdir(dataset_path)
                if test_images:
                    image_path = os.path.join(dataset_path, test_images[0])
                    print(f"Using dataset image: {image_path}")
                else:
                    print("No test images found. Please provide an image path.")
                    return None
            else:
                print("No test images found. Please provide an image path.")
                return None
    
    # Check if image exists
    if not os.path.exists(image_path):
        print(f"Image not found: {image_path}")
        # List available images
        print("\nAvailable images in current directory:")
        for f in os.listdir('.'):
            if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tiff')):
                print(f"  - {f}")
        return None
    
    print(f"Processing image: {image_path}")
    
    # Run inference with lower confidence for engraved text
    results = model(image_path, conf=0.3, iou=0.4)  # Even lower confidence for better detection
    
    # Display results
    for i, result in enumerate(results):
        print(f"\nResults for image {i+1}:")
        
        # Print detection info
        if result.boxes is not None:
            print(f"Detected {len(result.boxes)} text regions:")
            for j, box in enumerate(result.boxes):
                conf = box.conf[0].item()
                cls = box.cls[0].item()
                bbox = box.xyxy[0].cpu().numpy()
                print(f"  Region {j+1}: confidence={conf:.3f}, bbox={bbox}")
        
        # Plot results
        img = result.plot()  # Draw bounding boxes
        
        # Save result
        output_path = f"detection_result_{os.path.basename(image_path)}"
        cv2.imwrite(output_path, img)
        print(f"\nResult saved to: {output_path}")
        
        # Display
        plt.figure(figsize=(12, 8))
        plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        plt.title(f"Detection Results - {os.path.basename(image_path)}")
        plt.axis('off')
        plt.show()
        
        # Also show original image for comparison
        original_img = cv2.imread(image_path)
        plt.figure(figsize=(12, 8))
        plt.imshow(cv2.cvtColor(original_img, cv2.COLOR_BGR2RGB))
        plt.title(f"Original Image - {os.path.basename(image_path)}")
        plt.axis('off')
        plt.show()
    
    return results

# Alternative: Test on multiple images
def test_on_dataset():
    """Test on all images in the test folder"""
    test_dir = "metal-engraving-text/test/images"
    
    if not os.path.exists(test_dir):
        print(f"Test directory not found: {test_dir}")
        print("\nAvailable directories:")
        for item in os.listdir('.'):
            if os.path.isdir(item):
                print(f"  - {item}")
        return
    
    image_files = [f for f in os.listdir(test_dir) 
                  if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    
    if not image_files:
        print(f"No images found in {test_dir}")
        return
    
    print(f"Found {len(image_files)} test images")
    
    all_results = []
    for img_file in image_files[:5]:  # Test on first 5 images only
        print(f"\n{'='*50}")
        print(f"Testing on: {img_file}")
        print('='*50)
        
        img_path = os.path.join(test_dir, img_file)
        results = test_detection(img_path)
        if results:
            all_results.append((img_file, results))
    
    return all_results

# Run test
if __name__ == "__main__":
    # Option 1: Test on a specific image (uncomment and modify path)
    # test_detection("path/to/your/image.jpg")
    
    # Option 2: Try to auto-find an image
    test_detection()
    
    # Option 3: Test on dataset
    # test_on_dataset()