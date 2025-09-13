import pandas as pd
import pdfplumber

def parse(pdf_path: str) -> pd.DataFrame:
    # Initialize lists to store data
    dates = []
    descriptions = []
    debit_amounts = []
    credit_amounts = []
    balances = []

    # Read the PDF
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            # Get text from the page
            text = page.extract_text()

            # Split the text into lines
            lines = text.split('\n')

            # Iterate over the lines
            for line in lines:
                # Split the line into parts
                parts = line.strip().split()

                # Check if the line contains a date
                if len(parts) > 3 and parts[0].isdigit():
                    # Extract the date
                    date = ' '.join(parts[:3])

                    # Extract the description
                    description = ' '.join(parts[3:])

                    # Extract the debit amount
                    debit_amount = ""
                    for word in parts:
                        if word.replace('.','',1).replace('-','',1).isdigit():
                            debit_amount += word + ' '

                    # Extract the credit amount
                    credit_amount = ""
                    for word in parts:
                        if word.replace('.','',1).replace('-','',1).isdigit() and debit_amount == "":
                            credit_amount += word + ' '

                    # Extract the balance
                    balance = ""
                    for word in parts:
                        if word.replace('.','',1).replace('-','',1).isdigit() and credit_amount == "":
                            balance += word + ' '

                    # Add the data to the lists
                    dates.append(date)
                    descriptions.append(description.strip())
                    debit_amounts.append(debit_amount.strip())
                    credit_amounts.append(credit_amount.strip())
                    balances.append(balance.strip())

    # Create the DataFrame
    df = pd.DataFrame({
        'Date': dates,
        'Description': descriptions,
        'Debit Amt': debit_amounts,
        'Credit Amt': credit_amounts,
        'Balance': balances
    })

    # Fill missing values with ""
    df = df.fillna('')

    return df