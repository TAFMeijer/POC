import os
import re
import glob
from dotenv import load_dotenv

# Load config similar to main.py
load_dotenv()
PDF_FOLDER = "/Volumes/path/Admin/Bekeuringen/" 

def determine_prompt_type(filename):
    # Pattern A: Ends in 8 digits
    if re.search(r'(?<!\d)\d{8}\.pdf$', filename):
        return 'type_a'
    
    # Pattern B: Ends in 10 digits
    if re.search(r'(?<!\d)\d{10}\.pdf$', filename):
        return 'type_b'
    
    # Pattern C: Ends in 16 digits
    if re.search(r'(?<!\d)\d{4} \d{4} \d{4} \d{4}\.pdf$', filename):
        return 'type_c'
    
    return None

def audit_files():
    if not os.path.exists(PDF_FOLDER):
        print(f"Error: Folder {PDF_FOLDER} not found.")
        return

    pdf_files = glob.glob(os.path.join(PDF_FOLDER, "*.pdf"))
    print(f"Scanning {len(pdf_files)} files in {PDF_FOLDER}...")

    unmatched = []
    matched = 0

    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        prompt_type = determine_prompt_type(filename)
        
        if prompt_type:
            matched += 1
        else:
            unmatched.append(filename)

    print(f"\nSummary:")
    print(f"Matched:  {matched}")
    print(f"Unmatched: {len(unmatched)}")
    
    if unmatched:
        print("\n--- Unmatched Files (These were skipped) ---")
        for f in unmatched:
            print(f)
    else:
        print("\nAll files matched a pattern! If files are missing, checks 'skipped_files.json' for processing errors.")

if __name__ == "__main__":
    audit_files()
