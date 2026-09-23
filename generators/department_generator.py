import json
import pandas as pd


def generate_doctors(schema_path,hospital_df,department_df,config):
    """
    Generate departments for each hospital.
    """

    # Read department schema
    with open(schema_path, "r", encoding="utf-8") as file:
        schema = json.load(file)

    department_names = schema["departments"]

    data = []

    department_id = 1

    # Create departments for every hospital
    for hospital_id in hospital_df["hospital_id"]:

        for department_name in department_names:

            department = {
                "department_id": department_id,
                "department_name": department_name,
                "hospital_id": hospital_id
            }

            data.append(department)

            department_id += 1

    return pd.DataFrame(data)