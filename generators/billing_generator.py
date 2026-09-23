import json
import pandas as pd
from faker import Faker
import random
from datetime import date


fake = Faker()


def generate_billing(
    schema_path,
    patient_df,
    visit_df,
    admission_df,
    hospital_df,
    department_df,
    config
):
    """
    Generate synthetic billing records while maintaining
    valid patient, visit, admission, hospital and department
    relationships.

    Billing rules:

    total_amount = gross_amount - discount_amount

    insurance_amount + patient_amount = total_amount
    """

    # --------------------------------
    # Read billing schema
    # --------------------------------

    with open(
        schema_path,
        "r",
        encoding="utf-8"
    ) as file:
        schema = json.load(file)

    # --------------------------------
    # Get number of billing records
    # --------------------------------

    number_of_bills = config[
        "record_counts"
    ]["billing_records"]

    # --------------------------------
    # Prepare patient records
    # --------------------------------

    patient_records = patient_df[
        [
            "patient_id",
            "registration_date",
            "insurance_type"
        ]
    ].to_dict("records")

    # --------------------------------
    # Prepare visit records
    # --------------------------------

    visit_records = visit_df[
        [
            "visit_id",
            "patient_id",
            "hospital_id",
            "department_id",
            "visit_date"
        ]
    ].to_dict("records")

    # --------------------------------
    # Prepare admission records
    # --------------------------------

    admission_records = admission_df[
        [
            "admission_id",
            "patient_id",
            "hospital_id",
            "department_id",
            "admission_date",
            "discharge_date"
        ]
    ].to_dict("records")

    # --------------------------------
    # Bill categories
    # --------------------------------

    bill_categories = [
        "Consultation",
        "Procedure",
        "Room",
        "Pharmacy",
        "Diagnostic",
        "Surgery"
    ]

    data = []

    bill_id = 1

    # --------------------------------
    # Generate billing records
    # --------------------------------

    for _ in range(number_of_bills):

        # --------------------------------
        # Select bill category first
        # --------------------------------

        bill_category = random.choice(
            bill_categories
        )

        # --------------------------------
        # Room and Surgery bills should
        # be associated with an admission.
        # --------------------------------

        if bill_category in [
            "Room",
            "Surgery"
        ] and admission_records:

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

            admission_date = admission[
                "admission_date"
            ]

            discharge_date = admission[
                "discharge_date"
            ]

            visit_id = None

            # Bill date must be on or after admission
            if discharge_date is not None:

                bill_date = fake.date_between(
                    start_date=admission_date,
                    end_date=discharge_date
                )

            else:

                bill_date = fake.date_between(
                    start_date=admission_date,
                    end_date="today"
                )

        # --------------------------------
        # Other bill categories are linked
        # to a patient visit.
        # --------------------------------

        else:

            visit = random.choice(
                visit_records
            )

            visit_id = visit[
                "visit_id"
            ]

            patient_id = visit[
                "patient_id"
            ]

            hospital_id = visit[
                "hospital_id"
            ]

            department_id = visit[
                "department_id"
            ]

            visit_date = visit[
                "visit_date"
            ]

            admission_id = None

            # Bill date cannot be before visit date
            bill_date = fake.date_between(
                start_date=visit_date,
                end_date="today"
            )

        # --------------------------------
        # Get patient's insurance type
        # --------------------------------

        patient = patient_df[
            patient_df["patient_id"] == patient_id
        ].iloc[0]

        insurance_type = patient[
            "insurance_type"
        ]

        # --------------------------------
        # Generate gross amount based
        # on bill category
        # --------------------------------

        if bill_category == "Consultation":

            gross_amount = random.randint(
                500,
                2500
            )

        elif bill_category == "Procedure":

            gross_amount = random.randint(
                2000,
                15000
            )

        elif bill_category == "Room":

            gross_amount = random.randint(
                3000,
                20000
            )

        elif bill_category == "Pharmacy":

            gross_amount = random.randint(
                500,
                10000
            )

        elif bill_category == "Diagnostic":

            gross_amount = random.randint(
                1000,
                12000
            )

        else:
            # Surgery

            gross_amount = random.randint(
                25000,
                150000
            )

        # --------------------------------
        # Generate discount
        #
        # Keep discount below gross amount.
        # --------------------------------

        discount_percentage = random.uniform(
            0.00,
            0.20
        )

        discount_amount = round(
            gross_amount * discount_percentage,
            2
        )

        # --------------------------------
        # Calculate final amount
        # --------------------------------

        total_amount = round(
            gross_amount - discount_amount,
            2
        )

        # --------------------------------
        # Insurance contribution
        #
        # Self Pay -> no insurance
        # Insurance / Corporate -> partial
        # coverage.
        # --------------------------------

        if insurance_type == "Self Pay":

            insurance_amount = 0.00

        elif insurance_type == "Corporate":

            insurance_percentage = random.uniform(
                0.60,
                0.90
            )

            insurance_amount = round(
                total_amount * insurance_percentage,
                2
            )

        else:
            # Insurance

            insurance_percentage = random.uniform(
                0.50,
                0.80
            )

            insurance_amount = round(
                total_amount * insurance_percentage,
                2
            )

        # --------------------------------
        # Patient contribution
        # --------------------------------

        patient_amount = round(
            total_amount - insurance_amount,
            2
        )

        # --------------------------------
        # Payment status
        # --------------------------------

        payment_status = random.choice([
            "Paid",
            "Pending",
            "Partial"
        ])

        # --------------------------------
        # Create billing record
        # --------------------------------

        bill = {
            "bill_id": bill_id,
            "patient_id": patient_id,
            "visit_id": visit_id,
            "admission_id": admission_id,
            "hospital_id": hospital_id,
            "department_id": department_id,
            "bill_date": bill_date,
            "bill_category": bill_category,
            "gross_amount": round(
                gross_amount,
                2
            ),
            "discount_amount": discount_amount,
            "insurance_amount": insurance_amount,
            "patient_amount": patient_amount,
            "total_amount": total_amount,
            "payment_status": payment_status
        }

        data.append(bill)

        bill_id += 1

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