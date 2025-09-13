# tests/test_parser_contract.py
import importlib
import pathlib
import pandas as pd
import pytest

DATA_DIR = pathlib.Path("data")

@pytest.mark.parametrize("bank", [p.name for p in DATA_DIR.iterdir() if p.is_dir()])
def test_contract(bank):
    """
    Contract Test:
    - Each parser must define parse(pdf_path) -> pd.DataFrame
    - Output DataFrame must equal the CSV ground truth
    """

    parser_module = importlib.import_module(f"custom_parsers.{bank}_parser")

    # Must have a parse function
    assert hasattr(parser_module, "parse"), f"{bank}_parser.py missing parse()"

    pdf_path = DATA_DIR / bank / f"{bank}_sample.pdf"
    csv_path = DATA_DIR / bank / f"{bank}_sample.csv"

    # Load expected CSV
    expected_df = pd.read_csv(csv_path)

    # Run the parser
    parsed_df = parser_module.parse(str(pdf_path))

    # Ensure DataFrame type
    assert isinstance(parsed_df, pd.DataFrame), "parse() must return a pandas DataFrame"

    # Ensure schema match
    assert list(parsed_df.columns) == list(expected_df.columns), \
        "Parsed DataFrame columns do not match expected CSV"

    # Normalize index before comparison
    expected_df = expected_df.reset_index(drop=True)
    parsed_df = parsed_df.reset_index(drop=True)

    # Contract: exact equality
    assert parsed_df.equals(expected_df), f"{bank} parser output does not match expected CSV"
