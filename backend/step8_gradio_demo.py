"""
STEP 8: Gradio Demo with Confidence Scores
============================================
Interactive web demo for plastic waste classification using the
trained YOLOv8 model. Upload an image and get bounding box
predictions with class labels and confidence scores.

Run: python step8_gradio_demo.py
Opens at: http://localhost:7860
"""

import sys
from pathlib import Path

try:
    from ultralytics import YOLO
except ImportError:
    print("[FATAL] ultralytics not installed.")
    sys.exit(1)

try:
    import gradio as gr
except ImportError:
    print("[FATAL] gradio not installed. Run: pip install gradio")
    sys.exit(1)

import cv2
import numpy as np
import torch

# ──────────────────────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

# Try V2 model first, fall back to V1
V2_MODEL = PROJECT_ROOT / "outputs" / "train_v2" / "weights" / "best.pt"
V1_MODEL = PROJECT_ROOT / "outputs" / "train_v1" / "weights" / "best.pt"

IMG_SIZE = 640
CONF_THRESHOLD = 0.25
IOU_THRESHOLD = 0.45
DEVICE = "0" if torch.cuda.is_available() else "cpu"

CLASS_NAMES = {0: "PP", 1: "HDPE", 2: "PET", 3: "Rigid"}
CLASS_COLORS = {
    0: (46, 204, 113),    # PP - Green
    1: (52, 152, 219),    # HDPE - Blue
    2: (231, 76, 60),     # PET - Red
    3: (155, 89, 182),    # Rigid - Purple
}

# Load model globally
model = None


def load_model():
    """Load the best available YOLOv8 model."""
    global model
    if V2_MODEL.exists():
        model_path = V2_MODEL
        print(f"  Loading retrained model (V2): {model_path}")
    elif V1_MODEL.exists():
        model_path = V1_MODEL
        print(f"  Loading initial model (V1): {model_path}")
    else:
        print("[FATAL] No trained model found.")
        print("        Run step4_yolo_train.py first.")
        sys.exit(1)

    model = YOLO(str(model_path))
    print(f"  Model loaded successfully!")
    return model_path


def predict(image):
    """
    Run YOLOv8 inference on an uploaded image.
    Returns annotated image and detection summary.
    """
    if image is None:
        return None, "No image uploaded."

    if model is None:
        return None, "Model not loaded."

    # Run inference
    results = model.predict(
        source=image,
        imgsz=IMG_SIZE,
        conf=CONF_THRESHOLD,
        iou=IOU_THRESHOLD,
        device=DEVICE,
        verbose=False,
    )

    result = results[0]
    boxes = result.boxes

    # Convert image to BGR for OpenCV drawing
    if isinstance(image, np.ndarray):
        annotated = image.copy()
    else:
        annotated = np.array(image)

    # Build detection summary
    summary_lines = []
    detection_count = 0

    if boxes is not None and len(boxes) > 0:
        for i in range(len(boxes)):
            cls_id = int(boxes.cls[i])
            conf = float(boxes.conf[i])
            x1, y1, x2, y2 = [int(v) for v in boxes.xyxy[i].tolist()]

            cls_name = CLASS_NAMES.get(cls_id, f"Class_{cls_id}")
            color = CLASS_COLORS.get(cls_id, (255, 255, 255))

            # Draw bounding box
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 3)

            # Draw label background
            label = f"{cls_name} {conf:.2f}"
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
            cv2.rectangle(annotated, (x1, y1 - th - 10), (x1 + tw + 6, y1), color, -1)
            cv2.putText(annotated, label, (x1 + 3, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            summary_lines.append(f"  {cls_name}: {conf*100:.1f}% confidence")
            detection_count += 1

    if detection_count == 0:
        summary = "No plastics detected in this image."
    else:
        summary = f"Detected {detection_count} plastic item(s):\n" + "\n".join(summary_lines)

    return annotated, summary


def main():
    print("=" * 60)
    print("  STEP 8: Gradio Demo - Plastic Waste Classifier")
    print("=" * 60)

    model_path = load_model()

    print(f"\n  Device: {DEVICE}")
    print(f"  Confidence threshold: {CONF_THRESHOLD}")
    print(f"  Starting Gradio interface...\n")

    # Build Gradio interface
    with gr.Blocks(
        title="Erth - Plastic Waste Classifier",
        theme=gr.themes.Soft(primary_hue="emerald"),
    ) as demo:
        gr.Markdown(
            """
            # ♻️ Erth — AI Plastic Waste Classifier
            Upload an image of plastic waste to classify it into **PP**, **HDPE**, **PET**, or **Rigid**.
            The model uses YOLOv8 object detection trained on labeled plastic waste images.
            """
        )

        with gr.Row():
            with gr.Column(scale=1):
                input_image = gr.Image(
                    label="Upload Image",
                    type="numpy",
                    sources=["upload", "webcam"],
                )
                submit_btn = gr.Button("🔍 Classify", variant="primary", size="lg")

                gr.Markdown(
                    f"""
                    ### Model Info
                    - **Model**: YOLOv8s (fine-tuned)
                    - **Classes**: PP, HDPE, PET, Rigid
                    - **Confidence**: >= {CONF_THRESHOLD*100:.0f}%
                    - **Device**: {"GPU (" + torch.cuda.get_device_name(0) + ")" if torch.cuda.is_available() else "CPU"}
                    """
                )

            with gr.Column(scale=1):
                output_image = gr.Image(label="Detection Results", type="numpy")
                output_text = gr.Textbox(
                    label="Detection Summary",
                    lines=6,
                    interactive=False,
                )

        # Example images
        example_dir = PROJECT_ROOT / "dataset" / "img"
        if example_dir.exists():
            examples = sorted(list(example_dir.glob("*.jpg"))[:6] + list(example_dir.glob("*.jpeg"))[:6])
            if examples:
                gr.Examples(
                    examples=[[str(e)] for e in examples[:6]],
                    inputs=input_image,
                    outputs=[output_image, output_text],
                    fn=predict,
                    cache_examples=False,
                )

        submit_btn.click(
            fn=predict,
            inputs=input_image,
            outputs=[output_image, output_text],
        )

    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        inbrowser=True,
    )


if __name__ == "__main__":
    main()
