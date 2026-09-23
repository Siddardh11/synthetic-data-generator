import json
import pandas as pd


def generate_departments(
    schema_path,
    hospital_df,
    config
):
    """
    Generate departments for each hospital.
    """

    # Read department schema
    with open(schema_path, "r", encoding="utf-8") as file:
        schema = json.load(file)

    # Get department list from schema
    department_names = schema["departments"]

    # Get desired number of departments per hospital
    departments_per_hospital = config["record_counts"]["departments_per_hospital"]

    # Make sure requested number does not exceed available departments
    if departments_per_hospital > len(department_names):
        raise ValueError(
            f"Requested {departments_per_hospital} departments per hospital, "
            f"but only {len(department_names)} departments are defined in the schema."
        )

    data = []

    department_id = 1

    # Generate departments for every hospital
    for hospital_id in hospital_df["hospital_id"]:

        # Select required number of departments
        selected_departments = department_names[
            :departments_per_hospital
        ]

        for department_name in selected_departments:

            department = {
                "department_id": department_id,
                "department_name": department_name,
                "hospital_id": hospital_id
            }

            data.append(department)

            department_id += 1

    return pd.DataFrame(data)