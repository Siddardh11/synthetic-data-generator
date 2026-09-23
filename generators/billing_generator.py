import json
import pandas as pd
from faker import Faker
import random


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

    Clinical-cost correlations:
    - ICU admissions have the highest room daily rates.
    - Private wards cost more than Semi-Private and General.
    - Longer stays produce higher room charges.
    - Inpatient pharmacy cost increases with ward level and LOS.
    - Surgery/procedure bills are derived from actual procedure costs.
    - Diagnostic bills are derived from actual diagnostic amounts.

    Event-billing rules:
    - A completed procedure can generate at most one Procedure bill.
    - A completed surgery can generate at most one Surgery bill.
    - A completed diagnostic test can generate at most one Diagnostic bill.
    - Cancelled clinical events do not generate their corresponding bill.
    - The remaining billing records are filled with normal consultation,
      room, and pharmacy activity.

    Financial rules:
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
    # Number of billing records
    # --------------------------------

    number_of_bills = config[
        "record_counts"
    ]["billing_records"]

    # --------------------------------
    # Historical range
    # --------------------------------

    date_range = config["date_range"]

    historical_start = pd.to_datetime(
        date_range["start_date"]
    ).date()

    historical_end = pd.to_datetime(
        date_range["end_date"]
    ).date()

    # --------------------------------
    # Patient records
    # --------------------------------

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

    # --------------------------------
    # Visit records
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
    # Admission records
    # --------------------------------

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

    # --------------------------------
    # Diagnostic records
    # --------------------------------

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

    # --------------------------------
    # Surgery / procedure records
    # --------------------------------

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

    # --------------------------------
    # Build clinical activity lookups
    # --------------------------------

    diagnostics_by_visit = {}

    for diagnostic in diagnostic_records:
        diagnostics_by_visit.setdefault(
            diagnostic["visit_id"],
            []
        ).append(diagnostic)

    procedures_by_admission = {}

    for procedure in surgery_records:
        procedures_by_admission.setdefault(
            procedure["admission_id"],
            []
        ).append(procedure)

    # --------------------------------
    # Only completed clinical events
    # are eligible for corresponding
    # billing.
    # --------------------------------

    completed_diagnostics = [
        diagnostic
        for diagnostic in diagnostic_records
        if str(diagnostic["test_status"]).strip().lower()
        in {"completed", "complete", "done"}
    ]

    # If the source data uses a different status vocabulary,
    # retain records that are not explicitly cancelled.
    if not completed_diagnostics:
        completed_diagnostics = [
            diagnostic
            for diagnostic in diagnostic_records
            if str(diagnostic["test_status"]).strip().lower()
            not in {"cancelled", "canceled"}
        ]

    completed_procedures = [
        procedure
        for procedure in surgery_records
        if str(procedure["procedure_status"]).strip().lower()
        in {"completed", "complete", "done"}
    ]

    if not completed_procedures:
        completed_procedures = [
            procedure
            for procedure in surgery_records
            if str(procedure["procedure_status"]).strip().lower()
            not in {"cancelled", "canceled"}
        ]

    completed_procedure_events = [
        procedure
        for procedure in completed_procedures
        if procedure["procedure_category"] == "Procedure"
    ]

    completed_surgery_events = [
        procedure
        for procedure in completed_procedures
        if procedure["procedure_category"] == "Surgery"
    ]

    # --------------------------------
    # Build unused event pools.
    #
    # Each clinical event can produce
    # at most one corresponding bill.
    # --------------------------------

    unused_diagnostic_ids = {
        diagnostic["diagnostic_id"]
        for diagnostic in completed_diagnostics
    }

    unused_procedure_ids = {
        procedure["procedure_id"]
        for procedure in completed_procedure_events
    }

    unused_surgery_ids = {
        procedure["procedure_id"]
        for procedure in completed_surgery_events
    }

    # --------------------------------
    # Room daily rates
    # --------------------------------

    room_daily_rates = {
        "General": (1800, 3000),
        "Semi-Private": (3000, 5000),
        "Private": (5000, 8000),
        "ICU": (10000, 18000)
    }

    # --------------------------------
    # Helper functions
    # --------------------------------

    def choose_unused_event(events, unused_ids):
        """
        Select one unused clinical event.

        Returns None when all events in the
        pool have already received a bill.
        """
        if not unused_ids:
            return None

        candidates = [
            event
            for event in events
            if event["procedure_id"]
            if "procedure_id" in event
        ]

        # Diagnostic events use diagnostic_id.
        if events and "diagnostic_id" in events[0]:
            candidates = [
                event
                for event in events
                if event["diagnostic_id"] in unused_ids
            ]

            if not candidates:
                return None

            event = random.choice(candidates)
            unused_ids.remove(event["diagnostic_id"])
            return event

        candidates = [
            event
            for event in events
            if event["procedure_id"] in unused_ids
        ]

        if not candidates:
            return None

        event = random.choice(candidates)
        unused_ids.remove(event["procedure_id"])
        return event

    def choose_unused_diagnostic():
        if not unused_diagnostic_ids:
            return None

        candidates = [
            diagnostic
            for diagnostic in completed_diagnostics
            if diagnostic["diagnostic_id"] in unused_diagnostic_ids
        ]

        if not candidates:
            return None

        diagnostic = random.choice(candidates)

        unused_diagnostic_ids.remove(
            diagnostic["diagnostic_id"]
        )

        return diagnostic

    def choose_unused_procedure():
        if not unused_procedure_ids:
            return None

        candidates = [
            procedure
            for procedure in completed_procedure_events
            if procedure["procedure_id"] in unused_procedure_ids
        ]

        if not candidates:
            return None

        procedure = random.choice(candidates)

        unused_procedure_ids.remove(
            procedure["procedure_id"]
        )

        return procedure

    def choose_unused_surgery():
        if not unused_surgery_ids:
            return None

        candidates = [
            procedure
            for procedure in completed_surgery_events
            if procedure["procedure_id"] in unused_surgery_ids
        ]

        if not candidates:
            return None

        procedure = random.choice(candidates)

        unused_surgery_ids.remove(
            procedure["procedure_id"]
        )

        return procedure

    # --------------------------------
    # Generate billing records
    # --------------------------------

    data = []

    bill_id = 1

    while len(data) < number_of_bills:

        # --------------------------------
        # Determine available event-driven
        # categories.
        # --------------------------------

        available_event_categories = []

        if unused_procedure_ids:
            available_event_categories.append("Procedure")

        if unused_surgery_ids:
            available_event_categories.append("Surgery")

        if unused_diagnostic_ids:
            available_event_categories.append("Diagnostic")

        # --------------------------------
        # Normal billing categories.
        #
        # Event-driven categories are given
        # moderate weights but can never
        # exceed the number of actual events.
        # --------------------------------

        normal_categories = [
            "Consultation",
            "Room",
            "Pharmacy"
        ]

        category_pool = normal_categories + available_event_categories

        if available_event_categories:
            # Clinical event categories receive
            # enough probability to be used naturally,
            # but their pools impose a hard upper bound.
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
                0.50,  # Consultation
                0.25,  # Room
                0.25   # Pharmacy
            ]

        bill_category = random.choices(
            category_pool,
            weights=weights,
            k=1
        )[0]

        # --------------------------------
        # Consultation
        # --------------------------------

        if bill_category == "Consultation":

            visit = random.choice(
                visit_records
            )

            visit_id = visit["visit_id"]
            admission_id = None

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
                visit_date + pd.Timedelta(days=3).to_pytimedelta(),
                historical_end
            )

            bill_date = fake.date_between(
                start_date=bill_start,
                end_date=bill_end
            )

            gross_amount = random.randint(
                500,
                2500
            )

        # --------------------------------
        # Diagnostic
        # --------------------------------

        elif bill_category == "Diagnostic":

            diagnostic = choose_unused_diagnostic()

            # If all diagnostic events have already
            # been billed, fall back to consultation.
            if diagnostic is None:
                bill_category = "Consultation"

                visit = random.choice(
                    visit_records
                )

                visit_id = visit["visit_id"]
                admission_id = None

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
                    visit_date + pd.Timedelta(days=3).to_pytimedelta(),
                    historical_end
                )

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
                admission_id = None

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
                    diagnostic_date + pd.Timedelta(days=1).to_pytimedelta(),
                    historical_end
                )

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

        # --------------------------------
        # Room
        # --------------------------------

        elif bill_category == "Room":

            admission = random.choice(
                admission_records
            )

            visit_id = None
            admission_id = admission["admission_id"]

            patient_id = admission["patient_id"]
            hospital_id = admission["hospital_id"]
            department_id = admission["department_id"]

            admission_date = pd.to_datetime(
                admission["admission_date"]
            ).date()

            discharge_value = admission[
                "discharge_date"
            ]

            if pd.isna(discharge_value):

                discharge_date = min(
                    historical_end,
                    pd.Timestamp.today().date()
                )

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
                historical_end
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
                int(admission["length_of_stay"])
            )

            # A room bill represents a billing segment,
            # not necessarily the entire admission.
            billed_days = random.randint(
                1,
                min(length_of_stay, 7)
            )

            gross_amount = (
                daily_rate * billed_days
            )

        # --------------------------------
        # Procedure
        # --------------------------------

        elif bill_category == "Procedure":

            procedure = choose_unused_procedure()

            # If no unused completed procedure exists,
            # use normal pharmacy billing instead.
            if procedure is None:
                bill_category = "Pharmacy"

                admission = None

                use_admission = (
                    admission_records
                    and random.random() < 0.45
                )

                if use_admission:

                    admission = random.choice(
                        admission_records
                    )

                    visit_id = None
                    admission_id = admission["admission_id"]

                    patient_id = admission["patient_id"]
                    hospital_id = admission["hospital_id"]
                    department_id = admission["department_id"]

                    admission_date = pd.to_datetime(
                        admission["admission_date"]
                    ).date()

                    discharge_value = admission[
                        "discharge_date"
                    ]

                    if pd.isna(discharge_value):

                        discharge_date = min(
                            historical_end,
                            pd.Timestamp.today().date()
                        )

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
                        historical_end
                    )

                    if bill_start > bill_end:
                        bill_start = bill_end

                    bill_date = fake.date_between(
                        start_date=bill_start,
                        end_date=bill_end
                    )

                    length_of_stay = max(
                        1,
                        int(admission["length_of_stay"])
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
                            0.80 + 0.12 * length_of_stay
                        ),
                        2
                    )

                else:

                    visit = random.choice(
                        visit_records
                    )

                    visit_id = visit["visit_id"]
                    admission_id = None

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
                        visit_date + pd.Timedelta(days=3).to_pytimedelta(),
                        historical_end
                    )

                    bill_date = fake.date_between(
                        start_date=bill_start,
                        end_date=bill_end
                    )

                    gross_amount = random.randint(
                        500,
                        10000
                    )

            else:

                admission_id = procedure["admission_id"]
                visit_id = None

                patient_id = procedure["patient_id"]
                hospital_id = procedure["hospital_id"]
                department_id = procedure["department_id"]

                procedure_date = pd.to_datetime(
                    procedure["procedure_date"]
                ).date()

                bill_start = max(
                    procedure_date,
                    historical_start
                )

                bill_end = min(
                    procedure_date + pd.Timedelta(days=1).to_pytimedelta(),
                    historical_end
                )

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

        # --------------------------------
        # Surgery
        # --------------------------------

        elif bill_category == "Surgery":

            surgery = choose_unused_surgery()

            # If no unused completed surgery exists,
            # use normal pharmacy billing instead.
            if surgery is None:
                bill_category = "Pharmacy"

                use_admission = (
                    admission_records
                    and random.random() < 0.45
                )

                if use_admission:

                    admission = random.choice(
                        admission_records
                    )

                    visit_id = None
                    admission_id = admission["admission_id"]

                    patient_id = admission["patient_id"]
                    hospital_id = admission["hospital_id"]
                    department_id = admission["department_id"]

                    admission_date = pd.to_datetime(
                        admission["admission_date"]
                    ).date()

                    discharge_value = admission[
                        "discharge_date"
                    ]

                    if pd.isna(discharge_value):

                        discharge_date = min(
                            historical_end,
                            pd.Timestamp.today().date()
                        )

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
                        historical_end
                    )

                    if bill_start > bill_end:
                        bill_start = bill_end

                    bill_date = fake.date_between(
                        start_date=bill_start,
                        end_date=bill_end
                    )

                    length_of_stay = max(
                        1,
                        int(admission["length_of_stay"])
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
                            0.80 + 0.12 * length_of_stay
                        ),
                        2
                    )

                else:

                    visit = random.choice(
                        visit_records
                    )

                    visit_id = visit["visit_id"]
                    admission_id = None

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
                        visit_date + pd.Timedelta(days=3).to_pytimedelta(),
                        historical_end
                    )

                    bill_date = fake.date_between(
                        start_date=bill_start,
                        end_date=bill_end
                    )

                    gross_amount = random.randint(
                        500,
                        10000
                    )

            else:

                admission_id = surgery["admission_id"]
                visit_id = None

                patient_id = surgery["patient_id"]
                hospital_id = surgery["hospital_id"]
                department_id = surgery["department_id"]

                procedure_date = pd.to_datetime(
                    surgery["procedure_date"]
                ).date()

                bill_start = max(
                    procedure_date,
                    historical_start
                )

                bill_end = min(
                    procedure_date + pd.Timedelta(days=1).to_pytimedelta(),
                    historical_end
                )

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

        # --------------------------------
        # Pharmacy
        # --------------------------------

        else:

            use_admission = (
                admission_records
                and random.random() < 0.45
            )

            if use_admission:

                admission = random.choice(
                    admission_records
                )

                visit_id = None
                admission_id = admission["admission_id"]

                patient_id = admission["patient_id"]
                hospital_id = admission["hospital_id"]
                department_id = admission["department_id"]

                admission_date = pd.to_datetime(
                    admission["admission_date"]
                ).date()

                discharge_value = admission[
                    "discharge_date"
                ]

                if pd.isna(discharge_value):

                    discharge_date = min(
                        historical_end,
                        pd.Timestamp.today().date()
                    )

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
                    historical_end
                )

                if bill_start > bill_end:
                    bill_start = bill_end

                bill_date = fake.date_between(
                    start_date=bill_start,
                    end_date=bill_end
                )

                length_of_stay = max(
                    1,
                    int(admission["length_of_stay"])
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
                        0.80 + 0.12 * length_of_stay
                    ),
                    2
                )

            else:

                visit = random.choice(
                    visit_records
                )

                visit_id = visit["visit_id"]
                admission_id = None

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
                    visit_date + pd.Timedelta(days=3).to_pytimedelta(),
                    historical_end
                )

                bill_date = fake.date_between(
                    start_date=bill_start,
                    end_date=bill_end
                )

                gross_amount = random.randint(
                    500,
                    10000
                )

        # --------------------------------
        # Patient insurance
        # --------------------------------

        patient = patient_lookup[
            patient_id
        ]

        insurance_type = patient[
            "insurance_type"
        ]

        # --------------------------------
        # Discount
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
        # Total
        # --------------------------------

        total_amount = round(
            gross_amount - discount_amount,
            2
        )

        # --------------------------------
        # Insurance contribution
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
    # DataFrame
    # --------------------------------

    df = pd.DataFrame(data)

    # --------------------------------
    # Schema-defined column order
    # --------------------------------

    column_order = [
        column["name"]
        for column in schema["columns"]
    ]

    df = df[column_order]

    return df
