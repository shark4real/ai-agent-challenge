import pandas as pd
import numpy as np
from PyPDF2 import PdfReader, PdfReadError
import os

def parse(pdf_path: str) -> pd.DataFrame:
    """
    This function reads a PDF file, extracts text from each page, and converts it into a DataFrame.
    
    Args:
    pdf_path (str): The path to the PDF file.
    
    Returns:
    pd.DataFrame: A DataFrame containing the extracted text.
    """
    
    # Check if the file exists
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"The file {pdf_path} does not exist.")
    
    # Check if the file is a PDF
    if not pdf_path.endswith('.pdf'):
        raise ValueError(f"The file {pdf_path} is not a PDF.")
    
    try:
        # Read the PDF file
        reader = PdfReader(pdf_path)
        
        # Initialize an empty list to store the text from each page
        text_from_pages = []
        
        # Iterate through each page in the PDF
        for page in reader.pages:
            # Extract the text from the page
            text_from_pages.append(page.extract_text())
        
        # Join all the text from each page into a single string
        text = ' '.join(text_from_pages)
        
        # Convert the text to a DataFrame
        df = pd.DataFrame({
            'Date': [],
            'Description': [],
            'Debit Amt': [],
            'Credit Amt': [],
            'Balance': []
        })
        
        # Initialize the previous balance
        previous_balance = None
        
        # Iterate through each row in the DataFrame
        for index, row in df.iterrows():
            # If this is the first row, set the previous balance to the current balance
            if previous_balance is None:
                previous_balance = 0  # Initialize with 0 instead of None
            
            # Determine if this is a debit or credit
            if 'Balance' in df.columns:  # Check if the 'Balance' column exists
                if df.loc[index, 'Balance'] < previous_balance:
                    df.loc[index, 'Debit Amt'] = df.loc[index, 'Balance'] - previous_balance
                    df.loc[index, 'Credit Amt'] = np.nan
                elif df.loc[index, 'Balance'] > previous_balance:
                    df.loc[index, 'Credit Amt'] = df.loc[index, 'Balance'] - previous_balance
                    df.loc[index, 'Debit Amt'] = np.nan
                else:
                    df.loc[index, 'Debit Amt'] = np.nan
                    df.loc[index, 'Credit Amt'] = np.nan
            else:
                print("The 'Balance' column does not exist in the DataFrame.")
            
            # Update the previous balance
            previous_balance = df.loc[index, 'Balance'] if 'Balance' in df.columns else previous_balance
        
        # Return the DataFrame
        return df
    
    except PdfReadError as e:
        print(f"An error occurred while reading the PDF: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

# Example usage
pdf_path = 'path_to_your_pdf_file.pdf'
df = parse(pdf_path)
if df is not None:
    print(df)