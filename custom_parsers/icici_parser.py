import pdfplumber

def parse_pdf(pdf_path: str) -> list[dict]:
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text()

            lines = text.split('\n')
            transactions = []
            started = False
            for line in lines:
                line = line.strip()
                if "Date" in line and "Description" in line and "Debit Amt" in line and "Credit Amt" in line and "Balance" in line:
                    started = True
                    continue
                if started and line:
                    parts = line.split()
                    if len(parts) >= 5:
                        date_str = " ".join(parts[:2])
                        description = " ".join(parts[2:-3])
                        debit = parts[-3] if parts[-3].replace(".","").isdigit() else ""
                        credit = parts[-2] if parts[-2].replace(".","").isdigit() else ""
                        balance = parts[-1]
                        transactions.append({
                            'Date': date_str,
                            'Description': description,
                            'Debit Amt': debit,
                            'Credit Amt': credit,
                            'Balance': balance
                        })

            return transactions
    except FileNotFoundError:
        return []
    except Exception as e:
        print(f"An error occurred: {e}")
        return []