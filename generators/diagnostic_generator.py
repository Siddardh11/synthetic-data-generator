import json
import pandas as pd
from faker import Faker
import random


fake = Faker()


def generate_diagnostics(
    schema_path,
    visit_df,
    config
):
    """
    Generate synthetic diagnostic test records.

    Each diagnostic test is linked to an existing visit,
    ensuring valid patient, hospital, department and
    doctor relationships.
    """

    # --------------------------------
    # Read diagnostic schema
    # --------------------------------

    with open(
        schema_path,
        "r",
        encoding="utf-8"
    ) as file:
        schema = json.load(file)

    # --------------------------------
    # Get number of diagnostic records
    # --------------------------------

    number_of_diagnostics = config[
        "record_counts"
    ]["diagnostic_tests"]

    # --------------------------------
    # Prepare visit records
    # --------------------------------

    visit_records = visit_df[
        [
            "visit_id",
            "patient_id",
            "hospital_id",
            "department_id",
            "doctor_id",
            "visit_date"
        ]
    ].to_dict("records")

    # --------------------------------
    # Test definitions
    # --------------------------------

    test_categories = {
        "CBC": "Pathology",
        "Blood Sugar": "Pathology",
        "Lipid Profile": "Pathology",
        "ECG": "Cardiology",
        "X-Ray": "Radiology",
        "CT Scan": "Radiology",
        "MRI": "Radiology",
        "Ultrasound": "Radiology",
        "Kidney Function Test": "Pathology",
        "Liver Function Test": "Pathology"
    }

    # --------------------------------
    # Approximate synthetic test
    # price ranges
    # --------------------------------

    test_amounts = {
        "CBC": (300, 800),
        "Blood Sugar": (150, 500),
        "Lipid Profile": (500, 1200),
        "ECG": (300, 1000),
        "X-Ray": (500, 1500),
        "CT Scan": (3000, 8000),
        "MRI": (5000, 15000),
        "Ultrasound": (800, 2500),
        "Kidney Function Test": (500, 1500),
        "Liver Function Test": (600, 1800)
    }

    data = []

    diagnostic_id = 1

    # --------------------------------
    # Generate diagnostic records
    # --------------------------------

    for _ in range(number_of_diagnostics):

        # --------------------------------
        # Select an existing visit
        # --------------------------------

        visit = random.choice(
            visit_records
        )

        # --------------------------------
        # Inherit relationships from visit
        # --------------------------------

        visit_id = visit["visit_id"]

        patient_id = visit["patient_id"]

        hospital_id = visit["hospital_id"]

        department_id = visit["department_id"]

        doctor_id = visit["doctor_id"]

        visit_date = visit["visit_date"]

        # --------------------------------
        # Select test
        # --------------------------------

        test_name = random.choice(
            list(test_categories.keys())
        )

        test_category = test_categories[
            test_name
        ]

        # --------------------------------
        # Test date
        #
        # Diagnostic test cannot happen
        # before the associated visit.
        # --------------------------------

        test_date = fake.date_between(
            start_date=visit_date,
            end_date="today"
        )

        # --------------------------------
        # Test status
        # --------------------------------

        test_status = random.choice([
            "Completed",
            "Pending"
        ])

        # --------------------------------
        # Test amount
        # --------------------------------

        minimum_amount, maximum_amount = (
            test_amounts[test_name]
        )

        amount = random.randint(
            minimum_amount,
            maximum_amount
        )

        # --------------------------------
        # Create diagnostic record
        # --------------------------------

        diagnostic = {
            "diagnostic_id": diagnostic_id,
            "patient_id": patient_id,
            "visit_id": visit_id,
            "hospital_id": hospital_id,
            "department_id": department_id,
            "doctor_id": doctor_id,
            "test_date": test_date,
            "test_name": test_name,
            "test_category": test_category,
            "test_status": test_status,
            "amount": amount
        }

        data.append(diagnostic)

        diagnostic_id += 1

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