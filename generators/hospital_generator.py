import json
import pandas as pd

from utils.id_generator import generate_id


def generate_hospitals(schema_path):
    """
    Generate hospital master data from the hospital schema.

    Hospital locations and attributes are defined in the schema.
    Hospital IDs are generated using the centralized ID generator.
    """

    # ========================================
    # Read hospital schema
    # ========================================

    with open(
        schema_path,
        "r",
        encoding="utf-8"
    ) as file:
        schema = json.load(file)

    # ========================================
    # Read records from schema
    # ========================================

    records = schema.get("records", [])

    if not records:
        raise ValueError(
            "No hospital records found in hospital schema."
        )

    # ========================================
    # Generate hospital records
    # ========================================

    hospitals = []

    for record in records:

        hospital_id = generate_id("hospital")

        hospitals.append({
            "hospital_id": hospital_id,
            "hospital_name": record["hospital_name"],
            "city": record["city"],
            "state": record["state"],
            "hospital_type": record["hospital_type"],
            "bed_capacity": record["bed_capacity"]
        })

    # ========================================
    # Create DataFrame
    # ========================================

    hospital_df = pd.DataFrame(hospitals)

    # ========================================
    # Basic validation
    # ========================================

    if hospital_df["hospital_id"].duplicated().any():
        raise ValueError(
            "Duplicate hospital IDs generated."
        )

    if hospital_df["hospital_id"].isna().any():
        raise ValueError(
            "Hospital ID contains null values."
        )

    # ========================================
    # Return
    # ========================================

    return hospital_df