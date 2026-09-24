import json
import random
from datetime import date

import pandas as pd
from faker import Faker

from utils.id_generator import generate_id


fake = Faker("en_IN")


# ========================================
# Department → Specialization mapping
# ========================================

SPECIALIZATION_MAP = {
    "General Medicine": "General Physician",
    "Emergency & Critical Care": "Emergency Medicine",
    "Pediatrics": "Pediatrician",
    "Cardiology": "Cardiologist",
    "Orthopedics": "Orthopedic Specialist",
    "Obstetrics & Gynaecology": "Obstetrician & Gynaecologist",
    "Pulmonology": "Pulmonologist",
    "Gastroenterology": "Gastroenterologist",
    "Neurology": "Neurologist",
    "Nephrology": "Nephrologist",
    "Urology": "Urologist",
    "General Surgery": "General Surgeon",
    "Oncology": "Oncologist",
    "ENT": "ENT Specialist",
    "Dermatology": "Dermatologist",
}


# ========================================
# Base consultation fees
# ========================================

SPECIALIZATION_FEES = {
    "General Physician": (500, 1200),
    "Emergency Medicine": (800, 1800),
    "Pediatrician": (700, 1500),
    "Cardiologist": (1200, 2500),
    "Orthopedic Specialist": (1000, 2200),
    "Obstetrician & Gynaecologist": (900, 2000),
    "Pulmonologist": (1000, 2200),
    "Gastroenterologist": (1100, 2400),
    "Neurologist": (1200, 2500),
    "Nephrologist": (1100, 2300),
    "Urologist": (1000, 2200),
    "General Surgeon": (1000, 2300),
    "Oncologist": (1500, 2500),
    "ENT Specialist": (700, 1600),
    "Dermatologist": (600, 1500),
}


# ========================================
# Generate doctors
# ========================================

def generate_doctors(
    schema_path,
    hospital_df,
    department_df,
    config
):
    """
    Generate synthetic doctor master data.

    Guarantees:
    - Configured number of doctors is generated.
    - Every doctor belongs to a valid hospital.
    - Every doctor belongs to a department in that hospital.
    - Every department receives at least one doctor.
    - Doctor IDs use the centralized ID generator.
    - Specialization matches department.
    - Experience is between 2 and 30 years.
    - Consultation fee is between 500 and 2500.
    """

    # ========================================
    # Read doctor schema
    # ========================================

    with open(
        schema_path,
        "r",
        encoding="utf-8"
    ) as file:

        schema = json.load(file)

    # ========================================
    # Get doctor count
    # ========================================

    number_of_doctors = config[
        "record_counts"
    ]["doctors"]

    # ========================================
    # Validate input data
    # ========================================

    if hospital_df.empty:
        raise ValueError(
            "Hospital DataFrame is empty."
        )

    if department_df.empty:
        raise ValueError(
            "Department DataFrame is empty."
        )

    number_of_departments = len(
        department_df
    )

    if number_of_doctors < number_of_departments:
        raise ValueError(
            f"Cannot guarantee at least one doctor "
            f"per department. "
            f"Doctors: {number_of_doctors}, "
            f"Departments: {number_of_departments}"
        )

    # ========================================
    # Validate department → hospital
    # ========================================

    valid_hospital_ids = set(
        hospital_df["hospital_id"]
    )

    invalid_hospitals = (
        set(department_df["hospital_id"])
        - valid_hospital_ids
    )

    if invalid_hospitals:
        raise ValueError(
            "Departments reference invalid "
            f"hospital IDs: {invalid_hospitals}"
        )

    # ========================================
    # Validate all department names
    # have specialization mappings
    # ========================================

    department_names = set(
        department_df["department_name"]
    )

    missing_specializations = (
        department_names
        - set(SPECIALIZATION_MAP.keys())
    )

    if missing_specializations:
        raise ValueError(
            "No specialization mapping exists for "
            f"departments: {missing_specializations}"
        )

    # ========================================
    # Prepare department records
    # ========================================

    department_records = department_df[
        [
            "department_id",
            "department_name",
            "hospital_id"
        ]
    ].to_dict("records")

    # ========================================
    # Generate doctors
    # ========================================

    doctors = []

    # ========================================
    # STEP 1
    # Guarantee one doctor per department
    # ========================================

    for department in department_records:

        department_id = department[
            "department_id"
        ]

        department_name = department[
            "department_name"
        ]

        hospital_id = department[
            "hospital_id"
        ]

        specialization = SPECIALIZATION_MAP[
            department_name
        ]

        doctor = _create_doctor(
            hospital_id=hospital_id,
            department_id=department_id,
            specialization=specialization
        )

        doctors.append(doctor)

    # ========================================
    # STEP 2
    # Generate remaining doctors
    # ========================================

    remaining_doctors = (
        number_of_doctors
        - len(doctors)
    )

    for _ in range(remaining_doctors):

        department = random.choice(
            department_records
        )

        department_id = department[
            "department_id"
        ]

        department_name = department[
            "department_name"
        ]

        hospital_id = department[
            "hospital_id"
        ]

        specialization = SPECIALIZATION_MAP[
            department_name
        ]

        doctor = _create_doctor(
            hospital_id=hospital_id,
            department_id=department_id,
            specialization=specialization
        )

        doctors.append(doctor)

    # ========================================
    # Create DataFrame
    # ========================================

    doctor_df = pd.DataFrame(
        doctors,
        columns=[
            "doctor_id",
            "doctor_name",
            "specialization",
            "department_id",
            "hospital_id",
            "experience_years",
            "consultation_fee",
            "joining_date"
        ]
    )

    # ========================================
    # Validate count
    # ========================================

    if len(doctor_df) != number_of_doctors:
        raise ValueError(
            f"Expected {number_of_doctors} "
            f"doctors but generated "
            f"{len(doctor_df)}."
        )

    # ========================================
    # Validate doctor IDs
    # ========================================

    if doctor_df[
        "doctor_id"
    ].duplicated().any():

        raise ValueError(
            "Duplicate doctor IDs generated."
        )

    if doctor_df[
        "doctor_id"
    ].isna().any():

        raise ValueError(
            "Doctor ID contains null values."
        )

    # ========================================
    # Validate hospital relationships
    # ========================================

    invalid_doctor_hospitals = (
        set(doctor_df["hospital_id"])
        - valid_hospital_ids
    )

    if invalid_doctor_hospitals:
        raise ValueError(
            "Doctors reference invalid "
            f"hospital IDs: "
            f"{invalid_doctor_hospitals}"
        )

    # ========================================
    # Validate department relationships
    # ========================================

    valid_department_pairs = set(
        zip(
            department_df["department_id"],
            department_df["hospital_id"]
        )
    )

    doctor_department_pairs = set(
        zip(
            doctor_df["department_id"],
            doctor_df["hospital_id"]
        )
    )

    invalid_pairs = (
        doctor_department_pairs
        - valid_department_pairs
    )

    if invalid_pairs:
        raise ValueError(
            "Doctors reference department/"
            "hospital combinations that do "
            f"not exist: {invalid_pairs}"
        )

    # ========================================
    # Validate every department has doctor
    # ========================================

    doctor_department_ids = set(
        doctor_df["department_id"]
    )

    missing_departments = (
        set(department_df["department_id"])
        - doctor_department_ids
    )

    if missing_departments:
        raise ValueError(
            "These departments have no doctors: "
            f"{missing_departments}"
        )

    # ========================================
    # Validate specialization
    # ========================================

    specialization_failures = 0

    department_lookup = (
        department_df
        .set_index("department_id")
        ["department_name"]
        .to_dict()
    )

    for _, row in doctor_df.iterrows():

        department_name = department_lookup.get(
            row["department_id"]
        )

        expected_specialization = (
            SPECIALIZATION_MAP.get(
                department_name
            )
        )

        if (
            expected_specialization
            != row["specialization"]
        ):

            specialization_failures += 1

    if specialization_failures > 0:
        raise ValueError(
            "Doctor specialization does not "
            "match department for "
            f"{specialization_failures} doctors."
        )

    # ========================================
    # Validate consultation fees
    # ========================================

    if (
        doctor_df["consultation_fee"] < 500
    ).any():

        raise ValueError(
            "Doctor consultation fee cannot "
            "be below 500."
        )

    if (
        doctor_df["consultation_fee"] > 2500
    ).any():

        raise ValueError(
            "Doctor consultation fee cannot "
            "exceed 2500."
        )

    # ========================================
    # Validate experience
    # ========================================

    if (
        doctor_df["experience_years"] < 2
    ).any():

        raise ValueError(
            "Doctor experience cannot "
            "be below 2 years."
        )

    if (
        doctor_df["experience_years"] > 30
    ).any():

        raise ValueError(
            "Doctor experience cannot "
            "exceed 30 years."
        )

    # ========================================
    # Validate joining dates
    # ========================================

    if doctor_df[
        "joining_date"
    ].isna().any():

        raise ValueError(
            "Doctor joining date contains "
            "null values."
        )

    return doctor_df


