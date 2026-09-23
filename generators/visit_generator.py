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
    Generate synthetic patient visits while maintaining
    valid patient, hospital, department and doctor relationships.
    """

    # --------------------------------
    # Read visit schema
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

    data = []

    visit_id = 1

    # --------------------------------
    # Prepare patient records
    # --------------------------------

    patient_records = patient_df[
        [
            "patient_id",
            "registration_date"
        ]
    ].to_dict("records")

    # --------------------------------
    # Prepare doctor records
    # --------------------------------

    doctor_records = doctor_df[
        [
            "doctor_id",
            "hospital_id",
            "department_id"
        ]
    ].to_dict("records")

    # --------------------------------
    # Generate visits
    # --------------------------------

    for _ in range(number_of_visits):

        # --------------------------------
        # Select a patient
        # --------------------------------

        patient = random.choice(
            patient_records
        )

        patient_id = patient["patient_id"]

        registration_date = patient[
            "registration_date"
        ]

        # --------------------------------
        # Select a doctor
        # --------------------------------

        doctor = random.choice(
            doctor_records
        )

        doctor_id = doctor["doctor_id"]

        hospital_id = doctor["hospital_id"]

        department_id = doctor["department_id"]

        # --------------------------------
        # Generate visit date
        # Visit cannot happen before
        # patient registration
        # --------------------------------

        visit_date = fake.date_between(
            start_date=registration_date,
            end_date="today"
        )

        # --------------------------------
        # Visit type
        # --------------------------------

        visit_type = random.choice([
            "OP",
            "IP",
            "Emergency"
        ])

        # --------------------------------
        # Visit status
        # --------------------------------

        visit_status = random.choice([
            "Completed",
            "Cancelled"
        ])

        # --------------------------------
        # Consultation fee
        # --------------------------------

        consultation_fee = random.randint(
            500,
            2500
        )

        # --------------------------------
        # Visit source
        # --------------------------------

        source = random.choice([
            "Walk-in",
            "Appointment",
            "Referral"
        ])

        # --------------------------------
        # Create visit record
        # --------------------------------

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
    # Keep schema-defined column order
    # --------------------------------

    column_order = [
        column["name"]
        for column in schema["columns"]
    ]

    df = df[column_order]

    return df