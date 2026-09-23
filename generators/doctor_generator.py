import json
import pandas as pd
from faker import Faker
import random

fake = Faker()


def generate_doctors(
    schema_path,
    hospital_df,
    department_df,
    config
):

    with open(schema_path, "r", encoding="utf-8") as file:
        schema = json.load(file)

    doctors_per_hospital = config[
        "record_counts"
    ]["doctors_per_hospital"]

    data = []

    doctor_id = 1

    for hospital_id in hospital_df["hospital_id"]:

        hospital_departments = department_df[
            department_df["hospital_id"] == hospital_id
        ]

        department_ids = (
            hospital_departments[
                "department_id"
            ]
            .tolist()
        )

        # --------------------------------
        # Make sure there are enough doctors
        # to give every department at least
        # one doctor.
        # --------------------------------

        if doctors_per_hospital < len(
            department_ids
        ):

            raise ValueError(
                f"Hospital {hospital_id} has "
                f"{len(department_ids)} departments "
                f"but only "
                f"{doctors_per_hospital} doctors "
                f"were requested."
            )

        # --------------------------------
        # First assign one doctor to every
        # department.
        # --------------------------------

        assigned_departments = (
            department_ids.copy()
        )

        # --------------------------------
        # Assign remaining doctors randomly.
        # --------------------------------

        remaining_doctors = (
            doctors_per_hospital
            - len(department_ids)
        )

        assigned_departments.extend(
            random.choices(
                department_ids,
                k=remaining_doctors
            )
        )

        # --------------------------------
        # Generate doctors
        # --------------------------------

        for department_id in assigned_departments:

            department_name = (
                hospital_departments.loc[
                    hospital_departments[
                        "department_id"
                    ] == department_id,
                    "department_name"
                ]
                .iloc[0]
            )

            doctor = {
                "doctor_id": doctor_id,
                "doctor_name": fake.name(),
                "hospital_id": hospital_id,
                "department_id": department_id,
                "specialization": department_name,
                "experience_years": random.randint(
                    2,
                    30
                ),
                "consultation_fee": random.randint(
                    500,
                    2500
                ),
                "joining_date": fake.date_between(
                    start_date="-10y",
                    end_date="today"
                )
            }

            data.append(doctor)

            doctor_id += 1

    df = pd.DataFrame(data)

    column_order = [
        column["name"]
        for column in schema["columns"]
    ]

    return df[column_order]