# ========================================
# Doctor creation helper
# ========================================

def _create_doctor(
    hospital_id,
    department_id,
    specialization
):
    """
    Create one synthetic doctor record.
    """

    # ========================================
    # Experience
    # ========================================

    # Validator requirement:
    # 2 to 30 years

    experience_years = random.randint(
        2,
        30
    )

    # ========================================
    # Joining year
    # ========================================

    current_year = date.today().year

    earliest_joining_year = (
        current_year
        - experience_years
        - 1
    )

    latest_joining_year = (
        current_year
        - experience_years
    )

    joining_year = random.randint(
        earliest_joining_year,
        latest_joining_year
    )

    joining_date = date(
        joining_year,
        random.randint(1, 12),
        random.randint(1, 28)
    )

    # ========================================
    # Consultation fee
    # ========================================

    fee_range = SPECIALIZATION_FEES.get(
        specialization,
        (700, 1800)
    )

    base_fee = random.randint(
        fee_range[0],
        fee_range[1]
    )

    # Experienced doctors tend to charge more.

    experience_multiplier = (
        1
        + min(experience_years, 20)
        * 0.015
    )

    consultation_fee = round(
        base_fee
        * experience_multiplier
    )

    # ========================================
    # Keep within validator range
    # ₹500 – ₹2500
    # ========================================

    consultation_fee = max(
        500,
        min(
            consultation_fee,
            2500
        )
    )

    # ========================================
    # Doctor name
    # ========================================

    doctor_name = (
        f"Dr. {fake.first_name()} "
        f"{fake.last_name()}"
    )

    # ========================================
    # Return doctor
    # ========================================

    return {
        "doctor_id": generate_id(
            "doctor"
        ),
        "doctor_name": doctor_name,
        "specialization": specialization,
        "department_id": department_id,
        "hospital_id": hospital_id,
        "experience_years": experience_years,
        "consultation_fee": consultation_fee,
        "joining_date": joining_date.isoformat()
    }