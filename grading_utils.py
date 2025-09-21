import pandas as pd
import re

def load_answer_key(answer_path):
    """
    Improved answer key loading with better parsing for your specific format
    """
    # Read the Excel file
    df = pd.read_excel(answer_path, header=None)
    
    letter_map = {'a': 0, 'b': 1, 'c': 2, 'd': 3}
    correct_answers = []
    
    # Extract only the answer cells (ignore headers and empty cells)
    for row_idx, row in df.iterrows():
        for cell in row:
            if pd.isna(cell):
                continue
                
            cell_str = str(cell).strip().lower()
            
            # Skip header rows
            if any(keyword in cell_str for keyword in ['python', 'eda', 'sol', 'power bi', 'statistics', 'key', 'set']):
                continue
                
            # Extract answer using regex
            match = re.search(r'(\d+)\s*[.-]\s*([a-d]+)', cell_str)
            if match:
                answer_part = match.group(2).strip()
                
                # Handle multiple answers (like "ab.d")
                if any(sep in answer_part for sep in [',', '.', ' ']):
                    multi_answers = []
                    for char in answer_part:
                        if char in letter_map:
                            multi_answers.append(letter_map[char])
                    correct_answers.extend(multi_answers)
                elif answer_part in letter_map:
                    correct_answers.append(letter_map[answer_part])
    
    # Ensure we have exactly 100 answers
    if len(correct_answers) > 100:
        correct_answers = correct_answers[:100]
    elif len(correct_answers) < 100:
        # Pad with -1 if we don't have enough answers
        correct_answers.extend([-1] * (100 - len(correct_answers)))
    
    return correct_answers

def grade_sheet(student_answers, correct_answers):
    """
    Compare student answers with correct answers
    Handles both single and multiple answer questions
    """
    score = 0
    comparison = []
    detailed_results = []
    
    # Ensure we only grade up to the number of correct answers
    limit = min(len(student_answers), len(correct_answers))
    
    for i in range(limit):
        s = student_answers[i] if i < len(student_answers) else -1
        c = correct_answers[i] if i < len(correct_answers) else -1
        
        if c == -1:
            # No key for this question
            comparison.append("NA")
            detailed_results.append({"question": i+1, "status": "No key", "student_answer": s, "correct_answer": c})
        elif isinstance(c, list):
            # Multiple correct answers
            if isinstance(s, list) and set(s) == set(c):
                score += 1
                comparison.append("✔")
                detailed_results.append({"question": i+1, "status": "Correct", "student_answer": s, "correct_answer": c})
            else:
                comparison.append("✘")
                detailed_results.append({"question": i+1, "status": "Incorrect", "student_answer": s, "correct_answer": c})
        else:
            # Single correct answer
            if s == c:
                score += 1
                comparison.append("✔")
                detailed_results.append({"question": i+1, "status": "Correct", "student_answer": s, "correct_answer": c})
            else:
                comparison.append("✘")
                detailed_results.append({"question": i+1, "status": "Incorrect", "student_answer": s, "correct_answer": c})
    
    return score, comparison, detailed_results

def save_results(results, output_path="results.csv"):
    """
    Save results to CSV with more detailed information
    """
    df = pd.DataFrame(results)
    df.to_csv(output_path, index=False)
    return df