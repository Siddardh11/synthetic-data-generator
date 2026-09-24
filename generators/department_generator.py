import json
import pandas as pd

from utils.id_generator import generate_id


def generate_departments(
    schema_path,
    hospital_df,
    config
):
    """
    Generate department master data.

    Departments are distributed evenly across hospitals.
    Department IDs are generated using the centralized
    six-character ID generator.
    """

    # ========================================
    # Read department schema
    # ========================================

    with open(
        schema_path,
        "r",
        encoding="utf-8"
    ) as file:
        schema = json.load(file)

    # ========================================
    # Get required department count
    # ========================================

    number_of_departments = config[
        "record_counts"
    ]["departments"]

    # ========================================
    # Validate hospital data
    # ========================================

    if hospital_df.empty:
        raise ValueError(
            "Hospital DataFrame is empty."
        )

    number_of_hospitals = len(hospital_df)

    # ========================================
    # Validate department count
    # ========================================

    if number_of_departments % number_of_hospitals != 0:

        raise ValueError(
            "Department count must be evenly "
            "divisible by the number of hospitals."
        )

    departments_per_hospital = (
        number_of_departments
        // number_of_hospitals
    )

    # ========================================
    # Read department definitions
    # ========================================

    department_records = schema.get(
        "departments",
        schema.get("records", [])
    )

    if not department_records:
        raise ValueError(
            "No department definitions found "
            "in department schema."
        )

    # ========================================
    # Validate enough department definitions
    # ========================================

    if len(department_records) < departments_per_hospital:

        raise ValueError(
            f"Department schema contains only "
            f"{len(department_records)} definitions, "
            f"but {departments_per_hospital} are required "
            f"per hospital."
        )

    # ========================================
    # Select department names
    # ========================================

    department_names = []

    for record in department_records:

        if isinstance(record, dict):

            department_name = record.get(
                "department_name"
            )

        else:

            department_name = record

        if department_name:
            department_names.append(
                department_name
            )

    # ========================================
    # Remove duplicate department names
    # ========================================

    department_names = list(
        dict.fromkeys(department_names)
    )

    # ========================================
    # Validate department definitions
    # ========================================

    if len(department_names) < departments_per_hospital:

        raise ValueError(
            "Not enough unique department names "
            "available in the schema."
        )

    # ========================================
    # Generate departments
    # ========================================

    data = []

    for _, hospital in hospital_df.iterrows():

        hospital_id = hospital[
            "hospital_id"
        ]

        # ------------------------------------
        # Give every hospital the same
        # department set.
        # ------------------------------------

        selected_departments = department_names[
            :departments_per_hospital
        ]

        for department_name in selected_departments:

            department_id = generate_id(
                "department"
            )

            data.append({
                "department_id": department_id,
                "department_name": department_name,
                "hospital_id": hospital_id
            })

    # ========================================
    # Create DataFrame
    # ========================================

    department_df = pd.DataFrame(
        data,
        columns=[
            "department_id",
            "department_name",
            "hospital_id"
        ]
    )

    # ========================================
    # Validate record count
    # ========================================

    if len(department_df) != number_of_departments:

        raise ValueError(
            f"Expected {number_of_departments} "
            f"departments but generated "
            f"{len(department_df)}."
        )

    # ========================================
    # Validate department IDs
    # ========================================

    if department_df[
        "department_id"
    ].duplicated().any():

        raise ValueError(
            "Duplicate department IDs generated."
        )

    # ========================================
    # Validate hospital relationships
    # ========================================

    valid_hospital_ids = set(
        hospital_df["hospital_id"]
    )

    invalid_hospital_ids = set(
        department_df["hospital_id"]
    ) - valid_hospital_ids

    if invalid_hospital_ids:

        raise ValueError(
            "Departments reference unknown "
            f"hospital IDs: {invalid_hospital_ids}"
        )

    # ========================================
    # Validate distribution
    # ========================================

    department_counts = (
        department_df
        .groupby("hospital_id")
        .size()
    )

    invalid_distribution = (
        department_counts
        != departments_per_hospital
    ).any()

    if invalid_distribution:

        raise ValueError(
            "Departments were not distributed "
            "evenly across hospitals."
        )

    # ========================================
    # Return
    # ========================================

    return department_df