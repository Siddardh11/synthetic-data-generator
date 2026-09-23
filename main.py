import json

from generators.hospital_generator import generate_hospitals
from generators.department_generator import generate_departments
from generators.doctor_generator import generate_doctors


# --------------------------------
# Load configuration
# --------------------------------

with open("config/config.json", "r", encoding="utf-8") as file:
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
    hospital_df
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
# Display
# --------------------------------

print("\nHospital Data:")
print(hospital_df)

print("\nDepartment Data:")
print(department_df)

print("\nDoctor Data:")
print(doctor_df)


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


print("\nAll data generated successfully!")