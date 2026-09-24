import json
import random

import pandas as pd
from faker import Faker

from utils.id_generator import generate_id


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

    Diagnostic dates are generated on the same day or
    within a few days after the associated visit.
    """

    # ========================================
    # Read diagnostic schema
    # ========================================

    with open(
        schema_path,
        "r",
        encoding="utf-8"
    ) as file:
        schema = json.load(file)

    # ========================================
    # Get number of diagnostic records
    # ========================================

    number_of_diagnostics = config[
        "record_counts"
    ]["diagnostic_tests"]

    # ========================================
    # Historical date range
    # ========================================

    historical_start = pd.to_datetime(
        config["date_range"]["start_date"]
    ).date()

    historical_end = pd.to_datetime(
        config["date_range"]["end_date"]
    ).date()

    # ========================================
    # Validate visit DataFrame
    # ========================================

    if visit_df.empty:

        raise ValueError(
            "No visit records available "
            "for diagnostic generation."
        )

    required_visit_columns = {
        "visit_id",
        "patient_id",
        "hospital_id",
        "department_id",
        "doctor_id",
        "visit_date"
    }

    missing_columns = (
        required_visit_columns
        - set(visit_df.columns)
    )

    if missing_columns:

        raise ValueError(
            "Visit DataFrame is missing "
            f"required columns: {missing_columns}"
        )

    # ========================================
    # Prepare visit records
    # ========================================

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

    # ========================================
    # Test definitions
    # ========================================

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

    # ========================================
    # Diagnostic price ranges
    # ========================================

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

    # ========================================
    # Test selection weights
    # ========================================

    test_names = list(
        test_categories.keys()
    )

    test_weights = [
        0.22,  # CBC
        0.15,  # Blood Sugar
        0.08,  # Lipid Profile
        0.10,  # ECG
        0.12,  # X-Ray
        0.06,  # CT Scan
        0.04,  # MRI
        0.08,  # Ultrasound
        0.08,  # Kidney Function Test
        0.07   # Liver Function Test
    ]

    # ========================================
    # Generate diagnostics
    # ========================================

    data = []

    for _ in range(number_of_diagnostics):

        # ------------------------------------
        # Select an actual visit
        # ------------------------------------

        visit = random.choice(
            visit_records
        )

        # ------------------------------------
        # Inherit all relationships from visit
        # ------------------------------------

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

        doctor_id = visit[
            "doctor_id"
        ]

        visit_date = pd.to_datetime(
            visit["visit_date"]
        ).date()

        # ------------------------------------
        # Validate visit date
        # ------------------------------------

        if visit_date < historical_start:

            raise ValueError(
                f"Visit {visit_id} occurs before "
                "the configured historical range."
            )

        if visit_date > historical_end:

            raise ValueError(
                f"Visit {visit_id} occurs after "
                "the configured historical range."
            )

        # ------------------------------------
        # Select diagnostic test
        # ------------------------------------

        test_name = random.choices(
            test_names,
            weights=test_weights,
            k=1
        )[0]

        test_category = test_categories[
            test_name
        ]

        # ------------------------------------
        # Test date
        #
        # Test can occur:
        #   Visit date
        #   Visit + 1 day
        #   Visit + 2 days
        #   Visit + 3 days
        #
        # Never after historical_end.
        # ------------------------------------

        test_start = max(
            visit_date,
            historical_start
        )

        test_end = min(
            visit_date + pd.Timedelta(
                days=3
            ).to_pytimedelta(),
            historical_end
        )

        if test_start > test_end:

            test_start = test_end

        test_date = fake.date_between(
            start_date=test_start,
            end_date=test_end
        )

        # ------------------------------------
        # Test status
        # ------------------------------------

        test_status = random.choices(
            [
                "Completed",
                "Pending"
            ],
            weights=[
                0.90,
                0.10
            ],
            k=1
        )[0]

        # ------------------------------------
        # Diagnostic amount
        # ------------------------------------

        minimum_amount, maximum_amount = (
            test_amounts[test_name]
        )

        amount = random.randint(
            minimum_amount,
            maximum_amount
        )

        # ------------------------------------
        # Generate unique diagnostic ID
        # ------------------------------------

        diagnostic_id = generate_id(
            "diagnostic"
        )

        # ------------------------------------
        # Create record
        # ------------------------------------

        diagnostic = {
            "diagnostic_id": diagnostic_id,
            "patient_id": patient_id,
            "visit_id": visit_id,
            "hospital_id": hospital_id,
            "department_id": department_id,
            "doctor_id": doctor_id,
            "test_date": test_date.isoformat(),
            "test_name": test_name,
            "test_category": test_category,
            "test_status": test_status,
            "amount": amount
        }

        data.append(
            diagnostic
        )

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

    if len(df) != number_of_diagnostics:

        raise ValueError(
            f"Expected {number_of_diagnostics} "
            f"diagnostics but generated "
            f"{len(df)}."
        )

    # ========================================
    # Validate diagnostic IDs
    # ========================================

    if df[
        "diagnostic_id"
    ].duplicated().any():

        raise ValueError(
            "Duplicate diagnostic IDs generated."
        )

    # ========================================
    # Validate visit relationship
    # ========================================

    valid_visit_ids = set(
        visit_df["visit_id"]
    )

    invalid_visit_ids = (
        set(df["visit_id"])
        - valid_visit_ids
    )

    if invalid_visit_ids:

        raise ValueError(
            "Diagnostics contain invalid "
            f"visit IDs: {invalid_visit_ids}"
        )

    # ========================================
    # Validate inherited relationships
    # ========================================

    visit_lookup = (
        visit_df[
            [
                "visit_id",
                "patient_id",
                "hospital_id",
                "department_id",
                "doctor_id"
            ]
        ]
        .set_index("visit_id")
        .to_dict("index")
    )

    for row in df.itertuples(
        index=False
    ):

        visit = visit_lookup[
            row.visit_id
        ]

        # ------------------------------------
        # Patient
        # ------------------------------------

        if row.patient_id != visit[
            "patient_id"
        ]:

            raise ValueError(
                f"Diagnostic {row.diagnostic_id}: "
                "patient does not match "
                "associated visit."
            )

        # ------------------------------------
        # Hospital
        # ------------------------------------

        if row.hospital_id != visit[
            "hospital_id"
        ]:

            raise ValueError(
                f"Diagnostic {row.diagnostic_id}: "
                "hospital does not match "
                "associated visit."
            )

        # ------------------------------------
        # Department
        # ------------------------------------

        if row.department_id != visit[
            "department_id"
        ]:

            raise ValueError(
                f"Diagnostic {row.diagnostic_id}: "
                "department does not match "
                "associated visit."
            )

        # ------------------------------------
        # Doctor
        # ------------------------------------

        if row.doctor_id != visit[
            "doctor_id"
        ]:

            raise ValueError(
                f"Diagnostic {row.diagnostic_id}: "
                "doctor does not match "
                "associated visit."
            )

    # ========================================
    # Validate diagnostic dates
    # ========================================

    diagnostic_dates = pd.to_datetime(
        df["test_date"]
    )

    if (
        diagnostic_dates
        < pd.Timestamp(historical_start)
    ).any():

        raise ValueError(
            "Diagnostic test date occurs "
            "before historical start date."
        )

    if (
        diagnostic_dates
        > pd.Timestamp(historical_end)
    ).any():

        raise ValueError(
            "Diagnostic test date occurs "
            "after historical end date."
        )

    # ========================================
    # Validate test amounts
    # ========================================

    if (
        df["amount"] <= 0
    ).any():

        raise ValueError(
            "Diagnostic amount must be "
            "greater than zero."
        )

    # ========================================
    # Return
    # ========================================

    return df