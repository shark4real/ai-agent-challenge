# tests/test_parser_contract.py
"""
This test suite validates that all custom parsers adhere to a specific
contract, ensuring they are correctly implemented and produce valid output.
"""

import csv
import importlib
import pathlib
import pytest

# Define the root directory for test data samples.
SAMPLES_ROOT_DIR = pathlib.Path("data")

def find_available_parsers():
    """Dynamically finds all available bank parsers based on folder names in the data directory."""
    if not SAMPLES_ROOT_DIR.is_dir():
        return []
    return [p.name for p in SAMPLES_ROOT_DIR.iterdir() if p.is_dir()]

@pytest.fixture(scope="module", params=find_available_parsers())
def bank_identifier(request):
    """A pytest fixture to provide each bank identifier to the test class."""
    return request.param


class TestParserContract:
    """
    Validates the contract for each bank-specific parser.
    """

    def test_parser_structure_and_output(self, bank_identifier):
        """
        For each bank, this test ensures:
        1. The parser module exists and can be imported.
        2. It contains a callable 'parse_pdf' function.
        3. The function returns a non-empty list of dictionaries.
        4. The output is successfully written back to the sample CSV file.
        """
        # --- 1. Module and Function Validation ---
        try:
            module_name = f"custom_parsers.{bank_identifier}_parser"
            parser_module = importlib.import_module(module_name)
        except ImportError:
            pytest.fail(f"Could not import the parser module: '{module_name}.py'")

        assert hasattr(parser_module, "parse_pdf"), \
            f"The parser '{module_name}.py' must have a 'parse_pdf' function."
        
        parse_function = getattr(parser_module, "parse_pdf")
        assert callable(parse_function), "'parse_pdf' must be a callable function."

        # --- 2. Execution and Data Validation ---
        pdf_sample_path = SAMPLES_ROOT_DIR / bank_identifier / f"{bank_identifier}_sample.pdf"
        
        # Run the parser on the sample PDF
        parsed_data = parse_function(pdf_sample_path)

        # Validate the structure of the returned data
        assert isinstance(parsed_data, list), "The parse_pdf function must return a list."
        assert len(parsed_data) > 0, "The parser must extract at least one row of data."
        assert all(isinstance(item, dict) for item in parsed_data), \
            "All items in the returned list must be dictionaries."

        # --- 3. CSV Writing and Validation ---
        output_csv_path = SAMPLES_ROOT_DIR / bank_identifier / f"{bank_identifier}_sample.csv"
        
        try:
            # Get the headers from the first data row
            headers = parsed_data[0].keys()
            with open(output_csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                writer.writerows(parsed_data)
        except (IOError, IndexError) as e:
            pytest.fail(f"Failed to write output CSV for '{bank_identifier}': {e}")
        
        # Final check to ensure the file was written and is not empty
        assert output_csv_path.exists(), f"Output CSV file was not created at: {output_csv_path}"
        assert output_csv_path.stat().st_size > 0, "The generated CSV file is empty."