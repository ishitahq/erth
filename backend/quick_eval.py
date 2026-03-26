import torch
from ultralytics import YOLO

def main():
    model = YOLO(r"d:\Erth\outputs\train_v2\weights\best.pt")
    
    print("\nEvaluating on Training Set...")
    metrics_train = model.val(data=r"d:\Erth\dataset\data_expanded.yaml", split="train", imgsz=640, plots=False, verbose=False)
    
    print("\nEvaluating on Test Set...")
    metrics_test = model.val(data=r"d:\Erth\dataset\data_expanded.yaml", split="test", imgsz=640, plots=False, verbose=False)
    
    print("\n================== ACCURACY SUMMARY ==================")
    print(f"Training Accuracy (mAP@0.5):  {metrics_train.box.map50 * 100:.2f}%")
    print(f"Testing Accuracy (mAP@0.5):   {metrics_test.box.map50 * 100:.2f}%")
    print("======================================================")

if __name__ == "__main__":
    main()
