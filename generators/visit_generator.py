import json
import random

import pandas as pd
from faker import Faker

from utils.id_generator import generate_id


fake = Faker()


def generate_visits(
    schema_path,
    patient_df,
    hospital_df,
    department_df,
    doctor_df,
    config
):
    """
    Generate synthetic patient visits while maintaining
    valid patient, hospital, department and doctor relationships.

    Visit activity is influenced by:
    - Hospital activity
    - Department activity
    - Doctor workload
    - Monthly/seasonal activity
    - Day-of-week activity

    Visit dates:
    - Stay inside the configured historical period
    - Cannot occur before patient registration

    Relationships:
    - Visit patient_id -> Patient
    - Visit hospital_id -> Hospital
    - Visit department_id -> Department
    - Visit doctor_id -> Doctor
    - Doctor department_id == Visit department_id
    - Doctor hospital_id == Visit hospital_id
    """

    # ========================================
    # Read visit schema
    # ========================================

    with open(
        schema_path,
        "r",
        encoding="utf-8"
    ) as file:
        schema = json.load(file)

    # ========================================
    # Number of visits
    # ========================================

    number_of_visits = config[
        "record_counts"
    ]["visits"]

    # ========================================
    # Historical date range
    # ========================================

    historical_start = pd.to_datetime(
        config["date_range"]["start_date"]
    ).date()

    historical_end = pd.to_datetime(
        config["date_range"]["end_date"]
    ).date()

    if historical_start > historical_end:
        raise ValueError(
            "Historical start date cannot be "
            "after historical end date."
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
    # Validate hospital configuration
    # ========================================

    hospital_names = set(
        hospital_df["hospital_name"]
    )

    configured_hospital_names = set(
        hospital_activity_weights.keys()
    )

    missing_hospitals = (
        hospital_names
        - configured_hospital_names
    )

    if missing_hospitals:

        raise ValueError(
            "Missing hospital activity weights for: "
            + ", ".join(
                sorted(missing_hospitals)
            )
        )

    # ========================================
    # Validate department configuration
    # ========================================

    department_names = set(
        department_df["department_name"]
    )

    configured_department_names = set(
        department_activity_weights.keys()
    )

    missing_departments = (
        department_names
        - configured_department_names
    )

    if missing_departments:

        raise ValueError(
            "Missing department activity weights for: "
            + ", ".join(
                sorted(missing_departments)
            )
        )

    # ========================================
    # Doctor workload configuration
    # ========================================

    high_workload = doctor_workload_config.get(
        "high",
        1.30
    )

    medium_workload = doctor_workload_config.get(
        "medium",
        1.00
    )

    low_workload = doctor_workload_config.get(
        "low",
        0.70
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
    # Prepare patient records
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
    # Prepare doctor records
    # ========================================

    doctor_records = doctor_df[
        [
            "doctor_id",
            "hospital_id",
            "department_id",
            "consultation_fee"
        ]
    ].to_dict("records")

    if not doctor_records:

        raise ValueError(
            "No doctor records available."
        )

    # ========================================
    # Validate doctor relationships
    # ========================================

    hospital_lookup = {
        row["hospital_id"]: row["hospital_name"]
        for _, row in hospital_df.iterrows()
    }

    department_lookup = {
        row["department_id"]: {
            "department_name": row["department_name"],
            "hospital_id": row["hospital_id"]
        }
        for _, row in department_df.iterrows()
    }

    for doctor in doctor_records:

        doctor_hospital_id = doctor[
            "hospital_id"
        ]

        doctor_department_id = doctor[
            "department_id"
        ]

        if doctor_hospital_id not in hospital_lookup:

            raise ValueError(
                f"Doctor {doctor['doctor_id']} "
                f"references unknown hospital "
                f"{doctor_hospital_id}."
            )

        if doctor_department_id not in department_lookup:

            raise ValueError(
                f"Doctor {doctor['doctor_id']} "
                f"references unknown department "
                f"{doctor_department_id}."
            )

        department = department_lookup[
            doctor_department_id
        ]

        if (
            department["hospital_id"]
            != doctor_hospital_id
        ):

            raise ValueError(
                f"Doctor {doctor['doctor_id']} "
                "has a department belonging to "
                "another hospital."
            )

    # ========================================
    # Assign workload level to doctors
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
    # Create doctor selection weights
    #
    # Hospital activity
    # × Department activity
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

        hospital_weight = (
            float(
                hospital_activity_weights[
                    hospital_name
                ]
            )
        )

        department_weight = (
            float(
                department_activity_weights[
                    department_name
                ]
            )
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
                "Activity weights must be "
                "greater than zero."
            )

        doctor_selection_weights.append(
            combined_weight
        )

    # ========================================
    # Maximum possible date weight
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

    if maximum_date_weight <= 0:

        raise ValueError(
            "Monthly/day-of-week activity "
            "weights must be greater than zero."
        )

    # ========================================
    # Weighted date generator
    # ========================================

    def generate_weighted_date(
        start_date,
        end_date
    ):

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
    # Generate visits
    # ========================================

    data = []

    for _ in range(number_of_visits):

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
        # Visit date cannot occur before
        # patient registration.
        # ------------------------------------

        visit_start = max(
            registration_date,
            historical_start
        )

        visit_end = historical_end

        if visit_start > visit_end:
            visit_start = visit_end

        visit_date = generate_weighted_date(
            visit_start,
            visit_end
        )

        # ------------------------------------
        # Select doctor
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
        # Visit type
        # ------------------------------------

        visit_type = random.choices(
            [
                "OP",
                "IP",
                "Emergency"
            ],
            weights=[
                0.70,
                0.20,
                0.10
            ],
            k=1
        )[0]

        # ------------------------------------
        # Visit status
        # ------------------------------------

        visit_status = random.choices(
            [
                "Completed",
                "Cancelled"
            ],
            weights=[
                0.95,
                0.05
            ],
            k=1
        )[0]

        # ------------------------------------
        # Doctor's actual consultation fee
        # ------------------------------------

        consultation_fee = doctor[
            "consultation_fee"
        ]

        # ------------------------------------
        # Visit source
        # ------------------------------------

        source = random.choices(
            [
                "Walk-in",
                "Appointment",
                "Referral"
            ],
            weights=[
                0.45,
                0.45,
                0.10
            ],
            k=1
        )[0]

        # ------------------------------------
        # Generate six-character Visit ID
        # ------------------------------------

        visit_id = generate_id(
            "visit"
        )

        # ------------------------------------
        # Add visit
        # ------------------------------------

        data.append({
            "visit_id": visit_id,
            "patient_id": patient_id,
            "hospital_id": hospital_id,
            "department_id": department_id,
            "doctor_id": doctor_id,
            "visit_date": visit_date.isoformat(),
            "visit_type": visit_type,
            "visit_status": visit_status,
            "consultation_fee": consultation_fee,
            "source": source
        })

    # ========================================
    # Create DataFrame
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

    if len(df) != number_of_visits:

        raise ValueError(
            f"Expected {number_of_visits} visits "
            f"but generated {len(df)}."
        )

    if df["visit_id"].duplicated().any():

        raise ValueError(
            "Duplicate visit IDs generated."
        )

    # ----------------------------------------
    # Validate patient IDs
    # ----------------------------------------

    valid_patient_ids = set(
        patient_df["patient_id"]
    )

    invalid_patients = (
        set(df["patient_id"])
        - valid_patient_ids
    )

    if invalid_patients:

        raise ValueError(
            "Visits contain invalid patient IDs: "
            f"{invalid_patients}"
        )

    # ----------------------------------------
    # Validate doctor IDs
    # ----------------------------------------

    valid_doctor_ids = set(
        doctor_df["doctor_id"]
    )

    invalid_doctors = (
        set(df["doctor_id"])
        - valid_doctor_ids
    )

    if invalid_doctors:

        raise ValueError(
            "Visits contain invalid doctor IDs: "
            f"{invalid_doctors}"
        )

    # ----------------------------------------
    # Validate doctor → visit relationships
    # ----------------------------------------

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

    for row in df.itertuples(index=False):

        doctor = doctor_lookup[
            row.doctor_id
        ]

        if (
            doctor["hospital_id"]
            != row.hospital_id
        ):

            raise ValueError(
                f"Visit {row.visit_id}: "
                "doctor hospital does not "
                "match visit hospital."
            )

        if (
            doctor["department_id"]
            != row.department_id
        ):

            raise ValueError(
                f"Visit {row.visit_id}: "
                "doctor department does not "
                "match visit department."
            )

    # ========================================
    # Return
    # ========================================

    return df