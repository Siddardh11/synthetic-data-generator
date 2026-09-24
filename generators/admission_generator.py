import json
import random
from datetime import date, timedelta

import pandas as pd
from faker import Faker

from utils.id_generator import generate_id


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
    Generate synthetic inpatient admissions.

    Maintains:
    - Patient registration -> admission date relationship
    - Doctor -> department -> hospital relationship
    - Hospital activity variation
    - Department activity variation
    - Doctor workload variation
    - Monthly/seasonal variation
    - Day-of-week variation
    - Planned vs Emergency admission patterns
    - Ward type correlation with admission type
    - Ward-dependent length of stay
    - Correct discharge dates
    - Correct length of stay
    - Realistic ongoing admissions
    """

    # ========================================
    # Read schema
    # ========================================

    with open(
        schema_path,
        "r",
        encoding="utf-8"
    ) as file:
        schema = json.load(file)

    # ========================================
    # Record count
    # ========================================

    number_of_admissions = config[
        "record_counts"
    ]["admissions"]

    # ========================================
    # Historical date range
    # ========================================

    historical_start = date.fromisoformat(
        config["date_range"]["start_date"]
    )

    historical_end = date.fromisoformat(
        config["date_range"]["end_date"]
    )

    # Never generate future dates.
    effective_end = min(
        historical_end,
        date.today()
    )

    if historical_start > effective_end:

        raise ValueError(
            "Historical start date cannot be "
            "after the effective end date."
        )

    # ========================================
    # Variation configuration
    # ========================================

    variation = config.get(
        "variation",
        {}
    )

    hospital_activity_weights = variation.get(
        "hospital_activity_weights",
        {}
    )

    department_activity_weights = variation.get(
        "department_activity_weights",
        {}
    )

    doctor_workload_config = variation.get(
        "doctor_workload",
        {}
    )

    monthly_activity_weights = variation.get(
        "monthly_activity_weights",
        {}
    )

    day_of_week_activity_weights = variation.get(
        "day_of_week_activity_weights",
        {}
    )

    # ========================================
    # Validate hospital weights
    # ========================================

    hospital_lookup = {
        row["hospital_id"]: row["hospital_name"]
        for _, row in hospital_df.iterrows()
    }

    missing_hospital_weights = (
        set(hospital_lookup.values())
        - set(hospital_activity_weights.keys())
    )

    if missing_hospital_weights:

        raise ValueError(
            "Missing hospital activity weights for: "
            + ", ".join(
                sorted(missing_hospital_weights)
            )
        )

    # ========================================
    # Department lookup
    # ========================================

    department_lookup = {
        row["department_id"]: {
            "department_name": row["department_name"],
            "hospital_id": row["hospital_id"]
        }
        for _, row in department_df.iterrows()
    }

    missing_department_weights = (
        {
            value["department_name"]
            for value in department_lookup.values()
        }
        - set(department_activity_weights.keys())
    )

    if missing_department_weights:

        raise ValueError(
            "Missing department activity weights for: "
            + ", ".join(
                sorted(missing_department_weights)
            )
        )

    # ========================================
    # Doctor workload configuration
    # ========================================

    high_workload = float(
        doctor_workload_config.get(
            "high",
            1.30
        )
    )

    medium_workload = float(
        doctor_workload_config.get(
            "medium",
            1.00
        )
    )

    low_workload = float(
        doctor_workload_config.get(
            "low",
            0.70
        )
    )

    workload_distribution = (
        doctor_workload_config.get(
            "distribution",
            {
                "high": 0.20,
                "medium": 0.60,
                "low": 0.20
            }
        )
    )

    workload_labels = [
        "high",
        "medium",
        "low"
    ]

    workload_probabilities = [
        workload_distribution["high"],
        workload_distribution["medium"],
        workload_distribution["low"]
    ]

    workload_weights = {
        "high": high_workload,
        "medium": medium_workload,
        "low": low_workload
    }

    # ========================================
    # Prepare patients
    # ========================================

    patient_records = patient_df[
        [
            "patient_id",
            "registration_date"
        ]
    ].to_dict("records")

    if not patient_records:

        raise ValueError(
            "No patient records available."
        )

    # ========================================
    # Prepare doctors
    # ========================================

    doctor_records = doctor_df[
        [
            "doctor_id",
            "hospital_id",
            "department_id"
        ]
    ].to_dict("records")

    if not doctor_records:

        raise ValueError(
            "No doctor records available."
        )

    # ========================================
    # Validate doctor relationships
    # ========================================

    for doctor in doctor_records:

        doctor_id = doctor["doctor_id"]
        hospital_id = doctor["hospital_id"]
        department_id = doctor["department_id"]

        if hospital_id not in hospital_lookup:

            raise ValueError(
                f"Doctor {doctor_id} references "
                f"unknown hospital {hospital_id}."
            )

        if department_id not in department_lookup:

            raise ValueError(
                f"Doctor {doctor_id} references "
                f"unknown department {department_id}."
            )

        department = department_lookup[
            department_id
        ]

        if department["hospital_id"] != hospital_id:

            raise ValueError(
                f"Doctor {doctor_id} has a department "
                "belonging to another hospital."
            )

    # ========================================
    # Assign doctor workload
    # ========================================

    for doctor in doctor_records:

        workload_level = random.choices(
            workload_labels,
            weights=workload_probabilities,
            k=1
        )[0]

        doctor["workload_level"] = (
            workload_level
        )

        doctor["workload_weight"] = (
            workload_weights[
                workload_level
            ]
        )

    # ========================================
    # Doctor selection weights
    #
    # Hospital
    # × Department
    # × Doctor workload
    # ========================================

    doctor_selection_weights = []

    for doctor in doctor_records:

        hospital_name = hospital_lookup[
            doctor["hospital_id"]
        ]

        department_name = department_lookup[
            doctor["department_id"]
        ]["department_name"]

        hospital_weight = float(
            hospital_activity_weights[
                hospital_name
            ]
        )

        department_weight = float(
            department_activity_weights[
                department_name
            ]
        )

        doctor_weight = float(
            doctor["workload_weight"]
        )

        combined_weight = (
            hospital_weight
            * department_weight
            * doctor_weight
        )

        if combined_weight <= 0:

            raise ValueError(
                "Hospital, department and doctor "
                "weights must be greater than zero."
            )

        doctor_selection_weights.append(
            combined_weight
        )

    # ========================================
    # Maximum date weight
    # ========================================

    maximum_month_weight = max(
        (
            float(weight)
            for weight
            in monthly_activity_weights.values()
        ),
        default=1.0
    )

    maximum_weekday_weight = max(
        (
            float(weight)
            for weight
            in day_of_week_activity_weights.values()
        ),
        default=1.0
    )

    maximum_date_weight = (
        maximum_month_weight
        * maximum_weekday_weight
    )

    # ========================================
    # Weighted admission date
    # ========================================

    def generate_weighted_date(
        start_date,
        end_date
    ):
        """
        Generate a date using:

        Monthly activity
        ×
        Day-of-week activity
        """

        if start_date > end_date:
            return end_date

        while True:

            candidate_date = fake.date_between(
                start_date=start_date,
                end_date=end_date
            )

            month_weight = float(
                monthly_activity_weights.get(
                    str(candidate_date.month),
                    1.0
                )
            )

            weekday_name = (
                candidate_date.strftime("%A")
            )

            weekday_weight = float(
                day_of_week_activity_weights.get(
                    weekday_name,
                    1.0
                )
            )

            combined_weight = (
                month_weight
                * weekday_weight
            )

            acceptance_probability = (
                combined_weight
                / maximum_date_weight
            )

            if random.random() <= (
                acceptance_probability
            ):
                return candidate_date

    # ========================================
    # Diagnosis categories
    # ========================================

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

    # ========================================
    # Generate admissions
    # ========================================

    data = []

    for _ in range(number_of_admissions):

        # ------------------------------------
        # Select patient
        # ------------------------------------

        patient = random.choice(
            patient_records
        )

        patient_id = patient[
            "patient_id"
        ]

        registration_date = pd.to_datetime(
            patient["registration_date"]
        ).date()

        # ------------------------------------
        # Select doctor
        #
        # Doctor determines:
        # hospital + department
        # ------------------------------------

        doctor = random.choices(
            doctor_records,
            weights=doctor_selection_weights,
            k=1
        )[0]

        doctor_id = doctor[
            "doctor_id"
        ]

        hospital_id = doctor[
            "hospital_id"
        ]

        department_id = doctor[
            "department_id"
        ]

        # ------------------------------------
        # Admission type
        # ------------------------------------

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

        # ------------------------------------
        # Ward type
        #
        # Emergency:
        # higher ICU probability
        #
        # Planned:
        # lower ICU probability
        # ------------------------------------

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

        # ------------------------------------
        # Diagnosis
        # ------------------------------------

        diagnosis_category = random.choice(
            diagnosis_categories
        )

        # ------------------------------------
        # Admission status
        # ------------------------------------

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

        # ------------------------------------
        # Earliest possible admission
        # ------------------------------------

        admission_start = max(
            registration_date,
            historical_start
        )

        # ====================================
        # Ongoing admission
        # ====================================

        if admission_status == "Ongoing":

            recent_start = (
                effective_end
                - timedelta(days=30)
            )

            admission_start = max(
                admission_start,
                recent_start
            )

            if admission_start > effective_end:

                admission_start = effective_end

            admission_date = (
                generate_weighted_date(
                    admission_start,
                    effective_end
                )
            )

        # ====================================
        # Discharged admission
        # ====================================

        else:

            if admission_start > effective_end:

                admission_start = effective_end

            admission_date = (
                generate_weighted_date(
                    admission_start,
                    effective_end
                )
            )

        # ====================================
        # Length of stay
        # ====================================

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

        # ====================================
        # Discharge logic
        # ====================================

        if admission_status == "Discharged":

            discharge_date = (
                admission_date
                + timedelta(days=stay_days)
            )

            # Do not exceed configured range.
            discharge_date = min(
                discharge_date,
                historical_end
            )

            # Do not generate future discharge dates.
            discharge_date = min(
                discharge_date,
                date.today()
            )

            # --------------------------------
            # Exact LOS calculation
            # --------------------------------

            length_of_stay = (
                discharge_date
                - admission_date
            ).days

            # --------------------------------
            # Safety check
            # --------------------------------

            if length_of_stay < 0:

                discharge_date = admission_date

                length_of_stay = 0

        # ====================================
        # Ongoing admission
        # ====================================

        else:

            discharge_date = None

            # For ongoing admissions:
            length_of_stay = (
                date.today()
                - admission_date
            ).days

            if length_of_stay < 0:

                length_of_stay = 0

        # ====================================
        # Generate unique admission ID
        # ====================================

        admission_id = generate_id(
            "admission"
        )

        # ====================================
        # Create record
        # ====================================

        data.append({
            "admission_id": admission_id,
            "patient_id": patient_id,
            "hospital_id": hospital_id,
            "department_id": department_id,
            "doctor_id": doctor_id,
            "admission_date": (
                admission_date.isoformat()
            ),
            "discharge_date": (
                discharge_date.isoformat()
                if discharge_date is not None
                else None
            ),
            "admission_type": admission_type,
            "ward_type": ward_type,
            "diagnosis_category": diagnosis_category,
            "length_of_stay": length_of_stay,
            "admission_status": admission_status
        })

    # ========================================
    # DataFrame
    # ========================================

    df = pd.DataFrame(data)

    # ========================================
    # Schema column order
    # ========================================

    column_order = [
        column["name"]
        for column in schema["columns"]
    ]

    df = df[column_order]

    # ========================================
    # Final validation
    # ========================================

    if len(df) != number_of_admissions:

        raise ValueError(
            f"Expected {number_of_admissions} "
            f"admissions but generated "
            f"{len(df)}."
        )

    # ========================================
    # Duplicate ID validation
    # ========================================

    if df["admission_id"].duplicated().any():

        raise ValueError(
            "Duplicate admission IDs generated."
        )

    # ========================================
    # Patient relationship validation
    # ========================================

    valid_patient_ids = set(
        patient_df["patient_id"]
    )

    invalid_patient_ids = (
        set(df["patient_id"])
        - valid_patient_ids
    )

    if invalid_patient_ids:

        raise ValueError(
            "Admissions contain invalid "
            f"patient IDs: {invalid_patient_ids}"
        )

    # ========================================
    # Doctor relationship validation
    # ========================================

    doctor_lookup = (
        doctor_df[
            [
                "doctor_id",
                "hospital_id",
                "department_id"
            ]
        ]
        .set_index("doctor_id")
        .to_dict("index")
    )

    for row in df.itertuples(
        index=False
    ):

        doctor = doctor_lookup[
            row.doctor_id
        ]

        # ------------------------------------
        # Doctor hospital must match
        # admission hospital
        # ------------------------------------

        if (
            doctor["hospital_id"]
            != row.hospital_id
        ):

            raise ValueError(
                f"Admission {row.admission_id}: "
                "doctor hospital does not match "
                "admission hospital."
            )

        # ------------------------------------
        # Doctor department must match
        # admission department
        # ------------------------------------

        if (
            doctor["department_id"]
            != row.department_id
        ):

            raise ValueError(
                f"Admission {row.admission_id}: "
                "doctor department does not match "
                "admission department."
            )

    # ========================================
    # Date validation
    # ========================================

    admission_dates = pd.to_datetime(
        df["admission_date"]
    )

    discharge_dates = pd.to_datetime(
        df["discharge_date"],
        errors="coerce"
    )

    invalid_discharge_dates = (
        discharge_dates.notna()
        & (
            discharge_dates
            < admission_dates
        )
    )

    if invalid_discharge_dates.any():

        raise ValueError(
            "Found discharge dates before "
            "admission dates."
        )

    # ========================================
    # LOS validation
    # ========================================

    for row in df.itertuples(
        index=False
    ):

        # IMPORTANT:
        # Use pd.to_datetime instead of
        # date.fromisoformat so this validation
        # works whether pandas returns a string,
        # Timestamp, or date-like value.

        admission_date = pd.to_datetime(
            row.admission_date
        ).date()

        if pd.notna(
            row.discharge_date
        ):

            discharge_date = pd.to_datetime(
                row.discharge_date
            ).date()

            expected_los = (
                discharge_date
                - admission_date
            ).days

        else:

            expected_los = (
                date.today()
                - admission_date
            ).days

        if row.length_of_stay != expected_los:

            raise ValueError(
                f"Admission {row.admission_id}: "
                "length_of_stay does not match "
                "the admission/discharge dates."
            )

    # ========================================
    # Return
    # ========================================

    return df