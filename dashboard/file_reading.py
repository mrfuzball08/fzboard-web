from string import printable

import pandas as pd


def read_file_to_dataframe(uploaded_file_path):
    """
    Read a file (CSV or Excel) and convert it to a pandas DataFrame.

    Args:
        uploaded_file_path (str): Path to the file

    Returns:
        pd.DataFrame: The file contents as a DataFrame

    Raises:
        ValueError: If file type is not supported
        Exception: If there's an error reading the file
    """
    try:
        if uploaded_file_path.endswith(".csv"):
            df = pd.read_csv(uploaded_file_path)
        elif uploaded_file_path.endswith((".xlsx", ".xls")):
            df = pd.read_excel(uploaded_file_path)
        else:
            raise ValueError(
                f"Unsupported file type. Only CSV and Excel files are supported."
            )
        return df
    except Exception as e:
        raise Exception(f"Error reading file {uploaded_file_path}: {str(e)}")
