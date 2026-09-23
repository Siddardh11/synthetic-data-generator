import json
import pandas as pd
from faker import Faker
import random
from datetime import date


fake = Faker()


def calculate_age(date_of_birth):
    """
    Calculate current age from date of birth.
    """

    today = date.today()

    age = today.year - date_of_birth.year

    if (
        today.month,
        today.day
    ) < (
        date_of_birth.month,
        date_of_birth.day
    ):
        age -= 1

    return age


def generate_patients(schema_path, config):
    """
    Generate synthetic patient master data.
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
    # Get number of patients
    # --------------------------------

    number_of_patients = config[
        "record_counts"
    ]["patients"]


    # --------------------------------
    # Generate patients
    # --------------------------------

    data = []

    for patient_id in range(
        1,
        number_of_patients + 1
    ):

        # Generate date of birth
        date_of_birth = fake.date_of_birth(
            minimum_age=1,
            maximum_age=90
        )

        # Calculate age from DOB
        age = calculate_age(
            date_of_birth
        )

        # Generate patient
        patient = {

            "patient_id": patient_id,

            "patient_name": fake.name(),

            "gender": random.choice([
                "Male",
                "Female"
            ]),

            "date_of_birth": date_of_birth,

            "age": age,

            "city": fake.city(),

            "registration_date": fake.date_between(
                start_date="-5y",
                end_date="today"
            ),

            "insurance_type": random.choice([
                "Insurance",
                "Self Pay",
                "Corporate"
            ])
        }

        data.append(patient)


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