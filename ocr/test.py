from ultralytics import YOLO

def train_model():
    # Load a pretrained YOLOv8 model
    model = YOLO("yolov8n.pt") 

    # Train on your dataset
    model.train(
        data="metal-engraving-text/data.yaml",  # path to your data.yaml
        epochs=100,                             # number of training epochs
        batch=8,                                # adjust depending on GPU
        imgsz=640,                              # image size
        lr0=0.001,                              # learning rate
        pretrained=True,                        # start from pretrained weights
        name="metal-engraving-yolov8",          # folder to save results
        workers=4                               # You can set this to 0 if it still crashes
    )

if __name__ == '__main__':
    train_model()