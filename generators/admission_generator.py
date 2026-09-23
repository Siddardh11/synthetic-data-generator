import json
import pandas as pd
from faker import Faker
import random
from datetime import date, timedelta


fake = Faker()


def generate_admissions(
    schema_path,
    patient_df,
    hospital_df,
    department_df,
    doctor_df,
    config
):
    """
    Generate synthetic inpatient admissions while maintaining
    valid patient, hospital, department and doctor relationships.
    """

    # --------------------------------
    # Read admission schema
    # --------------------------------

    with open(
        schema_path,
        "r",
        encoding="utf-8"
    ) as file:
        schema = json.load(file)

    # --------------------------------
    # Get number of admissions
    # --------------------------------

    number_of_admissions = config[
        "record_counts"
    ]["admissions"]

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
    #
    # Selecting doctor first guarantees
    # valid hospital-department-doctor
    # relationships.
    # --------------------------------

    doctor_records = doctor_df[
        [
            "doctor_id",
            "hospital_id",
            "department_id"
        ]
    ].to_dict("records")

    # --------------------------------
    # Diagnosis categories
    #
    # These are synthetic categories
    # because no fixed list was provided
    # in the requirements.
    # --------------------------------

    diagnosis_categories = [
        "Cardiovascular",
        "Respiratory",
        "Neurological",
        "Orthopedic",
        "Gastrointestinal",
        "Renal",
        "Oncology",
        "Infectious Disease",
        "Endocrine",
        "General Medicine"
    ]

    data = []

    admission_id = 1

    # --------------------------------
    # Generate admissions
    # --------------------------------

    for _ in range(number_of_admissions):

        # --------------------------------
        # Select patient
        # --------------------------------

        patient = random.choice(
            patient_records
        )

        patient_id = patient["patient_id"]

        registration_date = patient[
            "registration_date"
        ]

        # --------------------------------
        # Select doctor
        # --------------------------------

        doctor = random.choice(
            doctor_records
        )

        doctor_id = doctor["doctor_id"]

        hospital_id = doctor["hospital_id"]

        department_id = doctor["department_id"]

        # --------------------------------
        # Admission date
        #
        # Admission cannot happen before
        # patient registration.
        # --------------------------------

        admission_date = fake.date_between(
            start_date=registration_date,
            end_date="today"
        )

        # --------------------------------
        # Admission type
        # --------------------------------

        admission_type = random.choice([
            "Emergency",
            "Planned"
        ])

        # --------------------------------
        # Ward type
        # --------------------------------

        ward_type = random.choice([
            "General",
            "Semi-Private",
            "Private",
            "ICU"
        ])

        # --------------------------------
        # Diagnosis category
        # --------------------------------

        diagnosis_category = random.choice(
            diagnosis_categories
        )

        # --------------------------------
        # Admission status
        # --------------------------------

        admission_status = random.choice([
            "Discharged",
            "Ongoing"
        ])

        # --------------------------------
        # Discharge date + length of stay
        # --------------------------------

        if admission_status == "Discharged":

            # Generate a stay between 1 and 30 days
            stay_days = random.randint(1, 30)

            discharge_date = (
                admission_date
                + timedelta(days=stay_days)
            )

            # Don't generate a future discharge
            # date for a completed admission.
            if discharge_date > date.today():

                discharge_date = date.today()

                stay_days = (
                    discharge_date - admission_date
                ).days

                # If admission happened today,
                # the stay is 0 days.
                if stay_days < 0:
                    stay_days = 0

            length_of_stay = stay_days

        else:

            # Ongoing admission has no discharge date.
            discharge_date = None

            length_of_stay = (
                date.today() - admission_date
            ).days

            if length_of_stay < 0:
                length_of_stay = 0

        # --------------------------------
        # Create admission record
        # --------------------------------

        admission = {
            "admission_id": admission_id,
            "patient_id": patient_id,
            "hospital_id": hospital_id,
            "department_id": department_id,
            "doctor_id": doctor_id,
            "admission_date": admission_date,
            "discharge_date": discharge_date,
            "admission_type": admission_type,
            "ward_type": ward_type,
            "diagnosis_category": diagnosis_category,
            "length_of_stay": length_of_stay,
            "admission_status": admission_status
        }

        data.append(admission)

        admission_id += 1

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