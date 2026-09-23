import json
import pandas as pd
from faker import Faker
import random


fake = Faker()


def generate_surgeries(
    schema_path,
    admission_df,
    config
):
    """
    Generate synthetic surgery/procedure records.

    Each record is linked to an existing admission,
    ensuring valid patient, hospital, department,
    and doctor relationships.
    """

    # --------------------------------
    # Read surgery schema
    # --------------------------------

    with open(
        schema_path,
        "r",
        encoding="utf-8"
    ) as file:
        schema = json.load(file)

    # --------------------------------
    # Get number of surgery records
    # --------------------------------

    number_of_surgeries = config[
        "record_counts"
    ]["procedures"]

    # --------------------------------
    # Prepare admission records
    # --------------------------------

    admission_records = admission_df[
        [
            "admission_id",
            "patient_id",
            "hospital_id",
            "department_id",
            "doctor_id",
            "admission_date",
            "discharge_date"
        ]
    ].to_dict("records")

    # --------------------------------
    # Surgery names
    # --------------------------------

    surgery_names = [
        "Appendectomy",
        "Gallbladder Surgery",
        "Hernia Repair",
        "Knee Replacement",
        "Hip Replacement",
        "Cataract Surgery",
        "Cardiac Bypass Surgery",
        "Cesarean Section",
        "Tumor Removal",
        "Fracture Surgery"
    ]

    # --------------------------------
    # Procedure names
    # --------------------------------

    procedure_names = [
        "Wound Dressing",
        "Biopsy",
        "Endoscopy",
        "Colonoscopy",
        "Minor Wound Repair",
        "Catheterization",
        "Suture Removal",
        "Abscess Drainage",
        "Central Line Placement",
        "Minor Excision"
    ]

    # --------------------------------
    # Cost ranges
    # --------------------------------

    surgery_cost_range = (
        25000,
        200000
    )

    procedure_cost_range = (
        2000,
        30000
    )

    data = []

    procedure_id = 1

    # --------------------------------
    # Generate records
    # --------------------------------

    for _ in range(number_of_surgeries):

        # --------------------------------
        # Select an existing admission
        # --------------------------------

        admission = random.choice(
            admission_records
        )

        admission_id = admission[
            "admission_id"
        ]

        patient_id = admission[
            "patient_id"
        ]

        hospital_id = admission[
            "hospital_id"
        ]

        department_id = admission[
            "department_id"
        ]

        doctor_id = admission[
            "doctor_id"
        ]

        admission_date = admission[
            "admission_date"
        ]

        discharge_date = admission[
            "discharge_date"
        ]

        # --------------------------------
        # Select category
        # --------------------------------

        procedure_category = random.choice([
            "Surgery",
            "Procedure"
        ])

        # --------------------------------
        # Select name and cost range
        # --------------------------------

        if procedure_category == "Surgery":

            procedure_name = random.choice(
                surgery_names
            )

            minimum_cost, maximum_cost = (
                surgery_cost_range
            )

        else:

            procedure_name = random.choice(
                procedure_names
            )

            minimum_cost, maximum_cost = (
                procedure_cost_range
            )

        # --------------------------------
        # Generate procedure date
        #
        # The procedure must happen
        # during the admission.
        # --------------------------------

        if discharge_date is not None:

            procedure_date = fake.date_between(
                start_date=admission_date,
                end_date=discharge_date
            )

        else:

            procedure_date = fake.date_between(
                start_date=admission_date,
                end_date="today"
            )

        # --------------------------------
        # Status
        # --------------------------------

        procedure_status = random.choice([
            "Completed",
            "Cancelled"
        ])

        # --------------------------------
        # Cost
        # --------------------------------

        cost = random.randint(
            minimum_cost,
            maximum_cost
        )

        # --------------------------------
        # Create record
        # --------------------------------

        surgery = {
            "procedure_id": procedure_id,
            "patient_id": patient_id,
            "admission_id": admission_id,
            "hospital_id": hospital_id,
            "department_id": department_id,
            "doctor_id": doctor_id,
            "procedure_date": procedure_date,
            "procedure_name": procedure_name,
            "procedure_category": procedure_category,
            "procedure_status": procedure_status,
            "cost": cost
        }

        data.append(surgery)

        procedure_id += 1

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