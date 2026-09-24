import json
import random

import pandas as pd
from faker import Faker

from utils.id_generator import generate_id


fake = Faker()


def generate_billing(
    schema_path,
    patient_df,
    visit_df,
    admission_df,
    diagnostic_df,
    surgery_df,
    hospital_df,
    department_df,
    config
):
    """
    Generate synthetic billing records using existing clinical activity.

    Billing is event-driven:

    - Consultation -> visit
    - Diagnostic   -> completed diagnostic activity
    - Pharmacy     -> visit or admission
    - Room         -> admission
    - Procedure    -> completed procedure activity
    - Surgery      -> completed surgery activity

    Financial rules:

    total_amount = gross_amount - discount_amount

    insurance_amount + patient_amount = total_amount
    """

    # ========================================
    # Read billing schema
    # ========================================

    with open(
        schema_path,
        "r",
        encoding="utf-8"
    ) as file:
        schema = json.load(file)

    # ========================================
    # Number of bills
    # ========================================

    number_of_bills = config[
        "record_counts"
    ]["billing_records"]

    # ========================================
    # Historical range
    # ========================================

    historical_start = pd.to_datetime(
        config["date_range"]["start_date"]
    ).date()

    historical_end = pd.to_datetime(
        config["date_range"]["end_date"]
    ).date()

    effective_end = min(
        historical_end,
        pd.Timestamp.today().date()
    )

    # ========================================
    # Validate source DataFrames
    # ========================================

    if patient_df.empty:
        raise ValueError(
            "Patient DataFrame is empty."
        )

    if visit_df.empty:
        raise ValueError(
            "Visit DataFrame is empty."
        )

    if admission_df.empty:
        raise ValueError(
            "Admission DataFrame is empty."
        )

    # ========================================
    # Patient records
    # ========================================

    patient_records = patient_df[
        [
            "patient_id",
            "registration_date",
            "insurance_type"
        ]
    ].to_dict("records")

    patient_lookup = {
        row["patient_id"]: row
        for row in patient_records
    }

    # ========================================
    # Visit records
    # ========================================

    visit_records = visit_df[
        [
            "visit_id",
            "patient_id",
            "hospital_id",
            "department_id",
            "visit_date"
        ]
    ].to_dict("records")

    # ========================================
    # Admission records
    # ========================================

    admission_records = admission_df[
        [
            "admission_id",
            "patient_id",
            "hospital_id",
            "department_id",
            "admission_date",
            "discharge_date",
            "admission_type",
            "ward_type",
            "length_of_stay"
        ]
    ].to_dict("records")

    # ========================================
    # Diagnostic records
    # ========================================

    diagnostic_records = diagnostic_df[
        [
            "diagnostic_id",
            "patient_id",
            "visit_id",
            "hospital_id",
            "department_id",
            "test_date",
            "test_name",
            "test_status",
            "amount"
        ]
    ].to_dict("records")

    # ========================================
    # Surgery / procedure records
    # ========================================

    surgery_records = surgery_df[
        [
            "procedure_id",
            "patient_id",
            "admission_id",
            "hospital_id",
            "department_id",
            "procedure_date",
            "procedure_category",
            "procedure_status",
            "cost"
        ]
    ].to_dict("records")

    # ========================================
    # Clinical event pools
    # ========================================

    completed_diagnostics = [
        diagnostic
        for diagnostic in diagnostic_records
        if str(
            diagnostic["test_status"]
        ).strip().lower()
        in {
            "completed",
            "complete",
            "done"
        }
    ]

    completed_procedures = [
        procedure
        for procedure in surgery_records
        if str(
            procedure["procedure_status"]
        ).strip().lower()
        in {
            "completed",
            "complete",
            "done"
        }
    ]

    completed_procedure_events = [
        procedure
        for procedure in completed_procedures
        if procedure["procedure_category"]
        == "Procedure"
    ]

    completed_surgery_events = [
        procedure
        for procedure in completed_procedures
        if procedure["procedure_category"]
        == "Surgery"
    ]

    # ========================================
    # Event selection helpers
    # ========================================

    def choose_unused_diagnostic():

        if not completed_diagnostics:
            return None

        index = random.randrange(
            len(completed_diagnostics)
        )

        completed_diagnostics[
            index
        ], completed_diagnostics[-1] = (
            completed_diagnostics[-1],
            completed_diagnostics[index]
        )

        return completed_diagnostics.pop()

    def choose_unused_procedure():

        if not completed_procedure_events:
            return None

        index = random.randrange(
            len(completed_procedure_events)
        )

        completed_procedure_events[
            index
        ], completed_procedure_events[-1] = (
            completed_procedure_events[-1],
            completed_procedure_events[index]
        )

        return completed_procedure_events.pop()

    def choose_unused_surgery():

        if not completed_surgery_events:
            return None

        index = random.randrange(
            len(completed_surgery_events)
        )

        completed_surgery_events[
            index
        ], completed_surgery_events[-1] = (
            completed_surgery_events[-1],
            completed_surgery_events[index]
        )

        return completed_surgery_events.pop()

    # ========================================
    # Room rates
    # ========================================

    room_daily_rates = {
        "General": (1800, 3000),
        "Semi-Private": (3000, 5000),
        "Private": (5000, 8000),
        "ICU": (10000, 18000)
    }

    # ========================================
    # Generate bills
    # ========================================

    data = []

    while len(data) < number_of_bills:

        available_event_categories = []

        if completed_procedure_events:
            available_event_categories.append(
                "Procedure"
            )

        if completed_surgery_events:
            available_event_categories.append(
                "Surgery"
            )

        if completed_diagnostics:
            available_event_categories.append(
                "Diagnostic"
            )

        normal_categories = [
            "Consultation",
            "Room",
            "Pharmacy"
        ]

        category_pool = (
            normal_categories
            + available_event_categories
        )

        # ------------------------------------
        # Billing category weights
        # ------------------------------------

        if available_event_categories:

            weights = []

            for category in category_pool:

                if category == "Consultation":
                    weights.append(0.34)

                elif category == "Room":
                    weights.append(0.20)

                elif category == "Pharmacy":
                    weights.append(0.23)

                elif category == "Diagnostic":
                    weights.append(0.10)

                elif category == "Procedure":
                    weights.append(0.08)

                elif category == "Surgery":
                    weights.append(0.05)

        else:

            weights = [
                0.50,
                0.25,
                0.25
            ]

        bill_category = random.choices(
            category_pool,
            weights=weights,
            k=1
        )[0]

        # ====================================
        # Common variables
        # ====================================

        visit_id = None
        admission_id = None
        gross_amount = 0.0

        # ====================================
        # Consultation
        # ====================================

        if bill_category == "Consultation":

            visit = random.choice(
                visit_records
            )

            visit_id = visit["visit_id"]

            patient_id = visit["patient_id"]
            hospital_id = visit["hospital_id"]
            department_id = visit["department_id"]

            visit_date = pd.to_datetime(
                visit["visit_date"]
            ).date()

            bill_start = max(
                visit_date,
                historical_start
            )

            bill_end = min(
                visit_date
                + pd.Timedelta(days=3).to_pytimedelta(),
                effective_end
            )

            if bill_start > bill_end:
                bill_start = bill_end

            bill_date = fake.date_between(
                start_date=bill_start,
                end_date=bill_end
            )

            gross_amount = random.randint(
                500,
                2500
            )

        # ====================================
        # Diagnostic
        # ====================================

        elif bill_category == "Diagnostic":

            diagnostic = (
                choose_unused_diagnostic()
            )

            if diagnostic is None:

                bill_category = "Consultation"

                visit = random.choice(
                    visit_records
                )

                visit_id = visit["visit_id"]

                patient_id = visit["patient_id"]
                hospital_id = visit["hospital_id"]
                department_id = visit["department_id"]

                visit_date = pd.to_datetime(
                    visit["visit_date"]
                ).date()

                bill_start = max(
                    visit_date,
                    historical_start
                )

                bill_end = min(
                    visit_date
                    + pd.Timedelta(days=3).to_pytimedelta(),
                    effective_end
                )

                if bill_start > bill_end:
                    bill_start = bill_end

                bill_date = fake.date_between(
                    start_date=bill_start,
                    end_date=bill_end
                )

                gross_amount = random.randint(
                    500,
                    2500
                )

            else:

                visit_id = diagnostic["visit_id"]

                patient_id = diagnostic["patient_id"]
                hospital_id = diagnostic["hospital_id"]
                department_id = diagnostic["department_id"]

                diagnostic_date = pd.to_datetime(
                    diagnostic["test_date"]
                ).date()

                bill_start = max(
                    diagnostic_date,
                    historical_start
                )

                bill_end = min(
                    diagnostic_date
                    + pd.Timedelta(days=1).to_pytimedelta(),
                    effective_end
                )

                if bill_start > bill_end:
                    bill_start = bill_end

                bill_date = fake.date_between(
                    start_date=bill_start,
                    end_date=bill_end
                )

                diagnostic_amount = float(
                    diagnostic["amount"]
                )

                gross_amount = round(
                    diagnostic_amount
                    * random.uniform(
                        0.95,
                        1.10
                    ),
                    2
                )

        # ====================================
        # Room
        # ====================================

        elif bill_category == "Room":

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

            admission_date = pd.to_datetime(
                admission["admission_date"]
            ).date()

            discharge_value = admission[
                "discharge_date"
            ]

            if pd.isna(discharge_value):

                discharge_date = effective_end

            else:

                discharge_date = pd.to_datetime(
                    discharge_value
                ).date()

            bill_start = max(
                admission_date,
                historical_start
            )

            bill_end = min(
                discharge_date,
                effective_end
            )

            if bill_start > bill_end:
                bill_start = bill_end

            bill_date = fake.date_between(
                start_date=bill_start,
                end_date=bill_end
            )

            ward_type = admission[
                "ward_type"
            ]

            minimum_daily, maximum_daily = (
                room_daily_rates.get(
                    ward_type,
                    room_daily_rates["General"]
                )
            )

            daily_rate = random.randint(
                minimum_daily,
                maximum_daily
            )

            length_of_stay = max(
                1,
                int(
                    admission[
                        "length_of_stay"
                    ]
                )
            )

            billed_days = random.randint(
                1,
                min(
                    length_of_stay,
                    7
                )
            )

            gross_amount = (
                daily_rate
                * billed_days
            )

        # ====================================
        # Procedure
        # ====================================

        elif bill_category == "Procedure":

            procedure = (
                choose_unused_procedure()
            )

            if procedure is None:

                bill_category = "Pharmacy"

                use_admission = (
                    bool(admission_records)
                    and random.random() < 0.45
                )

                if use_admission:

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

                    admission_date = pd.to_datetime(
                        admission["admission_date"]
                    ).date()

                    discharge_value = admission[
                        "discharge_date"
                    ]

                    if pd.isna(discharge_value):
                        discharge_date = effective_end
                    else:
                        discharge_date = pd.to_datetime(
                            discharge_value
                        ).date()

                    bill_start = max(
                        admission_date,
                        historical_start
                    )

                    bill_end = min(
                        discharge_date,
                        effective_end
                    )

                    if bill_start > bill_end:
                        bill_start = bill_end

                    bill_date = fake.date_between(
                        start_date=bill_start,
                        end_date=bill_end
                    )

                    length_of_stay = max(
                        1,
                        int(
                            admission[
                                "length_of_stay"
                            ]
                        )
                    )

                    ward_multiplier = {
                        "General": 1.00,
                        "Semi-Private": 1.15,
                        "Private": 1.30,
                        "ICU": 1.60
                    }.get(
                        admission["ward_type"],
                        1.00
                    )

                    base_pharmacy = random.randint(
                        500,
                        6000
                    )

                    gross_amount = round(
                        base_pharmacy
                        * ward_multiplier
                        * min(
                            1.75,
                            0.80
                            + 0.12
                            * length_of_stay
                        ),
                        2
                    )

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

                    visit_date = pd.to_datetime(
                        visit["visit_date"]
                    ).date()

                    bill_start = max(
                        visit_date,
                        historical_start
                    )

                    bill_end = min(
                        visit_date
                        + pd.Timedelta(
                            days=3
                        ).to_pytimedelta(),
                        effective_end
                    )

                    if bill_start > bill_end:
                        bill_start = bill_end

                    bill_date = fake.date_between(
                        start_date=bill_start,
                        end_date=bill_end
                    )

                    gross_amount = random.randint(
                        500,
                        10000
                    )

            else:

                admission_id = procedure[
                    "admission_id"
                ]

                patient_id = procedure[
                    "patient_id"
                ]

                hospital_id = procedure[
                    "hospital_id"
                ]

                department_id = procedure[
                    "department_id"
                ]

                procedure_date = pd.to_datetime(
                    procedure["procedure_date"]
                ).date()

                bill_start = max(
                    procedure_date,
                    historical_start
                )

                bill_end = min(
                    procedure_date
                    + pd.Timedelta(
                        days=1
                    ).to_pytimedelta(),
                    effective_end
                )

                if bill_start > bill_end:
                    bill_start = bill_end

                bill_date = fake.date_between(
                    start_date=bill_start,
                    end_date=bill_end
                )

                procedure_cost = float(
                    procedure["cost"]
                )

                gross_amount = round(
                    procedure_cost
                    * random.uniform(
                        0.95,
                        1.10
                    ),
                    2
                )

        # ====================================
        # Surgery
        # ====================================

        elif bill_category == "Surgery":

            surgery = choose_unused_surgery()

            if surgery is None:

                bill_category = "Pharmacy"

                use_admission = (
                    bool(admission_records)
                    and random.random() < 0.45
                )

                if use_admission:

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

                    admission_date = pd.to_datetime(
                        admission["admission_date"]
                    ).date()

                    discharge_value = admission[
                        "discharge_date"
                    ]

                    if pd.isna(discharge_value):
                        discharge_date = effective_end
                    else:
                        discharge_date = pd.to_datetime(
                            discharge_value
                        ).date()

                    bill_start = max(
                        admission_date,
                        historical_start
                    )

                    bill_end = min(
                        discharge_date,
                        effective_end
                    )

                    if bill_start > bill_end:
                        bill_start = bill_end

                    bill_date = fake.date_between(
                        start_date=bill_start,
                        end_date=bill_end
                    )

                    length_of_stay = max(
                        1,
                        int(
                            admission[
                                "length_of_stay"
                            ]
                        )
                    )

                    ward_multiplier = {
                        "General": 1.00,
                        "Semi-Private": 1.15,
                        "Private": 1.30,
                        "ICU": 1.60
                    }.get(
                        admission["ward_type"],
                        1.00
                    )

                    base_pharmacy = random.randint(
                        500,
                        6000
                    )

                    gross_amount = round(
                        base_pharmacy
                        * ward_multiplier
                        * min(
                            1.75,
                            0.80
                            + 0.12
                            * length_of_stay
                        ),
                        2
                    )

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

                    visit_date = pd.to_datetime(
                        visit["visit_date"]
                    ).date()

                    bill_start = max(
                        visit_date,
                        historical_start
                    )

                    bill_end = min(
                        visit_date
                        + pd.Timedelta(
                            days=3
                        ).to_pytimedelta(),
                        effective_end
                    )

                    if bill_start > bill_end:
                        bill_start = bill_end

                    bill_date = fake.date_between(
                        start_date=bill_start,
                        end_date=bill_end
                    )

                    gross_amount = random.randint(
                        500,
                        10000
                    )

            else:

                admission_id = surgery[
                    "admission_id"
                ]

                patient_id = surgery[
                    "patient_id"
                ]

                hospital_id = surgery[
                    "hospital_id"
                ]

                department_id = surgery[
                    "department_id"
                ]

                procedure_date = pd.to_datetime(
                    surgery["procedure_date"]
                ).date()

                bill_start = max(
                    procedure_date,
                    historical_start
                )

                bill_end = min(
                    procedure_date
                    + pd.Timedelta(
                        days=1
                    ).to_pytimedelta(),
                    effective_end
                )

                if bill_start > bill_end:
                    bill_start = bill_end

                bill_date = fake.date_between(
                    start_date=bill_start,
                    end_date=bill_end
                )

                surgery_cost = float(
                    surgery["cost"]
                )

                gross_amount = round(
                    surgery_cost
                    * random.uniform(
                        0.95,
                        1.10
                    ),
                    2
                )

        # ====================================
        # Pharmacy
        # ====================================

        else:

            use_admission = (
                bool(admission_records)
                and random.random() < 0.45
            )

            if use_admission:

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

                admission_date = pd.to_datetime(
                    admission["admission_date"]
                ).date()

                discharge_value = admission[
                    "discharge_date"
                ]

                if pd.isna(discharge_value):
                    discharge_date = effective_end
                else:
                    discharge_date = pd.to_datetime(
                        discharge_value
                    ).date()

                bill_start = max(
                    admission_date,
                    historical_start
                )

                bill_end = min(
                    discharge_date,
                    effective_end
                )

                if bill_start > bill_end:
                    bill_start = bill_end

                bill_date = fake.date_between(
                    start_date=bill_start,
                    end_date=bill_end
                )

                length_of_stay = max(
                    1,
                    int(
                        admission[
                            "length_of_stay"
                        ]
                    )
                )

                ward_multiplier = {
                    "General": 1.00,
                    "Semi-Private": 1.15,
                    "Private": 1.30,
                    "ICU": 1.60
                }.get(
                    admission["ward_type"],
                    1.00
                )

                base_pharmacy = random.randint(
                    500,
                    6000
                )

                gross_amount = round(
                    base_pharmacy
                    * ward_multiplier
                    * min(
                        1.75,
                        0.80
                        + 0.12
                        * length_of_stay
                    ),
                    2
                )

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

                visit_date = pd.to_datetime(
                    visit["visit_date"]
                ).date()

                bill_start = max(
                    visit_date,
                    historical_start
                )

                bill_end = min(
                    visit_date
                    + pd.Timedelta(
                        days=3
                    ).to_pytimedelta(),
                    effective_end
                )

                if bill_start > bill_end:
                    bill_start = bill_end

                bill_date = fake.date_between(
                    start_date=bill_start,
                    end_date=bill_end
                )

                gross_amount = random.randint(
                    500,
                    10000
                )

        # ====================================
        # Patient insurance
        # ====================================

        patient = patient_lookup[
            patient_id
        ]

        insurance_type = patient[
            "insurance_type"
        ]

        # ====================================
        # Discount
        # ====================================

        discount_percentage = random.uniform(
            0.00,
            0.20
        )

        discount_amount = round(
            gross_amount
            * discount_percentage,
            2
        )

        # ====================================
        # Total
        # ====================================

        total_amount = round(
            gross_amount
            - discount_amount,
            2
        )

        # ====================================
        # Insurance contribution
        # ====================================

        if insurance_type == "Self Pay":

            insurance_amount = 0.00

        elif insurance_type == "Corporate":

            insurance_percentage = random.uniform(
                0.60,
                0.90
            )

            insurance_amount = round(
                total_amount
                * insurance_percentage,
                2
            )

        else:

            insurance_percentage = random.uniform(
                0.50,
                0.80
            )

            insurance_amount = round(
                total_amount
                * insurance_percentage,
                2
            )

        # ====================================
        # Patient contribution
        # ====================================

        patient_amount = round(
            total_amount
            - insurance_amount,
            2
        )

        # ====================================
        # Payment status
        # ====================================

        payment_status = random.choices(
            [
                "Paid",
                "Pending",
                "Partial"
            ],
            weights=[
                0.75,
                0.15,
                0.10
            ],
            k=1
        )[0]

        # ====================================
        # Generate unique bill ID
        # ====================================

        bill_id = generate_id(
            "billing"
        )

        # ====================================
        # Create bill
        # ====================================

        bill = {
            "bill_id": bill_id,
            "patient_id": patient_id,
            "visit_id": visit_id,
            "admission_id": admission_id,
            "hospital_id": hospital_id,
            "department_id": department_id,
            "bill_date": bill_date.isoformat(),
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

    # ========================================
    # DataFrame
    # ========================================

    df = pd.DataFrame(data)

    # ========================================
    # Schema-defined column order
    # ========================================

    column_order = [
        column["name"]
        for column in schema["columns"]
    ]

    df = df[column_order]

    # ========================================
    # Final validations
    # ========================================

    if len(df) != number_of_bills:

        raise ValueError(
            f"Expected {number_of_bills} "
            f"billing records but generated "
            f"{len(df)}."
        )

    # ----------------------------------------
    # Unique bill IDs
    # ----------------------------------------

    if df["bill_id"].duplicated().any():

        raise ValueError(
            "Duplicate billing IDs generated."
        )

    # ----------------------------------------
    # Patient relationship
    # ----------------------------------------

    valid_patient_ids = set(
        patient_df["patient_id"]
    )

    invalid_patient_ids = (
        set(df["patient_id"])
        - valid_patient_ids
    )

    if invalid_patient_ids:

        raise ValueError(
            "Billing contains invalid patient IDs: "
            f"{invalid_patient_ids}"
        )

    # ----------------------------------------
    # Visit relationship
    # ----------------------------------------

    valid_visit_ids = set(
        visit_df["visit_id"]
    )

    billing_visit_ids = set(
        df["visit_id"].dropna()
    )

    invalid_visit_ids = (
        billing_visit_ids
        - valid_visit_ids
    )

    if invalid_visit_ids:

        raise ValueError(
            "Billing contains invalid visit IDs: "
            f"{invalid_visit_ids}"
        )

    # ----------------------------------------
    # Admission relationship
    # ----------------------------------------

    valid_admission_ids = set(
        admission_df["admission_id"]
    )

    billing_admission_ids = set(
        df["admission_id"].dropna()
    )

    invalid_admission_ids = (
        billing_admission_ids
        - valid_admission_ids
    )

    if invalid_admission_ids:

        raise ValueError(
            "Billing contains invalid admission IDs: "
            f"{invalid_admission_ids}"
        )

    # ----------------------------------------
    # Financial formula:
    #
    # total = gross - discount
    # ----------------------------------------

    calculated_total = (
        df["gross_amount"]
        - df["discount_amount"]
    ).round(2)

    if not (
        calculated_total
        == df["total_amount"].round(2)
    ).all():

        raise ValueError(
            "Billing financial formula failed: "
            "total_amount != "
            "gross_amount - discount_amount."
        )

    # ----------------------------------------
    # Financial formula:
    #
    # insurance + patient = total
    # ----------------------------------------

    calculated_split = (
        df["insurance_amount"]
        + df["patient_amount"]
    ).round(2)

    if not (
        calculated_split
        == df["total_amount"].round(2)
    ).all():

        raise ValueError(
            "Billing financial formula failed: "
            "insurance_amount + patient_amount "
            "!= total_amount."
        )

    # ----------------------------------------
    # Amount validation
    # ----------------------------------------

    amount_columns = [
        "gross_amount",
        "discount_amount",
        "insurance_amount",
        "patient_amount",
        "total_amount"
    ]

    for column in amount_columns:

        if (
            df[column] < 0
        ).any():

            raise ValueError(
                f"Negative values found in "
                f"{column}."
            )

    # ----------------------------------------
    # Date validation
    # ----------------------------------------

    billing_dates = pd.to_datetime(
        df["bill_date"]
    )

    if (
        billing_dates
        < pd.Timestamp(historical_start)
    ).any():

        raise ValueError(
            "Billing date occurs before "
            "historical start date."
        )

    if (
        billing_dates
        > pd.Timestamp(effective_end)
    ).any():

        raise ValueError(
            "Billing date occurs after "
            "effective end date."
        )

    # ========================================
    # Return
    # ========================================

    return df