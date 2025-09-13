import pandas as pd
from pdfplumber import pdf2calc

def extract_table(page):
    tables = page.extract_tables()
    if tables:
        return tables[0]
    else:
        return None

def extract_values(row):
    return row if len(row) >= 6 else ['', '', '', '']

def parse(pdf_path: str) -> pd.DataFrame:
    with pdfplumber.open(pdf_path) as pdf:
        pages = list(pdf.pages)
        if not pages:
            return pd.DataFrame(columns=['Date', 'Description', 'Debit Amt', 'Credit Amt', 'Balance'])
        
        table = extract_table(pages[0])
        if table is not None:
            table = table[1:]
            extracted_table = [extract_values(row) for row in table]
            df = pd.DataFrame(extracted_table, columns=['Date', 'Description', 'Debit Amt', 'Credit Amt', 'Balance'])
            df['Date'] = df['Date'].fillna("")
            df['Description'] = df['Description'].fillna("")
            df['Debit Amt'] = df['Debit Amt'].fillna("")
            df['Credit Amt'] = df['Credit Amt'].fillna("")
            df['Balance'] = df['Balance'].fillna("")
            return df
        else:
            return pd.DataFrame(columns=['Date', 'Description', 'Debit Amt', 'Credit Amt', 'Balance'])