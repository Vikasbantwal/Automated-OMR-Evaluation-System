import streamlit as st
import os
import pandas as pd
from omr_processing import preprocess_image, detect_bubbles, sort_bubbles, get_filled_answers
from grading_utils import load_answer_key, grade_sheet, save_results

# Define the base directory for the application
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")

def main():
    st.title("Automated OMR Evaluation System")
    
    # Create upload folder if not exists using absolute path
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    # Upload Answer Key
    answer_file = st.file_uploader("Upload Answer Key (Excel)", type=['xlsx'])
    correct_answers = []
    
    if answer_file:
        answer_path = os.path.join(UPLOAD_DIR, "answer_key.xlsx")
        with open(answer_path, "wb") as f:
            f.write(answer_file.getbuffer())
        
        if os.path.exists(answer_path):
            try:
                correct_answers = load_answer_key(answer_path)
                st.success(f"✅ Answer Key Detected: {len(correct_answers)} questions")
                
                st.write("First 10 answers:", [f"{i+1}-{['a','b','c','d'][ans] if isinstance(ans, int) and 0<=ans<4 else str(ans)}" 
                                              for i, ans in enumerate(correct_answers[:10])])
            except Exception as e:
                st.error(f"Error loading answer key: {str(e)}")
        else:
            st.error("Answer key file was not saved correctly.")
    
    # Upload Student OMR Sheets
    sheet_files = st.file_uploader(
        "Upload OMR Sheets (Multiple allowed)",
        type=['jpg', 'jpeg', 'png'],
        accept_multiple_files=True
    )
    
    if sheet_files and correct_answers:
        results = []
        all_detailed_results = []
        
        for i, sheet in enumerate(sheet_files):
            sheet_path = os.path.join(UPLOAD_DIR, f"sheet_{i+1}.jpg")
            with open(sheet_path, "wb") as f:
                f.write(sheet.getbuffer())
            
            try:
                thresh = preprocess_image(sheet_path)
                bubbles = detect_bubbles(thresh)
                
                if not bubbles:
                    st.error(f"No bubbles detected in {sheet.name}. Check image quality.")
                    continue
                
                sorted_bubbles = sort_bubbles(bubbles)
                student_answers = get_filled_answers(thresh, sorted_bubbles)
                
                if len(student_answers) > 100:
                    student_answers = student_answers[:100]
                elif len(student_answers) < 100:
                    student_answers.extend([-1] * (100 - len(student_answers)))
                
                score, comparison, detailed_results = grade_sheet(student_answers, correct_answers)
                
                results.append({
                    'Sheet Name': sheet.name,
                    'Score': score,
                    'Total Questions': len(correct_answers),
                    'Percentage': round(score / len(correct_answers) * 100, 2) if len(correct_answers) > 0 else 0
                })
                
                all_detailed_results.append({
                    'sheet_name': sheet.name,
                    'detailed_results': detailed_results
                })
                
                st.write(f"Processed {sheet.name}: Score = {score}/{len(correct_answers)}")
                
                st.write("First 10 answers comparison:")
                comp_df = pd.DataFrame(detailed_results[:10])
                st.dataframe(comp_df)
                
            except Exception as e:
                st.error(f"Error processing {sheet.name}: {str(e)}")
        
        if results:
            st.subheader("📊 Results Summary")
            df_results = pd.DataFrame(results)
            st.dataframe(df_results)
            
            st.subheader("Detailed Results")
            for detailed in all_detailed_results:
                with st.expander(f"Detailed results for {detailed['sheet_name']}"):
                    st.write(pd.DataFrame(detailed['detailed_results']))
            
            output_path = os.path.join(BASE_DIR, "results.csv")
            df_results.to_csv(output_path, index=False)
            
            with open(output_path, "rb") as f:
                st.download_button(
                    label="Download Results CSV",
                    data=f,
                    file_name="omr_results.csv",
                    mime="text/csv"
                )

if __name__ == "__main__":
    main()