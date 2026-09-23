import json

from generators.hospital_generator import generate_hospitals
from generators.department_generator import generate_departments
from generators.doctor_generator import generate_doctors
from generators.patient_generator import generate_patients


# --------------------------------
# Load configuration
# --------------------------------

with open(
    "config/config.json",
    "r",
    encoding="utf-8"
) as file:
    config = json.load(file)


# --------------------------------
# Hospital
# --------------------------------

hospital_schema_path = "schema/hospital_schema.json"

hospital_df = generate_hospitals(
    hospital_schema_path
)


# --------------------------------
# Department
# --------------------------------

department_schema_path = "schema/department_schema.json"

department_df = generate_departments(
    department_schema_path,
    hospital_df,
    config
)


# --------------------------------
# Doctor
# --------------------------------

doctor_schema_path = "schema/doctor_schema.json"

doctor_df = generate_doctors(
    doctor_schema_path,
    hospital_df,
    department_df,
    config
)


# --------------------------------
# Patient
# --------------------------------

patient_schema_path = "schema/patient_schema.json"

patient_df = generate_patients(
    patient_schema_path,
    config
)


# --------------------------------
# Display generated data
# --------------------------------



# --------------------------------
# Save output
# --------------------------------

hospital_df.to_csv(
    "output/hospital.csv",
    index=False
)

department_df.to_csv(
    "output/department.csv",
    index=False
)

doctor_df.to_csv(
    "output/doctor.csv",
    index=False
)

patient_df.to_csv(
    "output/patient.csv",
    index=False
)


# --------------------------------
# Summary
# --------------------------------

print("\n--------------------------------")
print("DATA GENERATION SUMMARY")
print("--------------------------------")

print(f"Hospitals   : {len(hospital_df)}")
print(f"Departments : {len(department_df)}")
print(f"Doctors     : {len(doctor_df)}")
print(f"Patients    : {len(patient_df)}")

print("--------------------------------")
print("All data generated successfully!")
print("--------------------------------")