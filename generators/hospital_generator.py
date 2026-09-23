import json
import pandas as pd


def generate_hospitals(schema_path):
    """
    Generate hospital master data from the hospital schema.
    """

    # Read schema
    with open(schema_path, "r", encoding="utf-8") as file:
        schema = json.load(file)

    # Get records from schema
    records = schema["records"]

    # Convert records into DataFrame
    df = pd.DataFrame(records)

    # Keep columns in schema-defined order
    column_order = [
        column["name"]
        for column in schema["columns"]
    ]

    df = df[column_order]

    return df
