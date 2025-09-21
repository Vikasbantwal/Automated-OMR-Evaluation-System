import cv2
import numpy as np

def preprocess_image(image_path):
    """
    Preprocess OMR image with enhanced preprocessing
    """
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not load image from {image_path}")
    
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Apply Gaussian blur to reduce noise
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Apply adaptive thresholding for better handling of lighting variations
    thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                  cv2.THRESH_BINARY_INV, 11, 2)
    
    return thresh

def detect_bubbles(thresh, min_area=300, max_area=2000):
    """
    Detect contours that represent bubbles with improved filtering
    """
    # Find contours
    contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    bubbles = []
    
    for c in contours:
        area = cv2.contourArea(c)
        (x, y, w, h) = cv2.boundingRect(c)
        aspect_ratio = w / float(h)
        
        # Filter based on area and aspect ratio (circular bubbles)
        if (min_area <= area <= max_area) and (0.7 <= aspect_ratio <= 1.3):
            bubbles.append((x, y, w, h))
    
    return bubbles

def sort_bubbles(bubbles, total_questions=100, questions_per_row=5, choices=4):
    """
    Sort detected bubbles by row and column with dynamic calculation
    """
    if not bubbles:
        return []
    
    # Calculate approximate row height
    y_coords = [b[1] for b in bubbles]
    min_y, max_y = min(y_coords), max(y_coords)
    
    # Estimate rows based on total questions and questions per row
    total_rows = (total_questions + questions_per_row - 1) // questions_per_row
    approx_row_height = (max_y - min_y) / (total_rows - 1) if total_rows > 1 else 50
    
    # Sort by y first (row), then x (col)
    bubbles = sorted(bubbles, key=lambda b: (b[1] // approx_row_height, b[0]))
    return bubbles

def get_filled_answers(thresh, bubbles, threshold_ratio=0.4):
    """
    Check which bubble is filled per question with improved detection
    """
    answers = []
    num_choices = 4  # a, b, c, d
    
    for q in range(0, len(bubbles), num_choices):
        question_bubbles = bubbles[q:q + num_choices]
        if len(question_bubbles) != num_choices:
            continue
        
        filled_choices = []
        max_fill = -1
        chosen = -1
        
        for idx, (x, y, w, h) in enumerate(question_bubbles):
            # Extract the bubble region
            roi = thresh[y:y+h, x:x+w]
            
            # Calculate the percentage of filled pixels
            total_pixels = w * h
            if total_pixels == 0:
                continue
                
            filled_ratio = cv2.countNonZero(roi) / total_pixels
            
            # Track the most filled bubble
            if filled_ratio > max_fill:
                max_fill = filled_ratio
                chosen = idx
            
            # If filled ratio exceeds threshold, mark as filled
            if filled_ratio > threshold_ratio:
                filled_choices.append(idx)
        
        # Handle single and multiple answers
        if len(filled_choices) == 1:
            answers.append(filled_choices[0])
        elif len(filled_choices) > 1:
            # For multiple choice questions, we'll store as list
            answers.append(filled_choices)
        elif max_fill > 0.1:  # Lower threshold for single detection
            answers.append(chosen)
        else:
            answers.append(-1)  # No answer
    
    return answers