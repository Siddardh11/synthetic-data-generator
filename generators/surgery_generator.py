import json
import random

import pandas as pd
from faker import Faker

from utils.id_generator import generate_id


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

    Procedure dates remain within the associated
    admission period.
    """

    # ========================================
    # Read surgery schema
    # ========================================

    with open(
        schema_path,
        "r",
        encoding="utf-8"
    ) as file:
        schema = json.load(file)

    # ========================================
    # Get number of records
    # ========================================

    number_of_surgeries = config[
        "record_counts"
    ]["procedures"]

    # ========================================
    # Validate admission DataFrame
    # ========================================

    if admission_df.empty:

        raise ValueError(
            "No admission records available "
            "for surgery/procedure generation."
        )

    required_columns = {
        "admission_id",
        "patient_id",
        "hospital_id",
        "department_id",
        "doctor_id",
        "admission_date",
        "discharge_date"
    }

    missing_columns = (
        required_columns
        - set(admission_df.columns)
    )

    if missing_columns:

        raise ValueError(
            "Admission DataFrame is missing "
            f"required columns: {missing_columns}"
        )

    # ========================================
    # Prepare admission records
    # ========================================

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

    # ========================================
    # Surgery names
    # ========================================

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

    # ========================================
    # Procedure names
    # ========================================

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

    # ========================================
    # Cost ranges
    # ========================================

    surgery_cost_range = (
        25000,
        200000
    )

    procedure_cost_range = (
        2000,
        30000
    )

    # ========================================
    # Generate records
    # ========================================

    data = []

    for _ in range(number_of_surgeries):

        # ------------------------------------
        # Select existing admission
        # ------------------------------------

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

        # ------------------------------------
        # Convert admission date
        # ------------------------------------

        admission_date = pd.to_datetime(
            admission["admission_date"]
        ).date()

        # ------------------------------------
        # Convert discharge date
        # ------------------------------------

        discharge_value = admission[
            "discharge_date"
        ]

        if pd.isna(discharge_value):

            discharge_date = (
                pd.Timestamp.today().date()
            )

        else:

            discharge_date = pd.to_datetime(
                discharge_value
            ).date()

        # ------------------------------------
        # Safety check
        # ------------------------------------

        if discharge_date < admission_date:

            raise ValueError(
                f"Admission {admission_id} has "
                "discharge date before admission date."
            )

        # ------------------------------------
        # Select category
        #
        # 30% Surgery
        # 70% Procedure
        # ------------------------------------

        procedure_category = random.choices(
            [
                "Surgery",
                "Procedure"
            ],
            weights=[
                30,
                70
            ],
            k=1
        )[0]

        # ------------------------------------
        # Select name and cost range
        # ------------------------------------

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

        # ------------------------------------
        # Procedure date
        #
        # Must occur during admission.
        # ------------------------------------

        procedure_date = fake.date_between(
            start_date=admission_date,
            end_date=discharge_date
        )

        # ------------------------------------
        # Procedure status
        # ------------------------------------

        procedure_status = random.choices(
            [
                "Completed",
                "Cancelled"
            ],
            weights=[
                90,
                10
            ],
            k=1
        )[0]

        # ------------------------------------
        # Cost
        # ------------------------------------

        cost = random.randint(
            minimum_cost,
            maximum_cost
        )

        # ------------------------------------
        # Generate unique procedure ID
        # ------------------------------------

        procedure_id = generate_id(
            "surgery"
        )

        # ------------------------------------
        # Create record
        # ------------------------------------

        surgery = {
            "procedure_id": procedure_id,
            "patient_id": patient_id,
            "admission_id": admission_id,
            "hospital_id": hospital_id,
            "department_id": department_id,
            "doctor_id": doctor_id,
            "procedure_date": (
                procedure_date.isoformat()
            ),
            "procedure_name": procedure_name,
            "procedure_category": procedure_category,
            "procedure_status": procedure_status,
            "cost": cost
        }

        data.append(surgery)

    # ========================================
    # Convert to DataFrame
    # ========================================

    df = pd.DataFrame(data)

    # ========================================
    # Keep schema-defined column order
    # ========================================

    column_order = [
        column["name"]
        for column in schema["columns"]
    ]

    df = df[column_order]

    # ========================================
    # Validate record count
    # ========================================

    if len(df) != number_of_surgeries:

        raise ValueError(
            f"Expected {number_of_surgeries} "
            f"records but generated "
            f"{len(df)}."
        )

    # ========================================
    # Validate unique procedure IDs
    # ========================================

    if df[
        "procedure_id"
    ].duplicated().any():

        raise ValueError(
            "Duplicate procedure IDs generated."
        )

    # ========================================
    # Validate admission relationship
    # ========================================

    valid_admission_ids = set(
        admission_df["admission_id"]
    )

    invalid_admission_ids = (
        set(df["admission_id"])
        - valid_admission_ids
    )

    if invalid_admission_ids:

        raise ValueError(
            "Surgery/procedure records contain "
            "invalid admission IDs: "
            f"{invalid_admission_ids}"
        )

    # ========================================
    # Validate inherited relationships
    # ========================================

    admission_lookup = (
        admission_df[
            [
                "admission_id",
                "patient_id",
                "hospital_id",
                "department_id",
                "doctor_id"
            ]
        ]
        .set_index("admission_id")
        .to_dict("index")
    )

    for row in df.itertuples(
        index=False
    ):

        admission = admission_lookup[
            row.admission_id
        ]

        # ------------------------------------
        # Patient
        # ------------------------------------

        if row.patient_id != admission[
            "patient_id"
        ]:

            raise ValueError(
                f"Procedure {row.procedure_id}: "
                "patient does not match "
                "associated admission."
            )

        # ------------------------------------
        # Hospital
        # ------------------------------------

        if row.hospital_id != admission[
            "hospital_id"
        ]:

            raise ValueError(
                f"Procedure {row.procedure_id}: "
                "hospital does not match "
                "associated admission."
            )

        # ------------------------------------
        # Department
        # ------------------------------------

        if row.department_id != admission[
            "department_id"
        ]:

            raise ValueError(
                f"Procedure {row.procedure_id}: "
                "department does not match "
                "associated admission."
            )

        # ------------------------------------
        # Doctor
        # ------------------------------------

        if row.doctor_id != admission[
            "doctor_id"
        ]:

            raise ValueError(
                f"Procedure {row.procedure_id}: "
                "doctor does not match "
                "associated admission."
            )

    # ========================================
    # Validate procedure dates
    # ========================================

    for row in df.itertuples(
        index=False
    ):

        admission = admission_lookup[
            row.admission_id
        ]

        admission_date = pd.to_datetime(
            admission_df.loc[
                admission_df["admission_id"]
                == row.admission_id,
                "admission_date"
            ].iloc[0]
        ).date()

        discharge_value = admission_df.loc[
            admission_df["admission_id"]
            == row.admission_id,
            "discharge_date"
        ].iloc[0]

        if pd.isna(discharge_value):

            discharge_date = (
                pd.Timestamp.today().date()
            )

        else:

            discharge_date = pd.to_datetime(
                discharge_value
            ).date()

        procedure_date = date_from_iso(
            row.procedure_date
        )

        if procedure_date < admission_date:

            raise ValueError(
                f"Procedure {row.procedure_id}: "
                "procedure date occurs before "
                "admission date."
            )

        if procedure_date > discharge_date:

            raise ValueError(
                f"Procedure {row.procedure_id}: "
                "procedure date occurs after "
                "discharge date."
            )

    # ========================================
    # Validate cost
    # ========================================

    if (
        df["cost"] <= 0
    ).any():

        raise ValueError(
            "Procedure/surgery cost must "
            "be greater than zero."
        )

    # ========================================
    # Return
    # ========================================

    return df


def date_from_iso(value):
    """
    Convert YYYY-MM-DD string into a date object.
    """

    return pd.to_datetime(
        value
    ).date()