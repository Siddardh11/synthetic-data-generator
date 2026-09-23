from generators.hospital_generator import generate_hospitals
from generators.department_generator import generate_departments


# --------------------------------
# Hospital
# --------------------------------

hospital_schema_path = "schema/hospital_schema.json"

hospital_df = generate_hospitals(
    hospital_schema_path
)

print("\nHospital Data:")
print(hospital_df)


# --------------------------------
# Department
# --------------------------------

department_schema_path = "schema/department_schema.json"

department_df = generate_departments(
    department_schema_path,
    hospital_df
)

print("\nDepartment Data:")
print(department_df)


# --------------------------------
# Output
# --------------------------------

hospital_df.to_csv(
    "output/hospital.csv",
    index=False
)

department_df.to_csv(
    "output/department.csv",
    index=False
)


print("\nHospital and department data generated successfully!")