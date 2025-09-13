import pdfplumber

def parse_pdf(pdf_path: str) -> list[dict]:
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text()

            lines = text.splitlines()
            transactions = []
            transaction = {}
            for line in lines:
                parts = line.split()
                if len(parts) > 3 and any(char.isdigit() for char in parts[0]):
                    if transaction:
                        transactions.append(transaction)
                    transaction = {}
                    try:
                        transaction['Date'] = parts[0] + " " + parts[1]
                        description_start = 2
                        if parts[2].lower() in ['dr', 'cr']:
                            description_start = 3
                        transaction['Description'] = " ".join(parts[description_start:-2])
                        if parts[-2].lower() == 'dr':
                            transaction['Debit Amt'] = parts[-1]
                            transaction['Credit Amt'] = ""
                        elif parts[-2].lower() == 'cr':
                            transaction['Credit Amt'] = parts[-1]
                            transaction['Debit Amt'] = ""
                        else:
                            transaction['Debit Amt'] = ""
                            transaction['Credit Amt'] = ""
                        transaction['Balance'] = ""

                    except (IndexError, ValueError):
                        pass

            if transaction:
                transactions.append(transaction)
            return transactions
    except FileNotFoundError:
        return []
    except Exception as e:
        print(f"An error occurred: {e}")
        return []