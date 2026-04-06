"""
Import readers service — reads uploaded files into pandas DataFrames.
Wraps the existing file_reading.py logic for Django UploadedFile / FileField objects.
"""

import os
import pandas as pd


def read_upload_to_dataframe(file_obj):
    """
    Read an uploaded file (CSV or Excel) into a pandas DataFrame.

    Args:
        file_obj: A Django UploadedFile, FieldFile, or file path string.

    Returns:
        pd.DataFrame

    Raises:
        ValueError: If the file type is not supported.
    """
    # Get filename for extension detection
    if hasattr(file_obj, 'name'):
        filename = file_obj.name
    else:
        filename = str(file_obj)

    ext = os.path.splitext(filename)[1].lower()

    # Reset file pointer if it's a file-like object
    if hasattr(file_obj, 'seek'):
        file_obj.seek(0)

    if ext == '.csv':
        df = pd.read_csv(file_obj, dtype=str, keep_default_na=False)
    elif ext in ('.xlsx', '.xls'):
        df = pd.read_excel(file_obj, dtype=str, keep_default_na=False)
    else:
        raise ValueError(
            f"Tipo de archivo no soportado: '{ext}'. Solo se aceptan archivos CSV y Excel (.xlsx, .xls)."
        )

    return df


def extract_headers(df):
    """
    Extract column header names from a DataFrame.

    Args:
        df: pandas DataFrame

    Returns:
        list[str]: List of column header strings.
    """
    return [str(col).strip() for col in df.columns.tolist()]
