import os
import re
import json
import glob
import pandas as pd
import google.generativeai as genai
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

# Configuration
API_KEY = os.getenv("GEMINI_API_KEY")
PROCESSED_LOG_FILE = "processed_files.json"
FAILED_LOG_FILE = "skipped_files.json"
EXCEL_OUTPUT_FILE = "output.xlsx"
PDF_FOLDER = "/Volumes/path/Admin/Bekeuringen/"  # Current directory, or change to specific path

# Configure Gemini
if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    print("WARNING: GEMINI_API_KEY not found in environment variables.")

# Placeholder Prompts (to be updated by user later)
PROMPT_8_DIGITS = "Return four data points (1) the amount right next to 'Te betalen', which is writen in Dutch format €##0,#0 so please transform it to a number #,##0.00 and (2) the date right next to 'Betalen vóór' written in dutch date format dd mmmm yyyy, please transform to English dd-mmm-yy and (3) the 8 digit number right next to 'Vorderingsnummer' formatted as ########, and please maintain that formatting and (4) if says in bold on the top of the letter 'Gemeente Amsterdam' return 'Gemeente Amsterdam belastingen', otherwise return 'issue'. Now return, the four values as such: amount; date; 8 digit number; type."
PROMPT_10_DIGITS = "Return four data points (1) the amount below 'totaal te betalen', which is writen in Dutch format €##0,#0 so please transform it to a number #,##0.00 and (2) the date below 'uiterste betaaldatum' written in dutch date format dd mmmm yyyy, please transform to English dd-mmm-yy and (3) the 10 digit number below 'vorderingsnummer (bij correspondentie vermelden)' formatted as ##########, and please maintain that formatting and (4) if says in bold on the top of the letter 'Gemeente Rotterdam' return 'Gemeente Rotterdam belastingen', otherwise return 'issue'. Now return, the four values as such: amount; date; 10 digit number; type."
PROMPT_16_DIGITS = "Return four data points (1) the amount just below 'Door u te betalen', which is writen in Dutch format €##0,#0 so please transform it to a number #,##0.00 and (2) the date just below 'Betaal vóór' written in dutch date format dd mmmm yyyy, please transform to English dd-mmm-yy and (3) the 16 digit number either below 'Tolnummer' or 'met betalingskenmerk' formatted as #### #### #### ####, and please maintain that formatting and (4) if it says 'Tolnummer' return 'CJIB Tolherinnering' otherwise return 'CJIB Verkeersboetes'. Now return, the four values as such: amount; date; 16 digit number; type."



def load_file_set(json_file):
    """Loads a set of filenames from a JSON file."""
    if os.path.exists(json_file):
        try:
            with open(json_file, 'r') as f:
                return set(json.load(f))
        except json.JSONDecodeError:
            return set()
    return set()

def save_file_set(json_file, file_set):
    """Saves a set of filenames to a JSON file."""
    with open(json_file, 'w') as f:
        json.dump(list(file_set), f, indent=4)

def determine_prompt_type(filename):
    """
    Determines the prompt type based on the filename pattern.
    Returns 'type_a' for 8 digits, 'type_b' for 10 digits, 'type_c' for 16 digits format, or None.
    """
    # Pattern A: Ends in 8 digits (e.g., file12345678.pdf) - ensure not part of a longer number
    if re.search(r'(?<!\d)\d{8}\.pdf$', filename):
        return 'type_a'
    
    # Pattern B: Ends in 10 digits (e.g., file1234567890.pdf) - ensure not part of a longer number
    if re.search(r'(?<!\d)\d{10}\.pdf$', filename):
        return 'type_b'
    
    # Pattern C: Ends in 16 digits formatted like "#### #### #### ####"
    if re.search(r'(?<!\d)\d{4} \d{4} \d{4} \d{4}\.pdf$', filename):
        return 'type_c'
    
    return None

def process_pdf_with_gemini(file_path, prompt):
    """
    Sends the PDF to Gemini API with the given prompt.
    Returns the text response.
    """
    if not API_KEY:
        return "Error: API Key missing"

    try:
        model = genai.GenerativeModel('gemini-3-flash-preview') # Using Gemini 3.0 Flash (vision capable)
        
        # Upload the file
        print(f"Uploading {file_path}...")
        sample_file = genai.upload_file(path=file_path, display_name=os.path.basename(file_path))
        
        print(f"Generating content for {os.path.basename(file_path)}...")
        response = model.generate_content([sample_file, prompt])
        
        return response.text
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None

