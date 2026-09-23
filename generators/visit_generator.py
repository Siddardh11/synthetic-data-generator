import json
import pandas as pd
from faker import Faker
import random


fake = Faker()


def generate_visits(
    schema_path,
    patient_df,
    hospital_df,
    department_df,
    doctor_df,
    config
):
    """
    Generate patient visits while maintaining valid
    patient, hospital, department and doctor relationships.
    """

    # --------------------------------
    # Read schema
    # --------------------------------

    with open(
        schema_path,
        "r",
        encoding="utf-8"
    ) as file:
        schema = json.load(file)

    # --------------------------------
    # Get number of visits
    # --------------------------------

    number_of_visits = config[
        "record_counts"
    ]["visits"]

    # --------------------------------
    # Prepare data
    # --------------------------------

    data = []

    visit_id = 1

    # --------------------------------
    # Generate visits
    # --------------------------------

    for _ in range(number_of_visits):

        # Select a patient
        patient_id = random.choice(
            patient_df["patient_id"].tolist()
        )

        # Select a hospital
        hospital_id = random.choice(
            hospital_df["hospital_id"].tolist()
        )

        # Get departments belonging to this hospital
        hospital_departments = department_df[
            department_df["hospital_id"] == hospital_id
        ]

        # Select a department
        department_id = random.choice(
            hospital_departments["department_id"].tolist()
        )

        # Get doctors belonging to this hospital AND department
        department_doctors = doctor_df[
            (doctor_df["hospital_id"] == hospital_id)
            &
            (doctor_df["department_id"] == department_id)
        ]

        # Select a doctor from that department
        doctor_id = random.choice(
            department_doctors["doctor_id"].tolist()
        )

        # Visit type
        visit_type = random.choice([
            "OP",
            "IP",
            "Emergency"
        ])

        # Visit status
        visit_status = random.choice([
            "Completed",
            "Cancelled"
        ])

        # Consultation fee
        consultation_fee = random.randint(
            500,
            2500
        )

        # Visit source
        source = random.choice([
            "Walk-in",
            "Appointment",
            "Referral"
        ])

        # Visit date
        visit_date = fake.date_between(
            start_date="-5y",
            end_date="today"
        )

        visit = {
            "visit_id": visit_id,
            "patient_id": patient_id,
            "hospital_id": hospital_id,
            "department_id": department_id,
            "doctor_id": doctor_id,
            "visit_date": visit_date,
            "visit_type": visit_type,
            "visit_status": visit_status,
            "consultation_fee": consultation_fee,
            "source": source
        }

        data.append(visit)

        visit_id += 1

    # --------------------------------
    # Convert to DataFrame
    # --------------------------------

    df = pd.DataFrame(data)

    # --------------------------------
    # Keep schema column order
    # --------------------------------

    column_order = [
        column["name"]
        for column in schema["columns"]
    ]

    df = df[column_order]

    return df