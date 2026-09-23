import json
import pandas as pd
from faker import Faker
import random


fake = Faker()


def generate_doctors(schema_path, hospital_df, department_df):

    # Read schema
    with open(schema_path, "r", encoding="utf-8") as file:
        schema = json.load(file)

    doctors_per_hospital = schema["doctors_per_hospital"]

    data = []

    doctor_id = 1

    # Generate doctors hospital by hospital
    for hospital_id in hospital_df["hospital_id"]:

        # Get departments belonging to this hospital
        hospital_departments = department_df[
            department_df["hospital_id"] == hospital_id
        ]

        department_ids = hospital_departments["department_id"].tolist()

        # Generate doctors
        for _ in range(doctors_per_hospital):

            # Select a department ONLY from this hospital
            department_id = random.choice(department_ids)

            # Get department name
            department_name = hospital_departments.loc[
                hospital_departments["department_id"] == department_id,
                "department_name"
            ].iloc[0]

            doctor = {
                "doctor_id": doctor_id,
                "doctor_name": fake.name(),
                "hospital_id": hospital_id,
                "department_id": department_id,
                "specialization": department_name,
                "experience_years": random.randint(2, 30),
                "consultation_fee": random.randint(500, 2500),
                "joining_date": fake.date_between(
                    start_date="-10y",
                    end_date="today"
                )
            }

            data.append(doctor)

            doctor_id += 1

    return pd.DataFrame(data)