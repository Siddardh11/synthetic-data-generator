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

    Admission characteristics are correlated so that:
    - Emergency admissions are more likely to use ICU.
    - Planned admissions are more likely to use General,
      Semi-Private and Private wards.
    - ICU admissions generally have longer stays.
    - Emergency admissions generally have longer stays than
      planned admissions.
    - Discharge dates remain logically consistent with
      admission dates.
    - Ongoing admissions are recent and have no discharge date.
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
    # Historical date range
    # --------------------------------

    historical_start = date.fromisoformat(
        config["date_range"]["start_date"]
    )

    historical_end = date.fromisoformat(
        config["date_range"]["end_date"]
    )

    # Never generate dates after today.
    effective_end = min(
        historical_end,
        date.today()
    )

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
        # Convert registration date
        # --------------------------------

        if isinstance(registration_date, str):

            registration_date = date.fromisoformat(
                registration_date
            )

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
        # Admission type
        #
        # Planned admissions are slightly
        # more common than emergency.
        # --------------------------------

        admission_type = random.choices(
            [
                "Planned",
                "Emergency"
            ],
            weights=[
                0.55,
                0.45
            ],
            k=1
        )[0]

        # --------------------------------
        # Ward type
        #
        # Ward selection depends partly
        # on admission type.
        # --------------------------------

        if admission_type == "Emergency":

            ward_type = random.choices(
                [
                    "General",
                    "Semi-Private",
                    "Private",
                    "ICU"
                ],
                weights=[
                    0.35,
                    0.20,
                    0.10,
                    0.35
                ],
                k=1
            )[0]

        else:

            ward_type = random.choices(
                [
                    "General",
                    "Semi-Private",
                    "Private",
                    "ICU"
                ],
                weights=[
                    0.40,
                    0.30,
                    0.25,
                    0.05
                ],
                k=1
            )[0]

        # --------------------------------
        # Diagnosis category
        # --------------------------------

        diagnosis_category = random.choice(
            diagnosis_categories
        )

        # --------------------------------
        # Admission status
        #
        # Most admissions are discharged.
        # A smaller portion are ongoing.
        # --------------------------------

        admission_status = random.choices(
            [
                "Discharged",
                "Ongoing"
            ],
            weights=[
                0.92,
                0.08
            ],
            k=1
        )[0]

        # --------------------------------
        # Determine valid admission range
        # --------------------------------

        admission_start = max(
            registration_date,
            historical_start
        )

        # --------------------------------
        # Admission date
        #
        # Discharged admissions:
        #   Can occur anywhere in the
        #   historical period.
        #
        # Ongoing admissions:
        #   Must be recent so that the
        #   calculated ongoing LOS remains
        #   realistic.
        # --------------------------------

        if admission_status == "Ongoing":

            # Keep ongoing admissions within
            # the last 30 days.

            recent_start = effective_end - timedelta(
                days=30
            )

            admission_start = max(
                admission_start,
                recent_start
            )

            if admission_start > effective_end:

                admission_start = effective_end

            admission_date = fake.date_between(
                start_date=admission_start,
                end_date=effective_end
            )

        else:

            if admission_start > effective_end:

                admission_start = effective_end

            admission_date = fake.date_between(
                start_date=admission_start,
                end_date=effective_end
            )

        # --------------------------------
        # Length of stay
        #
        # LOS depends on:
        # - Admission type
        # - Ward type
        #
        # ICU generally has the longest
        # expected stay.
        # --------------------------------

        if ward_type == "ICU":

            if admission_type == "Emergency":

                stay_days = random.randint(
                    5,
                    21
                )

            else:

                stay_days = random.randint(
                    3,
                    14
                )

        elif ward_type == "Private":

            if admission_type == "Emergency":

                stay_days = random.randint(
                    3,
                    12
                )

            else:

                stay_days = random.randint(
                    2,
                    8
                )

        elif ward_type == "Semi-Private":

            if admission_type == "Emergency":

                stay_days = random.randint(
                    3,
                    10
                )

            else:

                stay_days = random.randint(
                    2,
                    7
                )

        else:

            # General ward

            if admission_type == "Emergency":

                stay_days = random.randint(
                    2,
                    8
                )

            else:

                stay_days = random.randint(
                    1,
                    6
                )

        # --------------------------------
        # Discharged admission
        # --------------------------------

        if admission_status == "Discharged":

            discharge_date = (
                admission_date
                + timedelta(days=stay_days)
            )

            # --------------------------------
            # Do not allow discharge after
            # the configured historical end.
            # --------------------------------

            if discharge_date > historical_end:

                discharge_date = historical_end

            # --------------------------------
            # Do not allow discharge after
            # today.
            # --------------------------------

            if discharge_date > date.today():

                discharge_date = date.today()

            # --------------------------------
            # Recalculate LOS from the actual
            # admission and discharge dates.
            # --------------------------------

            stay_days = (
                discharge_date - admission_date
            ).days

            # --------------------------------
            # Protect against negative LOS.
            # --------------------------------

            if stay_days < 0:

                stay_days = 0

                discharge_date = admission_date

            length_of_stay = stay_days

        # --------------------------------
        # Ongoing admission
        # --------------------------------

        else:

            # Ongoing admissions do not have
            # a discharge date.

            discharge_date = None

            # IMPORTANT:
            # The validator defines ongoing LOS
            # as today - admission_date.
            #
            # Therefore we calculate it exactly
            # that way instead of randomly assigning
            # a separate LOS.

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