import json
import random
from datetime import date, datetime

import pandas as pd
from faker import Faker

from utils.id_generator import generate_id
from utils.location_data import INDIAN_CITIES


fake = Faker("en_IN")


def generate_patients(
    schema_path,
    config
):
    """
    Generate synthetic patient master data.

    Guarantees:
    - Configured number of patients is generated.
    - Patient IDs use the centralized six-character ID generator.
    - Date of birth is logically consistent with age.
    - Registration date falls inside the configured historical range.
    - Patient location is selected from predefined Indian
      city/state combinations.
    - Insurance type has realistic variation.
    """

    # ========================================
    # Read patient schema
    # ========================================

    with open(
        schema_path,
        "r",
        encoding="utf-8"
    ) as file:

        schema = json.load(file)

    # ========================================
    # Get patient count
    # ========================================

    number_of_patients = config[
        "record_counts"
    ]["patients"]

    # ========================================
    # Historical date range
    # ========================================

    historical_start = date.fromisoformat(
        config["date_range"]["start_date"]
    )

    historical_end = date.fromisoformat(
        config["date_range"]["end_date"]
    )

    # ========================================
    # Validate date range
    # ========================================

    if historical_start > historical_end:

        raise ValueError(
            "Patient historical start date "
            "cannot be after the end date."
        )

    # ========================================
    # Validate location data
    # ========================================

    if not INDIAN_CITIES:

        raise ValueError(
            "INDIAN_CITIES is empty."
        )

    # ========================================
    # Insurance distribution
    # ========================================

    insurance_types = [
        "Insurance",
        "Self Pay",
        "Corporate"
    ]

    insurance_weights = [
        0.50,
        0.35,
        0.15
    ]

    # ========================================
    # Gender distribution
    # ========================================

    genders = [
        "Male",
        "Female"
    ]

    gender_weights = [
        0.52,
        0.48
    ]

    # ========================================
    # Generate patients
    # ========================================

    patients = []

    for _ in range(number_of_patients):

        # ------------------------------------
        # Patient ID
        # ------------------------------------

        patient_id = generate_id(
            "patient"
        )

        # ------------------------------------
        # Patient name
        # ------------------------------------

        patient_name = fake.name()

        # ------------------------------------
        # Gender
        # ------------------------------------

        gender = random.choices(
            genders,
            weights=gender_weights,
            k=1
        )[0]

        # ------------------------------------
        # Date of birth
        # ------------------------------------

        # Keep the synthetic population mainly
        # between 1 and 90 years old.

        age = random.choices(
            population=[
                5,
                15,
                25,
                35,
                45,
                55,
                65,
                75,
                85
            ],
            weights=[
                0.04,
                0.08,
                0.16,
                0.17,
                0.17,
                0.15,
                0.12,
                0.08,
                0.03
            ],
            k=1
        )[0]

        # ------------------------------------
        # Create DOB from age
        # ------------------------------------

        today = date.today()

        birth_year = (
            today.year - age
        )

        birth_date = date(
            birth_year,
            random.randint(1, 12),
            random.randint(1, 28)
        )

        # ------------------------------------
        # Make sure the calculated age is
        # consistent with today's date.
        # ------------------------------------

        calculated_age = (
            today.year
            - birth_date.year
            - (
                (
                    today.month,
                    today.day
                )
                <
                (
                    birth_date.month,
                    birth_date.day
                )
            )
        )

        age = calculated_age

        # ------------------------------------
        # Registration date
        # ------------------------------------

        registration_date = fake.date_between(
            start_date=historical_start,
            end_date=historical_end
        )

        # ------------------------------------
        # Residential location
        #
        # city/state are selected together
        # so that combinations remain valid.
        # ------------------------------------

        location = random.choice(
            INDIAN_CITIES
        )

        city = location["city"]

        # ------------------------------------
        # Insurance type
        # ------------------------------------

        insurance_type = random.choices(
            insurance_types,
            weights=insurance_weights,
            k=1
        )[0]

        # ------------------------------------
        # Add patient
        # ------------------------------------

        patients.append({
            "patient_id": patient_id,
            "patient_name": patient_name,
            "gender": gender,
            "date_of_birth": birth_date.isoformat(),
            "age": age,
            "city": city,
            "registration_date": registration_date,
            "insurance_type": insurance_type
        })

    # ========================================
    # Create DataFrame
    # ========================================

    patient_df = pd.DataFrame(
        patients,
        columns=[
            "patient_id",
            "patient_name",
            "gender",
            "date_of_birth",
            "age",
            "city",
            "registration_date",
            "insurance_type"
        ]
    )

    # ========================================
    # Convert registration date to
    # YYYY-MM-DD string
    # ========================================

    patient_df[
        "registration_date"
    ] = pd.to_datetime(
        patient_df["registration_date"]
    ).dt.strftime(
        "%Y-%m-%d"
    )

    # ========================================
    # Validate patient count
    # ========================================

    if len(patient_df) != number_of_patients:

        raise ValueError(
            f"Expected {number_of_patients} "
            f"patients but generated "
            f"{len(patient_df)}."
        )

    # ========================================
    # Validate patient IDs
    # ========================================

    if patient_df[
        "patient_id"
    ].duplicated().any():

        raise ValueError(
            "Duplicate patient IDs generated."
        )

    # ========================================
    # Validate gender
    # ========================================

    invalid_gender = set(
        patient_df["gender"]
    ) - {
        "Male",
        "Female"
    }

    if invalid_gender:

        raise ValueError(
            "Invalid gender values: "
            f"{invalid_gender}"
        )

    # ========================================
    # Validate insurance
    # ========================================

    invalid_insurance = set(
        patient_df["insurance_type"]
    ) - {
        "Insurance",
        "Self Pay",
        "Corporate"
    }

    if invalid_insurance:

        raise ValueError(
            "Invalid insurance values: "
            f"{invalid_insurance}"
        )

    # ========================================
    # Validate dates
    # ========================================

    dob_series = pd.to_datetime(
        patient_df["date_of_birth"]
    )

    registration_series = pd.to_datetime(
        patient_df["registration_date"]
    )

    if (
        registration_series
        < pd.Timestamp(historical_start)
    ).any():

        raise ValueError(
            "Patient registration date "
            "occurs before historical start."
        )

    if (
        registration_series
        > pd.Timestamp(historical_end)
    ).any():

        raise ValueError(
            "Patient registration date "
            "occurs after historical end."
        )

    if (
        dob_series
        >= registration_series
    ).any():

        raise ValueError(
            "Patient date of birth must "
            "be before registration date."
        )

    # ========================================
    # Validate age
    # ========================================

    today = date.today()

    for _, patient in patient_df.iterrows():

        birth_date = date.fromisoformat(
            patient["date_of_birth"]
        )

        expected_age = (
            today.year
            - birth_date.year
            - (
                (
                    today.month,
                    today.day
                )
                <
                (
                    birth_date.month,
                    birth_date.day
                )
            )
        )

        if patient["age"] != expected_age:

            raise ValueError(
                f"Age mismatch for patient "
                f"{patient['patient_id']}."
            )

    # ========================================
    # Return
    # ========================================

    return patient_df