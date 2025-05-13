# app/processing/video_processor.py
import cv2
from ultralytics import YOLO
import logging # Use logging for better tracking
import torch # Ensure torch is available

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def process_video(input_video_path: str, output_video_path: str, model_path: str):
    """
    Processes a video file using a YOLOv8 model to detect objects (traffic signs),
    annotates the video with bounding boxes and labels, and saves the result.

    Args:
        input_video_path (str): Path to the input video file.
        output_video_path (str): Path where the processed video will be saved.
        model_path (str): Path to the trained YOLOv8 model (.pt file).
    """
    logging.info(f"Starting video processing for: {input_video_path}")
    logging.info(f"Using model: {model_path}")
    logging.info(f"Output will be saved to: {output_video_path}")

    # Check GPU availability (optional but recommended)
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    logging.info(f"Using device: {device}")

    try:
        # Load the YOLOv8 model
        model = YOLO(model_path)
        model.to(device) # Move model to GPU if available
        class_names = model.names # Get class names from the model
        logging.info(f"Model loaded successfully. Class names: {class_names}")

    except Exception as e:
        logging.error(f"Error loading YOLO model: {e}", exc_info=True)
        raise  # Re-raise the exception to be caught by the route

    # Open the input video file
    cap = cv2.VideoCapture(input_video_path)
    if not cap.isOpened():
        logging.error(f"Error opening video file: {input_video_path}")
        raise IOError(f"Cannot open video file: {input_video_path}")

    # Get video properties
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    logging.info(f"Video properties: {frame_width}x{frame_height} @ {fps:.2f} FPS, Total Frames: {total_frames}")

    # Define the codec and create VideoWriter object
    # Using 'mp4v' codec for MP4 output. Other options: 'XVID' for AVI
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video_writer = cv2.VideoWriter(output_video_path, fourcc, fps, (frame_width, frame_height))
    if not video_writer.isOpened():
         logging.error(f"Error initializing video writer for: {output_video_path}")
         cap.release() # Release the input video capture object
         raise IOError(f"Cannot initialize video writer for: {output_video_path}")


    logging.info("Starting frame processing loop...")
    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            logging.info("End of video reached or cannot read frame.")
            break

        frame_count += 1
        if frame_count % 100 == 0: # Log progress every 100 frames
             logging.info(f"Processing frame {frame_count}/{total_frames}")

        # Perform inference
        # You might need to adjust parameters like conf, iou based on your training/notebook
        try:
            results = model.predict(frame, device=device, verbose=False) # verbose=False to reduce console spam
        except Exception as e:
            logging.error(f"Error during model prediction on frame {frame_count}: {e}", exc_info=True)
            # Decide if you want to skip the frame or stop processing
            continue # Skip this frame

        # Process results - results[0] contains detections for the first image (frame)
        annotated_frame = frame.copy() # Work on a copy to preserve original
        detections = results[0].boxes.data.cpu().numpy() # Get boxes, scores, classes as numpy array

        if len(detections) > 0:
            for i, det in enumerate(detections):
                x1, y1, x2, y2, score, class_id = det
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2) # Convert coordinates to integers
                class_id = int(class_id)

                # Get class name
                label = class_names.get(class_id, f"Class_{class_id}") # Use dictionary .get for safety
                label_with_score = f"{label}: {score:.2f}"

                # Draw bounding box
                # You can customize color, thickness etc.
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

                # Put label text above the bounding box
                (text_width, text_height), baseline = cv2.getTextSize(label_with_score, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                # Ensure text background doesn't go out of frame (simple check)
                text_y = y1 - 10 if y1 - 10 > text_height else y1 + text_height + baseline
                cv2.rectangle(annotated_frame, (x1, text_y - text_height - baseline), (x1 + text_width, text_y), (0, 255, 0), -1) # Text background
                cv2.putText(annotated_frame, label_with_score, (x1, text_y - baseline // 2), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2) # Black text


        # Write the annotated frame to the output video
        video_writer.write(annotated_frame)

    # Release resources
    logging.info("Finished processing all frames. Releasing resources.")
    cap.release()
    video_writer.release()
    # cv2.destroyAllWindows() # Not strictly necessary in backend, but good practice
    logging.info(f"Video processing complete. Output saved to: {output_video_path}")


# Example of how to run this script standalone (for testing)
if __name__ == '__main__':
    # Create dummy files for testing if they don't exist
    # You should replace these with actual paths for testing
    test_input_path = "../test_videos/sample.mp4" # Adjust path as needed
    test_output_path = "../outputs/test_output.mp4" # Adjust path as needed
    test_model_path = "../ml_model/best.pt" # Adjust path as needed

    # Make sure dummy directories exist if running standalone
    import os
    os.makedirs(os.path.dirname(test_input_path), exist_ok=True)
    os.makedirs(os.path.dirname(test_output_path), exist_ok=True)
    os.makedirs(os.path.dirname(test_model_path), exist_ok=True)
    # You'd need a sample video and model file at these locations to test

    print(f"Running test processing...")
    print(f"Input: {os.path.abspath(test_input_path)}")
    print(f"Output: {os.path.abspath(test_output_path)}")
    print(f"Model: {os.path.abspath(test_model_path)}")

    if not os.path.exists(test_input_path):
         print(f"ERROR: Test input video not found at {test_input_path}")
    elif not os.path.exists(test_model_path):
         print(f"ERROR: Test model file not found at {test_model_path}")
    else:
        try:
            process_video(test_input_path, test_output_path, test_model_path)
            print("Test processing finished successfully.")
        except Exception as e:
            print(f"Test processing failed: {e}")