def append_to_excel(data_dict):
    """Appends a dictionary of data as a new row in the Excel file."""
    df_new = pd.DataFrame([data_dict])
    
    if os.path.exists(EXCEL_OUTPUT_FILE):
        try:
            # Simple Read-Concat-Write approach to avoid file locking/buffering issues
            df_existing = pd.read_excel(EXCEL_OUTPUT_FILE)
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
            df_combined.to_excel(EXCEL_OUTPUT_FILE, index=False)
            print(f"DEBUG: Appended to {EXCEL_OUTPUT_FILE}, total rows: {len(df_combined)}")
        except PermissionError:
            print(f"CRITICAL ERROR: {EXCEL_OUTPUT_FILE} is open or locked. Please close the file and run again.")
            raise  # Stop execution immediately
        except Exception as e:
            print(f"CRITICAL ERROR updating Excel: {e}")
            raise  # Stop execution immediately
    else:
        df_new.to_excel(EXCEL_OUTPUT_FILE, index=False)
        print(f"DEBUG: Created {EXCEL_OUTPUT_FILE}")

def scan_and_process():
    """Main function to scan folder and process new PDFs."""
    processed_files = load_file_set(PROCESSED_LOG_FILE)
    skipped_files = load_file_set(FAILED_LOG_FILE) # Load failed/skipped files
    
    if not os.path.exists(PDF_FOLDER):
        print(f"Error: Folder {PDF_FOLDER} not found.")
        return

    pdf_files = glob.glob(os.path.join(PDF_FOLDER, "*.pdf"))
    
    print(f"Found {len(pdf_files)} PDF files.")
    
    processed_count = 0
    BATCH_LIMIT = 50
    
    for pdf_path in pdf_files:
        if processed_count >= BATCH_LIMIT:
            print(f"Batch limit of {BATCH_LIMIT} reached. Stopping for inspection.")
            break

        filename = os.path.basename(pdf_path)
        
        # Skip if already successfully processed
        if filename in processed_files:
            print(f"Skipping already processed: {filename}")
            continue
            
        prompt_type = determine_prompt_type(filename)
        
        if not prompt_type:
            print(f"Skipping {filename}: Pattern not matched.")
            continue
            
        prompt = PROMPT_8_DIGITS if prompt_type == 'type_a' else PROMPT_10_DIGITS if prompt_type == 'type_b' else PROMPT_16_DIGITS if prompt_type == 'type_c' else None
        print(f"Processing {filename} as {prompt_type}...")
        
        # Call Gemini
        result_text = process_pdf_with_gemini(pdf_path, prompt) 
        
        success = False
        parts = []

        if result_text:
            try:
                # Split by semicolon and strip whitespace
                parts = [p.strip() for p in result_text.split(';')]
                
                # Check for Valid Parse (Success Criteria)
                if len(parts) >= 4:
                     success = True
                else:
                    print(f"Warning: Unexpected format (User Prompt Mismatch) for {filename}: {result_text}")
            except Exception as e:
                print(f"Error parsing response for {filename}: {e}")

        if success:
            amount = parts[0]
            date_val = parts[1]
            number = parts[2]
            type_val = parts[3]

            # Log to Excel
            row_data = {
                "Bedrag": amount,
                "Uiterste betaaldatum": date_val,
                "Betaalkenmerk": number,
                "Ter name van": type_val,
                "Bestandsnaam": filename,
                "Verwerkt op": pd.Timestamp.now().isoformat()
            }
            append_to_excel(row_data)
            
            # Mark as processed (Success)
            processed_files.add(filename)
            save_file_set(PROCESSED_LOG_FILE, processed_files)
            
            # If it was previously failed/skipped, remove it from that list
            if filename in skipped_files:
                skipped_files.remove(filename)
                save_file_set(FAILED_LOG_FILE, skipped_files)
                
            print(f"Finished {filename}: {amount} | {date_val} | {number} | {type_val}")
            processed_count += 1
            
        else:
            # Handle Failure
            print(f"FAILED to process {filename}. Adding to skipped list.")
            skipped_files.add(filename)
            save_file_set(FAILED_LOG_FILE, skipped_files)

if __name__ == "__main__":
    scan_and_process()
