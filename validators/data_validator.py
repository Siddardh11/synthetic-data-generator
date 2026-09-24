import os
import json
import pandas as pd


# ========================================
# Project paths
# ========================================

OUTPUT_DIR = "output"
CONFIG_PATH = "config/config.json"


# ========================================
# Load configuration
# ========================================

with open(
    CONFIG_PATH,
    "r",
    encoding="utf-8"
) as file:
    config = json.load(file)


# ========================================
# Expected files
# ========================================

expected_files = {
    "hospital": "hospital.csv",
    "department": "department.csv",
    "doctor": "doctor.csv",
    "patient": "patient.csv",
    "visit": "visit.csv",
    "admission": "admission.csv",
    "billing": "billing.csv",
    "diagnostic": "diagnostic_test.csv",
    "surgery": "surgery.csv"
}


# ========================================
# Expected record counts
# ========================================

expected_counts = {
    "hospital": config["record_counts"]["hospitals"],

    "department": config["record_counts"]["departments"],

    "doctor": config["record_counts"]["doctors"],

    "patient": config["record_counts"]["patients"],

    "visit": config["record_counts"]["visits"],

    "admission": config["record_counts"]["admissions"],

    "billing": config["record_counts"]["billing_records"],

    "diagnostic": config[
        "record_counts"
    ]["diagnostic_tests"],

    "surgery": config[
        "record_counts"
    ]["procedures"]
}


# ========================================
# Primary key definitions
# ========================================

primary_keys = {
    "hospital": "hospital_id",
    "department": "department_id",
    "doctor": "doctor_id",
    "patient": "patient_id",
    "visit": "visit_id",
    "admission": "admission_id",
    "billing": "bill_id",
    "diagnostic": "diagnostic_id",
    "surgery": "procedure_id"
}


# ========================================
# Foreign key definitions
# ========================================

foreign_keys = {
    "department": {
        "hospital_id": (
            "hospital",
            "hospital_id"
        )
    },

    "doctor": {
        "hospital_id": (
            "hospital",
            "hospital_id"
        ),

        "department_id": (
            "department",
            "department_id"
        )
    },

    "visit": {
        "patient_id": (
            "patient",
            "patient_id"
        ),

        "hospital_id": (
            "hospital",
            "hospital_id"
        ),

        "department_id": (
            "department",
            "department_id"
        ),

        "doctor_id": (
            "doctor",
            "doctor_id"
        )
    },

    "admission": {
        "patient_id": (
            "patient",
            "patient_id"
        ),

        "hospital_id": (
            "hospital",
            "hospital_id"
        ),

        "department_id": (
            "department",
            "department_id"
        ),

        "doctor_id": (
            "doctor",
            "doctor_id"
        )
    },

    "billing": {
        "patient_id": (
            "patient",
            "patient_id"
        ),

        "visit_id": (
            "visit",
            "visit_id"
        ),

        "admission_id": (
            "admission",
            "admission_id"
        ),

        "hospital_id": (
            "hospital",
            "hospital_id"
        ),

        "department_id": (
            "department",
            "department_id"
        )
    },

    "diagnostic": {
        "patient_id": (
            "patient",
            "patient_id"
        ),

        "visit_id": (
            "visit",
            "visit_id"
        ),

        "hospital_id": (
            "hospital",
            "hospital_id"
        ),

        "department_id": (
            "department",
            "department_id"
        ),

        "doctor_id": (
            "doctor",
            "doctor_id"
        )
    },

    "surgery": {
        "patient_id": (
            "patient",
            "patient_id"
        ),

        "admission_id": (
            "admission",
            "admission_id"
        ),

        "hospital_id": (
            "hospital",
            "hospital_id"
        ),

        "department_id": (
            "department",
            "department_id"
        ),

        "doctor_id": (
            "doctor",
            "doctor_id"
        )
    }
}


# ========================================
# Load all CSV files
# ========================================

tables = {}

print("\n========================================")
print("LOADING GENERATED DATA")
print("========================================")

for table_name, file_name in expected_files.items():

    file_path = os.path.join(
        OUTPUT_DIR,
        file_name
    )

    if not os.path.exists(file_path):

        print(
            f"✗ {file_name} - FILE NOT FOUND"
        )

    else:

        df = pd.read_csv(file_path)

        tables[table_name] = df

        print(
            f"✓ {file_name} - loaded "
            f"({len(df)} records)"
        )


# ========================================
# Stop if files are missing
# ========================================

missing_tables = [
    table
    for table in expected_files
    if table not in tables
]

if missing_tables:

    print("\n========================================")
    print("VALIDATION STOPPED")
    print("========================================")

    print(
        "Missing tables:",
        ", ".join(missing_tables)
    )

    print("\nRun:")
    print("python main.py")

    raise SystemExit


# ========================================
# Test 1 — Record Counts
# ========================================

print("\n========================================")
print("1. RECORD COUNT VALIDATION")
print("========================================")

count_failures = 0

for table_name, expected_count in expected_counts.items():

    actual_count = len(
        tables[table_name]
    )

    if actual_count == expected_count:

        print(
            f"✓ {table_name:<12} "
            f"{actual_count} / {expected_count}"
        )

    else:

        print(
            f"✗ {table_name:<12} "
            f"{actual_count} / {expected_count}"
        )

        count_failures += 1


# ========================================
# Test 2 — Primary Keys
# ========================================

print("\n========================================")
print("2. PRIMARY KEY VALIDATION")
print("========================================")

primary_key_failures = 0

for table_name, primary_key in primary_keys.items():

    df = tables[table_name]

    # Check column exists
    if primary_key not in df.columns:

        print(
            f"✗ {table_name}: "
            f"{primary_key} column missing"
        )

        primary_key_failures += 1

        continue

    # Check null values
    null_count = df[
        primary_key
    ].isna().sum()

    # Check duplicates
    duplicate_count = df[
        primary_key
    ].duplicated().sum()

    if null_count == 0 and duplicate_count == 0:

        print(
            f"✓ {table_name:<12} "
            f"{primary_key}"
        )

    else:

        print(
            f"✗ {table_name:<12} "
            f"{primary_key} "
            f"(nulls={null_count}, "
            f"duplicates={duplicate_count})"
        )

        primary_key_failures += 1


# ========================================
# Test 3 — Foreign Keys
# ========================================

print("\n========================================")
print("3. FOREIGN KEY VALIDATION")
print("========================================")

foreign_key_failures = 0

for table_name, relationships in foreign_keys.items():

    df = tables[table_name]

    for column_name, (
        referenced_table,
        referenced_column
    ) in relationships.items():

        # Make sure the source column exists
        if column_name not in df.columns:

            print(
                f"✗ {table_name}.{column_name} "
                f"column missing"
            )

            foreign_key_failures += 1

            continue

        # Get valid referenced IDs
        valid_ids = set(
            tables[referenced_table][
                referenced_column
            ].dropna()
        )

        # Find invalid IDs
        invalid_rows = df[
            ~df[column_name].isin(valid_ids)
            &
            df[column_name].notna()
        ]

        invalid_count = len(
            invalid_rows
        )

        if invalid_count == 0:

            print(
                f"✓ {table_name}.{column_name} "
                f"→ "
                f"{referenced_table}.{referenced_column}"
            )

        else:

            print(
                f"✗ {table_name}.{column_name} "
                f"→ "
                f"{referenced_table}.{referenced_column} "
                f"({invalid_count} invalid)"
            )

            foreign_key_failures += 1

# ========================================
# Test 4 — Relationship Consistency
# ========================================

print("\n========================================")
print("4. RELATIONSHIP CONSISTENCY VALIDATION")
print("========================================")

relationship_failures = 0


# ----------------------------------------
# Department → Hospital
# ----------------------------------------

department_lookup = (
    tables["department"]
    .set_index("department_id")["hospital_id"]
    .to_dict()
)

for _, row in tables["department"].iterrows():

    department_id = row["department_id"]
    hospital_id = row["hospital_id"]

    if department_lookup.get(department_id) != hospital_id:

        relationship_failures += 1

        print(
            f"✗ Department {department_id} "
            f"has incorrect hospital relationship"
        )


if relationship_failures == 0:

    print(
        "✓ Department → Hospital"
    )


# ----------------------------------------
# Doctor → Hospital + Department
# ----------------------------------------

doctor_lookup = (
    tables["doctor"]
    .set_index("doctor_id")
    [
        [
            "hospital_id",
            "department_id"
        ]
    ]
    .to_dict("index")
)

department_lookup = (
    tables["department"]
    .set_index("department_id")
    [
        "hospital_id"
    ]
    .to_dict()
)

doctor_failures = 0

for _, row in tables["doctor"].iterrows():

    doctor_id = row["doctor_id"]

    hospital_id = row["hospital_id"]

    department_id = row["department_id"]

    expected_hospital = department_lookup.get(
        department_id
    )

    if expected_hospital != hospital_id:

        doctor_failures += 1

        print(
            f"✗ Doctor {doctor_id}: "
            f"department {department_id} "
            f"belongs to hospital "
            f"{expected_hospital}, "
            f"but doctor belongs to hospital "
            f"{hospital_id}"
        )


if doctor_failures == 0:

    print(
        "✓ Doctor → Hospital + Department"
    )

relationship_failures += doctor_failures


# ----------------------------------------
# Visit → Doctor + Department + Hospital
# ----------------------------------------

visit_failures = 0

doctor_lookup = (
    tables["doctor"]
    .set_index("doctor_id")[["hospital_id", "department_id"]]
    .to_dict("index")
)

for row in tables["visit"].itertuples(index=False):

    doctor = doctor_lookup.get(row.doctor_id)

    if doctor is None:
        continue

    if doctor["hospital_id"] != row.hospital_id:

        visit_failures += 1

        print(
            f"✗ Visit {row.visit_id}: "
            f"doctor {row.doctor_id} belongs to "
            f"hospital {doctor['hospital_id']}, "
            f"not {row.hospital_id}"
        )

    if doctor["department_id"] != row.department_id:

        visit_failures += 1

        print(
            f"✗ Visit {row.visit_id}: "
            f"doctor {row.doctor_id} belongs to "
            f"department {doctor['department_id']}, "
            f"not {row.department_id}"
        )


if visit_failures == 0:

    print(
        "✓ Visit → Doctor + Department + Hospital"
    )

relationship_failures += visit_failures


# ----------------------------------------
# Visit → Patient
# ----------------------------------------

visit_patient_failures = 0

valid_patient_ids = set(
    tables["patient"]["patient_id"]
)

for _, row in tables["visit"].iterrows():

    if row["patient_id"] not in valid_patient_ids:

        visit_patient_failures += 1

        print(
            f"✗ Visit {row['visit_id']}: "
            f"invalid patient relationship"
        )


if visit_patient_failures == 0:

    print(
        "✓ Visit → Patient"
    )

relationship_failures += visit_patient_failures


# ----------------------------------------
# Admission → Doctor + Department + Hospital
# ----------------------------------------

admission_failures = 0

for row in tables["admission"].itertuples(index=False):

    doctor = doctor_lookup.get(row.doctor_id)

    if doctor is None:
        continue

    if doctor["hospital_id"] != row.hospital_id:

        admission_failures += 1

        print(
            f"✗ Admission {row.admission_id}: "
            f"doctor/hospital mismatch"
        )

    if doctor["department_id"] != row.department_id:

        admission_failures += 1

        print(
            f"✗ Admission {row.admission_id}: "
            f"doctor/department mismatch"
        )


if admission_failures == 0:

    print(
        "✓ Admission → Doctor + Department + Hospital"
    )

relationship_failures += admission_failures


# ----------------------------------------
# Admission → Patient
# ----------------------------------------

admission_patient_failures = 0

valid_patient_ids = set(
    tables["patient"]["patient_id"]
)

for _, row in tables["admission"].iterrows():

    if row["patient_id"] not in valid_patient_ids:

        admission_patient_failures += 1

        print(
            f"✗ Admission {row['admission_id']}: "
            f"invalid patient relationship"
        )


if admission_patient_failures == 0:

    print(
        "✓ Admission → Patient"
    )

relationship_failures += admission_patient_failures


# ----------------------------------------
# Diagnostic → Visit
# ----------------------------------------

diagnostic_failures = 0

visit_lookup = (
    tables["visit"]
    .set_index("visit_id")
    [
        [
            "patient_id",
            "hospital_id",
            "department_id",
            "doctor_id"
        ]
    ]
    .to_dict("index")
)

for _, row in tables["diagnostic"].iterrows():

    diagnostic_id = row["diagnostic_id"]

    visit_id = row["visit_id"]

    visit = visit_lookup.get(
        visit_id
    )

    if visit is None:

        continue

    if row["patient_id"] != visit["patient_id"]:

        diagnostic_failures += 1

        print(
            f"✗ Diagnostic {diagnostic_id}: "
            f"patient does not match visit"
        )

    if row["hospital_id"] != visit["hospital_id"]:

        diagnostic_failures += 1

        print(
            f"✗ Diagnostic {diagnostic_id}: "
            f"hospital does not match visit"
        )

    if row["department_id"] != visit["department_id"]:

        diagnostic_failures += 1

        print(
            f"✗ Diagnostic {diagnostic_id}: "
            f"department does not match visit"
        )

    if row["doctor_id"] != visit["doctor_id"]:

        diagnostic_failures += 1

        print(
            f"✗ Diagnostic {diagnostic_id}: "
            f"doctor does not match visit"
        )


if diagnostic_failures == 0:

    print(
        "✓ Diagnostic → Visit + Patient + "
        "Doctor + Department + Hospital"
    )

relationship_failures += diagnostic_failures


# ----------------------------------------
# Surgery → Admission
# ----------------------------------------

surgery_failures = 0

admission_lookup = (
    tables["admission"]
    .set_index("admission_id")
    [
        [
            "patient_id",
            "hospital_id",
            "department_id",
            "doctor_id"
        ]
    ]
    .to_dict("index")
)

for _, row in tables["surgery"].iterrows():

    procedure_id = row["procedure_id"]

    admission_id = row["admission_id"]

    admission = admission_lookup.get(
        admission_id
    )

    if admission is None:

        continue

    if row["patient_id"] != admission["patient_id"]:

        surgery_failures += 1

        print(
            f"✗ Surgery {procedure_id}: "
            f"patient does not match admission"
        )

    if row["hospital_id"] != admission["hospital_id"]:

        surgery_failures += 1

        print(
            f"✗ Surgery {procedure_id}: "
            f"hospital does not match admission"
        )

    if row["department_id"] != admission["department_id"]:

        surgery_failures += 1

        print(
            f"✗ Surgery {procedure_id}: "
            f"department does not match admission"
        )

    if row["doctor_id"] != admission["doctor_id"]:

        surgery_failures += 1

        print(
            f"✗ Surgery {procedure_id}: "
            f"doctor does not match admission"
        )


if surgery_failures == 0:

    print(
        "✓ Surgery → Admission + Patient + "
        "Doctor + Department + Hospital"
    )

relationship_failures += surgery_failures


# ----------------------------------------
# Billing → Visit / Admission
# ----------------------------------------

billing_failures = 0

visit_lookup = (
    tables["visit"]
    .set_index("visit_id")
    [
        [
            "patient_id",
            "hospital_id",
            "department_id"
        ]
    ]
    .to_dict("index")
)

admission_lookup = (
    tables["admission"]
    .set_index("admission_id")
    [
        [
            "patient_id",
            "hospital_id",
            "department_id"
        ]
    ]
    .to_dict("index")
)

for _, row in tables["billing"].iterrows():

    bill_id = row["bill_id"]

    # --------------------------------
    # Visit-based bill
    # --------------------------------

    if pd.notna(row["visit_id"]):

        visit = visit_lookup.get(
            row["visit_id"]
        )

        if visit is None:

            continue

        if row["patient_id"] != visit["patient_id"]:

            billing_failures += 1

            print(
                f"✗ Billing {bill_id}: "
                f"patient does not match visit"
            )

        if row["hospital_id"] != visit["hospital_id"]:

            billing_failures += 1

            print(
                f"✗ Billing {bill_id}: "
                f"hospital does not match visit"
            )

        if row["department_id"] != visit["department_id"]:

            billing_failures += 1

            print(
                f"✗ Billing {bill_id}: "
                f"department does not match visit"
            )

    # --------------------------------
    # Admission-based bill
    # --------------------------------

    if pd.notna(row["admission_id"]):

        admission = admission_lookup.get(
            row["admission_id"]
        )

        if admission is None:

            continue

        if row["patient_id"] != admission["patient_id"]:

            billing_failures += 1

            print(
                f"✗ Billing {bill_id}: "
                f"patient does not match admission"
            )

        if row["hospital_id"] != admission["hospital_id"]:

            billing_failures += 1

            print(
                f"✗ Billing {bill_id}: "
                f"hospital does not match admission"
            )

        if row["department_id"] != admission["department_id"]:

            billing_failures += 1

            print(
                f"✗ Billing {bill_id}: "
                f"department does not match admission"
            )


if billing_failures == 0:

    print(
        "✓ Billing → Visit / Admission + "
        "Patient + Hospital + Department"
    )

relationship_failures += billing_failures

# ========================================
# Test 5 — Date & Business Rule Validation
# ========================================

print("\n========================================")
print("5. DATE & BUSINESS RULE VALIDATION")
print("========================================")

date_failures = 0

today = pd.Timestamp.today().normalize()

# ========================================
# Configured Historical Date Range
# ========================================

date_range = config["date_range"]

historical_start = pd.to_datetime(
    date_range["start_date"]
).normalize()

historical_end = pd.to_datetime(
    date_range["end_date"]
).normalize()


# ========================================
# Patient Date Validation
# ========================================

patient_failures = 0

patients = tables["patient"].copy()

patients["registration_date"] = pd.to_datetime(
    patients["registration_date"],
    errors="coerce"
)

for _, row in patients.iterrows():

    patient_id = row["patient_id"]

    registration_date = row[
        "registration_date"
    ]

    # Invalid date
    if pd.isna(registration_date):

        patient_failures += 1

        print(
            f"✗ Patient {patient_id}: "
            f"invalid registration_date"
        )

    # Registration cannot be in future
    elif registration_date > today:

        patient_failures += 1

        print(
            f"✗ Patient {patient_id}: "
            f"registration_date is in the future"
        )


if patient_failures == 0:

    print(
        "✓ Patient registration dates"
    )

date_failures += patient_failures


# ========================================
# Visit Date Validation
# ========================================

visit_failures = 0

patients_lookup = (
    patients
    .set_index("patient_id")
    ["registration_date"]
    .to_dict()
)

visits = tables["visit"].copy()

visits["visit_date"] = pd.to_datetime(
    visits["visit_date"],
    errors="coerce"
)

for _, row in visits.iterrows():

    visit_id = row["visit_id"]

    patient_id = row["patient_id"]

    visit_date = row["visit_date"]

    registration_date = patients_lookup.get(
        patient_id
    )

    # Invalid visit date
    if pd.isna(visit_date):

        visit_failures += 1

        print(
            f"✗ Visit {visit_id}: "
            f"invalid visit_date"
        )

        continue

    # Visit cannot be in future
    if visit_date > today:

        visit_failures += 1

        print(
            f"✗ Visit {visit_id}: "
            f"visit_date is in the future"
        )

    # Visit cannot occur before registration
    if (
        registration_date is not None
        and
        visit_date < registration_date
    ):

        visit_failures += 1

        print(
            f"✗ Visit {visit_id}: "
            f"visit_date is before "
            f"patient registration"
        )


if visit_failures == 0:

    print(
        "✓ Visit dates"
    )

date_failures += visit_failures


# ========================================
# Admission Date Validation
# ========================================

admission_failures = 0

admissions = tables["admission"].copy()

admissions["admission_date"] = pd.to_datetime(
    admissions["admission_date"],
    errors="coerce"
)

admissions["discharge_date"] = pd.to_datetime(
    admissions["discharge_date"],
    errors="coerce"
)

for _, row in admissions.iterrows():

    admission_id = row["admission_id"]

    patient_id = row["patient_id"]

    admission_date = row[
        "admission_date"
    ]

    discharge_date = row[
        "discharge_date"
    ]

    admission_status = row[
        "admission_status"
    ]

    length_of_stay = row[
        "length_of_stay"
    ]

    registration_date = patients_lookup.get(
        patient_id
    )

    # --------------------------------
    # Admission date validity
    # --------------------------------

    if pd.isna(admission_date):

        admission_failures += 1

        print(
            f"✗ Admission {admission_id}: "
            f"invalid admission_date"
        )

        continue

    # Admission cannot be in future
    if admission_date > today:

        admission_failures += 1

        print(
            f"✗ Admission {admission_id}: "
            f"admission_date is in the future"
        )

    # Admission cannot happen before registration
    if (
        registration_date is not None
        and
        admission_date < registration_date
    ):

        admission_failures += 1

        print(
            f"✗ Admission {admission_id}: "
            f"admission_date is before "
            f"patient registration"
        )

    # =================================
    # Discharged admission
    # =================================

    if admission_status == "Discharged":

        # Discharge date must exist
        if pd.isna(discharge_date):

            admission_failures += 1

            print(
                f"✗ Admission {admission_id}: "
                f"Discharged but discharge_date "
                f"is missing"
            )

            continue

        # Discharge cannot be before admission
        if discharge_date < admission_date:

            admission_failures += 1

            print(
                f"✗ Admission {admission_id}: "
                f"discharge_date is before "
                f"admission_date"
            )

        # Discharge cannot be in future
        if discharge_date > today:

            admission_failures += 1

            print(
                f"✗ Admission {admission_id}: "
                f"discharge_date is in the future"
            )

        # --------------------------------
        # Validate length of stay
        # --------------------------------

        expected_length = (
            discharge_date - admission_date
        ).days

        if length_of_stay != expected_length:

            admission_failures += 1

            print(
                f"✗ Admission {admission_id}: "
                f"length_of_stay mismatch "
                f"(expected {expected_length}, "
                f"got {length_of_stay})"
            )

    # =================================
    # Ongoing admission
    # =================================

    elif admission_status == "Ongoing":

        # Ongoing admission should not
        # have a discharge date
        if pd.notna(discharge_date):

            admission_failures += 1

            print(
                f"✗ Admission {admission_id}: "
                f"Ongoing but discharge_date "
                f"exists"
            )

        # --------------------------------
        # Validate current length of stay
        # --------------------------------

        expected_length = (
            today - admission_date
        ).days

        if length_of_stay != expected_length:

            admission_failures += 1

            print(
                f"✗ Admission {admission_id}: "
                f"ongoing length_of_stay mismatch "
                f"(expected {expected_length}, "
                f"got {length_of_stay})"
            )


if admission_failures == 0:

    print(
        "✓ Admission dates + "
        "length of stay + status"
    )

date_failures += admission_failures


# ========================================
# Diagnostic Date Validation
# ========================================

diagnostic_failures = 0

visit_date_lookup = (
    visits
    .set_index("visit_id")
    ["visit_date"]
    .to_dict()
)

diagnostics = tables["diagnostic"].copy()

diagnostics["test_date"] = pd.to_datetime(
    diagnostics["test_date"],
    errors="coerce"
)

for _, row in diagnostics.iterrows():

    diagnostic_id = row[
        "diagnostic_id"
    ]

    visit_id = row[
        "visit_id"
    ]

    test_date = row[
        "test_date"
    ]

    visit_date = visit_date_lookup.get(
        visit_id
    )

    # Invalid test date
    if pd.isna(test_date):

        diagnostic_failures += 1

        print(
            f"✗ Diagnostic {diagnostic_id}: "
            f"invalid test_date"
        )

        continue

    # Test cannot be in future
    if test_date > today:

        diagnostic_failures += 1

        print(
            f"✗ Diagnostic {diagnostic_id}: "
            f"test_date is in the future"
        )

    # Test cannot happen before visit
    if (
        visit_date is not None
        and
        test_date < visit_date
    ):

        diagnostic_failures += 1

        print(
            f"✗ Diagnostic {diagnostic_id}: "
            f"test_date is before visit_date"
        )


if diagnostic_failures == 0:

    print(
        "✓ Diagnostic test dates"
    )

date_failures += diagnostic_failures


# ========================================
# Surgery Date Validation
# ========================================

surgery_failures = 0

admission_date_lookup = (
    admissions
    .set_index("admission_id")
    [
        [
            "admission_date",
            "discharge_date",
            "admission_status"
        ]
    ]
    .to_dict("index")
)

surgeries = tables["surgery"].copy()

surgeries["procedure_date"] = pd.to_datetime(
    surgeries["procedure_date"],
    errors="coerce"
)

for _, row in surgeries.iterrows():

    procedure_id = row[
        "procedure_id"
    ]

    admission_id = row[
        "admission_id"
    ]

    procedure_date = row[
        "procedure_date"
    ]

    admission = admission_date_lookup.get(
        admission_id
    )

    # Invalid procedure date
    if pd.isna(procedure_date):

        surgery_failures += 1

        print(
            f"✗ Surgery {procedure_id}: "
            f"invalid procedure_date"
        )

        continue

    # Procedure cannot be in future
    if procedure_date > today:

        surgery_failures += 1

        print(
            f"✗ Surgery {procedure_id}: "
            f"procedure_date is in the future"
        )

    if admission is None:

        continue

    admission_date = admission[
        "admission_date"
    ]

    discharge_date = admission[
        "discharge_date"
    ]

    # Procedure cannot happen before admission
    if procedure_date < admission_date:

        surgery_failures += 1

        print(
            f"✗ Surgery {procedure_id}: "
            f"procedure_date is before "
            f"admission_date"
        )

    # --------------------------------
    # For discharged admissions,
    # procedure must happen before
    # discharge.
    # --------------------------------

    if (
        pd.notna(discharge_date)
        and
        procedure_date > discharge_date
    ):

        surgery_failures += 1

        print(
            f"✗ Surgery {procedure_id}: "
            f"procedure_date is after "
            f"discharge_date"
        )


if surgery_failures == 0:

    print(
        "✓ Surgery dates"
    )

date_failures += surgery_failures


# ========================================
# Historical Date Range Validation
# ========================================

historical_failures = 0

print("\n----------------------------------------")
print(
    f"Configured historical period: "
    f"{historical_start.date()} → "
    f"{historical_end.date()}"
)


def validate_historical_range(df, date_column, table_name):

    failures = 0

    dates = pd.to_datetime(
        df[date_column],
        errors="coerce"
    )

    invalid_dates = dates[
        dates.notna()
        &
        (
            (dates < historical_start)
            |
            (dates > historical_end)
        )
    ]

    if len(invalid_dates) > 0:

        failures = len(invalid_dates)

        print(
            f"✗ {table_name}.{date_column}: "
            f"{failures} dates outside "
            f"historical range"
        )

    else:

        print(
            f"✓ {table_name}.{date_column}: "
            f"within historical range"
        )

    return failures


historical_failures += validate_historical_range(
    tables["patient"],
    "registration_date",
    "patient"
)

historical_failures += validate_historical_range(
    tables["visit"],
    "visit_date",
    "visit"
)

historical_failures += validate_historical_range(
    tables["admission"],
    "admission_date",
    "admission"
)

historical_failures += validate_historical_range(
    tables["admission"],
    "discharge_date",
    "admission"
)

historical_failures += validate_historical_range(
    tables["billing"],
    "bill_date",
    "billing"
)

historical_failures += validate_historical_range(
    tables["diagnostic"],
    "test_date",
    "diagnostic"
)

historical_failures += validate_historical_range(
    tables["surgery"],
    "procedure_date",
    "surgery"
)


# ========================================
# Actual Historical Coverage
# ========================================

coverage_tables = {
    "patient": (
        tables["patient"],
        "registration_date"
    ),
    "visit": (
        tables["visit"],
        "visit_date"
    ),
    "admission": (
        tables["admission"],
        "admission_date"
    ),
    "billing": (
        tables["billing"],
        "bill_date"
    ),
    "diagnostic": (
        tables["diagnostic"],
        "test_date"
    ),
    "surgery": (
        tables["surgery"],
        "procedure_date"
    )
}

for table_name, (df, date_column) in coverage_tables.items():

    dates = pd.to_datetime(
        df[date_column],
        errors="coerce"
    ).dropna()

    if len(dates) == 0:

        historical_failures += 1

        print(
            f"✗ {table_name}: no valid dates available"
        )

        continue

    print(
        f"✓ {table_name} coverage: "
        f"{dates.min().date()} → "
        f"{dates.max().date()}"
    )


# ========================================
# Step 2 — Monthly / Quarterly / Yearly
#              Distribution Validation
# ========================================

print("\n----------------------------------------")
print("DATE DISTRIBUTION & COVERAGE VALIDATION")
print("----------------------------------------")


distribution_failures = 0


def validate_date_distribution(
    df,
    date_column,
    table_name,
    minimum_active_months=3,
    minimum_active_quarters=2,
    minimum_active_years=1,
    max_month_share=0.50
):
    """Check whether records are reasonably distributed over time."""

    failures = 0

    dates = pd.to_datetime(
        df[date_column],
        errors="coerce"
    ).dropna()

    if len(dates) == 0:
        print(
            f"✗ {table_name}: no valid dates for distribution check"
        )
        return 1

    # ----------------------------------------
    # Monthly coverage
    # ----------------------------------------

    monthly_counts = dates.dt.to_period("M").value_counts()
    active_months = len(monthly_counts)

    if active_months < minimum_active_months:

        failures += 1

        print(
            f"✗ {table_name}: only {active_months} "
            f"active months; expected at least "
            f"{minimum_active_months}"
        )

    else:

        print(
            f"✓ {table_name}: monthly coverage "
            f"across {active_months} months"
        )

    # ----------------------------------------
    # Monthly concentration
    # ----------------------------------------

    largest_month_count = monthly_counts.max()
    largest_month_share = largest_month_count / len(dates)

    if largest_month_share > max_month_share:

        failures += 1

        largest_month = monthly_counts.idxmax()

        print(
            f"✗ {table_name}: {largest_month} contains "
            f"{largest_month_count}/{len(dates)} records "
            f"({largest_month_share:.1%}), exceeding "
            f"the {max_month_share:.0%} limit"
        )

    else:

        print(
            f"✓ {table_name}: no excessive monthly "
            f"concentration "
            f"(max {largest_month_share:.1%})"
        )

    # ----------------------------------------
    # Quarterly coverage
    # ----------------------------------------

    quarterly_counts = dates.dt.to_period("Q").value_counts()
    active_quarters = len(quarterly_counts)

    if active_quarters < minimum_active_quarters:

        failures += 1

        print(
            f"✗ {table_name}: only {active_quarters} "
            f"active quarters; expected at least "
            f"{minimum_active_quarters}"
        )

    else:

        print(
            f"✓ {table_name}: quarterly coverage "
            f"across {active_quarters} quarters"
        )

    # ----------------------------------------
    # Yearly coverage
    # ----------------------------------------

    yearly_counts = dates.dt.year.value_counts()
    active_years = len(yearly_counts)

    if active_years < minimum_active_years:

        failures += 1

        print(
            f"✗ {table_name}: only {active_years} "
            f"active years; expected at least "
            f"{minimum_active_years}"
        )

    else:

        print(
            f"✓ {table_name}: yearly coverage "
            f"across {active_years} years"
        )

    return failures


# Larger datasets should cover more months.
distribution_failures += validate_date_distribution(
    tables["patient"],
    "registration_date",
    "patient",
    minimum_active_months=6,
    minimum_active_quarters=4,
    minimum_active_years=2,
    max_month_share=0.25
)

distribution_failures += validate_date_distribution(
    tables["visit"],
    "visit_date",
    "visit",
    minimum_active_months=6,
    minimum_active_quarters=4,
    minimum_active_years=2,
    max_month_share=0.25
)

distribution_failures += validate_date_distribution(
    tables["admission"],
    "admission_date",
    "admission",
    minimum_active_months=4,
    minimum_active_quarters=3,
    minimum_active_years=2,
    max_month_share=0.35
)

distribution_failures += validate_date_distribution(
    tables["billing"],
    "bill_date",
    "billing",
    minimum_active_months=6,
    minimum_active_quarters=4,
    minimum_active_years=2,
    max_month_share=0.25
)

distribution_failures += validate_date_distribution(
    tables["diagnostic"],
    "test_date",
    "diagnostic",
    minimum_active_months=6,
    minimum_active_quarters=4,
    minimum_active_years=2,
    max_month_share=0.25
)

distribution_failures += validate_date_distribution(
    tables["surgery"],
    "procedure_date",
    "surgery",
    minimum_active_months=4,
    minimum_active_quarters=3,
    minimum_active_years=2,
    max_month_share=0.40
)


historical_failures += distribution_failures

date_failures += historical_failures

print("----------------------------------------")
print(
    f"Historical/distribution failures : "
    f"{historical_failures}"
)
print(
    f"Date/business rule failures : "
    f"{date_failures}"
)

# ========================================
# Date Validation Summary
# ========================================

print("----------------------------------------")
print(
    f"Date/business rule failures : "
    f"{date_failures}"
)

# ========================================
# Test 6 — Financial Validation
# ========================================

print("\n========================================")
print("6. FINANCIAL VALIDATION")
print("========================================")

financial_failures = 0


# ========================================
# Billing Financial Validation
# ========================================

billing_failures = 0

billing = tables["billing"].copy()

# Convert financial columns to numeric
financial_columns = [
    "gross_amount",
    "discount_amount",
    "insurance_amount",
    "patient_amount",
    "total_amount"
]

for column in financial_columns:
    billing[column] = pd.to_numeric(
        billing[column],
        errors="coerce"
    )


for _, row in billing.iterrows():

    bill_id = row["bill_id"]

    gross_amount = row["gross_amount"]
    discount_amount = row["discount_amount"]
    insurance_amount = row["insurance_amount"]
    patient_amount = row["patient_amount"]
    total_amount = row["total_amount"]


    # ====================================
    # Check numeric values
    # ====================================

    if pd.isna(gross_amount):

        billing_failures += 1

        print(
            f"✗ Billing {bill_id}: "
            f"invalid gross_amount"
        )

        continue


    if pd.isna(discount_amount):

        billing_failures += 1

        print(
            f"✗ Billing {bill_id}: "
            f"invalid discount_amount"
        )

        continue


    if pd.isna(insurance_amount):

        billing_failures += 1

        print(
            f"✗ Billing {bill_id}: "
            f"invalid insurance_amount"
        )

        continue


    if pd.isna(patient_amount):

        billing_failures += 1

        print(
            f"✗ Billing {bill_id}: "
            f"invalid patient_amount"
        )

        continue


    if pd.isna(total_amount):

        billing_failures += 1

        print(
            f"✗ Billing {bill_id}: "
            f"invalid total_amount"
        )

        continue


    # ====================================
    # Gross amount
    # ====================================

    if gross_amount < 0:

        billing_failures += 1

        print(
            f"✗ Billing {bill_id}: "
            f"gross_amount is negative"
        )


    # ====================================
    # Discount amount
    # ====================================

    if discount_amount < 0:

        billing_failures += 1

        print(
            f"✗ Billing {bill_id}: "
            f"discount_amount is negative"
        )


    if discount_amount > gross_amount:

        billing_failures += 1

        print(
            f"✗ Billing {bill_id}: "
            f"discount_amount exceeds "
            f"gross_amount"
        )


    # ====================================
    # Total amount
    # ====================================

    expected_total = (
        gross_amount - discount_amount
    )

    if abs(total_amount - expected_total) > 0.01:

        billing_failures += 1

        print(
            f"✗ Billing {bill_id}: "
            f"total_amount mismatch "
            f"(expected {expected_total:.2f}, "
            f"got {total_amount:.2f})"
        )


    # ====================================
    # Insurance amount
    # ====================================

    if insurance_amount < 0:

        billing_failures += 1

        print(
            f"✗ Billing {bill_id}: "
            f"insurance_amount is negative"
        )


    if insurance_amount > total_amount:

        billing_failures += 1

        print(
            f"✗ Billing {bill_id}: "
            f"insurance_amount exceeds "
            f"total_amount"
        )


    # ====================================
    # Patient amount
    # ====================================

    if patient_amount < 0:

        billing_failures += 1

        print(
            f"✗ Billing {bill_id}: "
            f"patient_amount is negative"
        )


    if patient_amount > total_amount:

        billing_failures += 1

        print(
            f"✗ Billing {bill_id}: "
            f"patient_amount exceeds "
            f"total_amount"
        )


    # ====================================
    # Insurance + Patient = Total
    # ====================================

    responsibility_total = (
        insurance_amount
        + patient_amount
    )

    if abs(
        responsibility_total - total_amount
    ) > 0.01:

        billing_failures += 1

        print(
            f"✗ Billing {bill_id}: "
            f"insurance + patient amount "
            f"does not equal total amount "
            f"(expected {total_amount:.2f}, "
            f"got {responsibility_total:.2f})"
        )


if billing_failures == 0:

    print(
        "✓ Billing financial rules"
    )

financial_failures += billing_failures


# ========================================
# Diagnostic Amount Validation
# ========================================

diagnostic_failures = 0

diagnostics = tables["diagnostic"].copy()

diagnostics["amount"] = pd.to_numeric(
    diagnostics["amount"],
    errors="coerce"
)


for _, row in diagnostics.iterrows():

    diagnostic_id = row[
        "diagnostic_id"
    ]

    amount = row["amount"]


    if pd.isna(amount):

        diagnostic_failures += 1

        print(
            f"✗ Diagnostic {diagnostic_id}: "
            f"invalid amount"
        )

        continue


    if amount < 0:

        diagnostic_failures += 1

        print(
            f"✗ Diagnostic {diagnostic_id}: "
            f"amount is negative"
        )


if diagnostic_failures == 0:

    print(
        "✓ Diagnostic financial rules"
    )

financial_failures += diagnostic_failures


# ========================================
# Surgery Cost Validation
# ========================================

surgery_failures = 0

surgeries = tables["surgery"].copy()

surgeries["cost"] = pd.to_numeric(
    surgeries["cost"],
    errors="coerce"
)


for _, row in surgeries.iterrows():

    procedure_id = row[
        "procedure_id"
    ]

    cost = row["cost"]


    if pd.isna(cost):

        surgery_failures += 1

        print(
            f"✗ Surgery {procedure_id}: "
            f"invalid cost"
        )

        continue


    if cost < 0:

        surgery_failures += 1

        print(
            f"✗ Surgery {procedure_id}: "
            f"cost is negative"
        )


if surgery_failures == 0:

    print(
        "✓ Surgery financial rules"
    )

financial_failures += surgery_failures


# ========================================
# Financial Validation Summary
# ========================================

print("----------------------------------------")

print(
    f"Financial failures : "
    f"{financial_failures}"
)

# ========================================
# Test 7 — Schema & Data Quality Validation
# ========================================

print("\n========================================")
print("7. SCHEMA & DATA QUALITY VALIDATION")
print("========================================")

quality_failures = 0


# ========================================
# Expected Columns
# ========================================

expected_columns = {

    "hospital": [
        "hospital_id",
        "hospital_name",
        "city",
        "state",
        "hospital_type",
        "bed_capacity"
    ],

    "department": [
        "department_id",
        "department_name",
        "hospital_id"
    ],

    "doctor": [
        "doctor_id",
        "doctor_name",
        "hospital_id",
        "department_id",
        "specialization",
        "experience_years",
        "consultation_fee",
        "joining_date"
    ],

    "patient": [
        "patient_id",
        "patient_name",
        "gender",
        "date_of_birth",
        "age",
        "city",
        "registration_date",
        "insurance_type"
    ],

    "visit": [
        "visit_id",
        "patient_id",
        "hospital_id",
        "department_id",
        "doctor_id",
        "visit_date",
        "visit_type",
        "visit_status",
        "consultation_fee",
        "source"
    ],

    "admission": [
        "admission_id",
        "patient_id",
        "hospital_id",
        "department_id",
        "doctor_id",
        "admission_date",
        "discharge_date",
        "admission_type",
        "ward_type",
        "diagnosis_category",
        "length_of_stay",
        "admission_status"
    ],

    "billing": [
        "bill_id",
        "patient_id",
        "visit_id",
        "admission_id",
        "hospital_id",
        "department_id",
        "bill_date",
        "bill_category",
        "gross_amount",
        "discount_amount",
        "insurance_amount",
        "patient_amount",
        "total_amount",
        "payment_status"
    ],

    "diagnostic": [
        "diagnostic_id",
        "patient_id",
        "visit_id",
        "hospital_id",
        "department_id",
        "doctor_id",
        "test_date",
        "test_name",
        "test_category",
        "test_status",
        "amount"
    ],

    "surgery": [
        "procedure_id",
        "patient_id",
        "admission_id",
        "hospital_id",
        "department_id",
        "doctor_id",
        "procedure_date",
        "procedure_name",
        "procedure_category",
        "procedure_status",
        "cost"
    ]
}


# ========================================
# Check Columns
# ========================================

column_failures = 0

for table_name, expected in expected_columns.items():

    actual = list(tables[table_name].columns)

    missing_columns = [
        column
        for column in expected
        if column not in actual
    ]

    unexpected_columns = [
        column
        for column in actual
        if column not in expected
    ]

    if missing_columns:

        column_failures += 1

        print(
            f"✗ {table_name}: "
            f"missing columns {missing_columns}"
        )

    if unexpected_columns:

        column_failures += 1

        print(
            f"✗ {table_name}: "
            f"unexpected columns {unexpected_columns}"
        )

    if not missing_columns and not unexpected_columns:

        print(
            f"✓ {table_name} columns"
        )


quality_failures += column_failures


# ========================================
# Required / Non-null Columns
# ========================================

required_columns = {

    "hospital": [
        "hospital_id",
        "hospital_name",
        "city",
        "state",
        "hospital_type",
        "bed_capacity"
    ],

    "department": [
        "department_id",
        "department_name",
        "hospital_id"
    ],

    "doctor": [
        "doctor_id",
        "doctor_name",
        "hospital_id",
        "department_id",
        "specialization",
        "experience_years",
        "consultation_fee",
        "joining_date"
    ],

    "patient": [
        "patient_id",
        "patient_name",
        "gender",
        "date_of_birth",
        "age",
        "city",
        "registration_date",
        "insurance_type"
    ],

    "visit": [
        "visit_id",
        "patient_id",
        "hospital_id",
        "department_id",
        "doctor_id",
        "visit_date",
        "visit_type",
        "visit_status",
        "consultation_fee",
        "source"
    ],

    "admission": [
        "admission_id",
        "patient_id",
        "hospital_id",
        "department_id",
        "doctor_id",
        "admission_date",
        "admission_type",
        "ward_type",
        "diagnosis_category",
        "length_of_stay",
        "admission_status"
    ],

    "billing": [
        "bill_id",
        "patient_id",
        "hospital_id",
        "department_id",
        "bill_date",
        "bill_category",
        "gross_amount",
        "discount_amount",
        "insurance_amount",
        "patient_amount",
        "total_amount",
        "payment_status"
    ],

    "diagnostic": [
        "diagnostic_id",
        "patient_id",
        "visit_id",
        "hospital_id",
        "department_id",
        "doctor_id",
        "test_date",
        "test_name",
        "test_category",
        "test_status",
        "amount"
    ],

    "surgery": [
        "procedure_id",
        "patient_id",
        "admission_id",
        "hospital_id",
        "department_id",
        "doctor_id",
        "procedure_date",
        "procedure_name",
        "procedure_category",
        "procedure_status",
        "cost"
    ]
}


null_failures = 0

for table_name, columns in required_columns.items():

    df = tables[table_name]

    table_null_failures = 0

    for column in columns:

        null_count = df[column].isna().sum()

        if null_count > 0:

            table_null_failures += 1

            print(
                f"✗ {table_name}.{column}: "
                f"{null_count} null values"
            )

    if table_null_failures == 0:

        print(
            f"✓ {table_name} required fields"
        )

    null_failures += table_null_failures


quality_failures += null_failures


# ========================================
# Allowed Category Values
# ========================================

allowed_values = {

    "hospital": {
        "hospital_type": [
            "Multi-Specialty"
        ]
    },

    "patient": {
        "gender": [
            "Male",
            "Female"
        ],
        "insurance_type": [
            "Insurance",
            "Self Pay",
            "Corporate"
        ]
    },

    "visit": {
        "visit_type": [
            "OP",
            "IP",
            "Emergency"
        ],
        "visit_status": [
            "Completed",
            "Cancelled"
        ],
        "source": [
            "Walk-in",
            "Appointment",
            "Referral"
        ]
    },

    "admission": {
        "admission_type": [
            "Emergency",
            "Planned"
        ],
        "ward_type": [
            "General",
            "Semi-Private",
            "Private",
            "ICU"
        ],
        "admission_status": [
            "Discharged",
            "Ongoing"
        ]
    },

    "billing": {
        "bill_category": [
            "Consultation",
            "Procedure",
            "Room",
            "Pharmacy",
            "Diagnostic",
            "Surgery"
        ],
        "payment_status": [
            "Paid",
            "Pending",
            "Partial"
        ]
    },

    "diagnostic": {
        "test_name": [
            "CBC",
            "Blood Sugar",
            "Lipid Profile",
            "ECG",
            "X-Ray",
            "CT Scan",
            "MRI",
            "Ultrasound",
            "Kidney Function Test",
            "Liver Function Test"
        ],
        "test_category": [
            "Pathology",
            "Radiology",
            "Cardiology"
        ],
        "test_status": [
            "Completed",
            "Pending"
        ]
    },

    "surgery": {
        "procedure_category": [
            "Surgery",
            "Procedure"
        ],
        "procedure_status": [
            "Completed",
            "Cancelled"
        ]
    }
}


category_failures = 0

for table_name, column_rules in allowed_values.items():

    df = tables[table_name]

    table_failed = False

    for column, allowed in column_rules.items():

        invalid_values = df[
            ~df[column].isin(allowed)
        ][column].dropna().unique()

        if len(invalid_values) > 0:

            category_failures += 1
            table_failed = True

            print(
                f"✗ {table_name}.{column}: "
                f"invalid values {list(invalid_values)}"
            )

    if not table_failed:

        print(
            f"✓ {table_name} category values"
        )


quality_failures += category_failures


# ========================================
# Patient Age Validation
# ========================================

patient_age_failures = 0

patients = tables["patient"].copy()

patients["date_of_birth"] = pd.to_datetime(
    patients["date_of_birth"],
    errors="coerce"
)

today = pd.Timestamp.today().normalize()

for _, row in patients.iterrows():

    patient_id = row["patient_id"]

    dob = row["date_of_birth"]

    age = row["age"]

    if pd.isna(dob):

        patient_age_failures += 1

        print(
            f"✗ Patient {patient_id}: "
            f"invalid date_of_birth"
        )

        continue

    # DOB cannot be in future

    if dob > today:

        patient_age_failures += 1

        print(
            f"✗ Patient {patient_id}: "
            f"date_of_birth is in the future"
        )

        continue

    # Calculate expected age

    expected_age = (
        today.year
        - dob.year
        - (
            (today.month, today.day)
            < (dob.month, dob.day)
        )
    )

    if age != expected_age:

        patient_age_failures += 1

        print(
            f"✗ Patient {patient_id}: "
            f"age mismatch "
            f"(expected {expected_age}, "
            f"got {age})"
        )


if patient_age_failures == 0:

    print(
        "✓ Patient age ↔ date_of_birth"
    )

quality_failures += patient_age_failures


# ========================================
# Doctor Specialization Validation
# ========================================
# ========================================
# Doctor Specialization Validation
# ========================================

doctor_specialization_failures = 0

departments = tables["department"].copy()

department_lookup = (
    departments
    .set_index("department_id")
    ["department_name"]
    .to_dict()
)

# Department → Specialization mapping
specialization_map = {
    "General Medicine": "General Physician",
    "Emergency & Critical Care": "Emergency Medicine",
    "Pediatrics": "Pediatrician",
    "Cardiology": "Cardiologist",
    "Orthopedics": "Orthopedic Specialist",
    "Obstetrics & Gynaecology":
        "Obstetrician & Gynaecologist",
    "Pulmonology": "Pulmonologist",
    "Gastroenterology": "Gastroenterologist",
    "Neurology": "Neurologist",
    "Nephrology": "Nephrologist",
    "Urology": "Urologist",
    "General Surgery": "General Surgeon",
    "Oncology": "Oncologist",
    "ENT": "ENT Specialist",
    "Dermatology": "Dermatologist"
}

doctors = tables["doctor"]

for _, row in doctors.iterrows():

    doctor_id = row["doctor_id"]

    department_id = row["department_id"]

    specialization = row[
        "specialization"
    ]

    department_name = department_lookup.get(
        department_id
    )

    expected_specialization = (
        specialization_map.get(
            department_name
        )
    )

    if (
        expected_specialization is not None
        and
        specialization
        != expected_specialization
    ):

        doctor_specialization_failures += 1

        print(
            f"✗ Doctor {doctor_id}: "
            f"specialization does not match "
            f"department"
        )


if doctor_specialization_failures == 0:

    print(
        "✓ Doctor specialization ↔ department"
    )

quality_failures += doctor_specialization_failures


# ========================================
# Data Quality Summary
# ========================================

print("----------------------------------------")

print(
    f"Schema/data quality failures : "
    f"{quality_failures}"
)

# ========================================
# Test 8 — Realism & Distribution Validation
# ========================================

print("\n========================================")
print("8. REALISM & DISTRIBUTION VALIDATION")
print("========================================")

realism_failures = 0


# ========================================
# Helper
# ========================================

def check_categories(
    df,
    column,
    expected_values,
    table_name
):
    failures = 0

    counts = df[column].value_counts()

    for value in expected_values:

        count = counts.get(value, 0)

        if count == 0:

            failures += 1

            print(
                f"✗ {table_name}.{column}: "
                f"category '{value}' has 0 records"
            )

    return failures


# ========================================
# 1. Every Hospital Should Have
#    Departments
# ========================================

hospital_department_counts = (
    tables["department"]
    .groupby("hospital_id")
    .size()
)

hospital_failures = 0

for hospital_id in tables["hospital"]["hospital_id"]:

    count = hospital_department_counts.get(
        hospital_id,
        0
    )

    if count == 0:

        hospital_failures += 1

        print(
            f"✗ Hospital {hospital_id}: "
            f"no departments"
        )


if hospital_failures == 0:

    print(
        "✓ Every hospital has departments"
    )

realism_failures += hospital_failures


# ========================================
# 2. Every Hospital Should Have Doctors
# ========================================

hospital_doctor_counts = (
    tables["doctor"]
    .groupby("hospital_id")
    .size()
)

doctor_hospital_failures = 0

for hospital_id in tables["hospital"]["hospital_id"]:

    count = hospital_doctor_counts.get(
        hospital_id,
        0
    )

    if count == 0:

        doctor_hospital_failures += 1

        print(
            f"✗ Hospital {hospital_id}: "
            f"no doctors"
        )


if doctor_hospital_failures == 0:

    print(
        "✓ Every hospital has doctors"
    )

realism_failures += doctor_hospital_failures


# ========================================
# 3. Every Department Should Have
#    At Least One Doctor
# ========================================

department_doctor_counts = (
    tables["doctor"]
    .groupby("department_id")
    .size()
)

department_failures = 0

for department_id in tables["department"]["department_id"]:

    count = department_doctor_counts.get(
        department_id,
        0
    )

    if count == 0:

        department_failures += 1

        print(
            f"✗ Department {department_id}: "
            f"no doctors"
        )


if department_failures == 0:

    print(
        "✓ Every department has doctors"
    )

realism_failures += department_failures


# ========================================
# 4. Patient Age Range
# ========================================

patient_age_failures = 0

patients = tables["patient"]

invalid_ages = patients[
    (patients["age"] < 1)
    |
    (patients["age"] > 90)
]

if len(invalid_ages) > 0:

    patient_age_failures = len(
        invalid_ages
    )

    print(
        f"✗ Patient ages outside "
        f"1-90 range: "
        f"{patient_age_failures}"
    )

else:

    print(
        "✓ Patient ages within "
        "configured range"
    )

realism_failures += patient_age_failures


# ========================================
# 5. Visit Category Coverage
# ========================================

visit_failures = 0

visit_failures += check_categories(
    tables["visit"],
    "visit_type",
    [
        "OP",
        "IP",
        "Emergency"
    ],
    "visit"
)

visit_failures += check_categories(
    tables["visit"],
    "visit_status",
    [
        "Completed",
        "Cancelled"
    ],
    "visit"
)

visit_failures += check_categories(
    tables["visit"],
    "source",
    [
        "Walk-in",
        "Appointment",
        "Referral"
    ],
    "visit"
)

if visit_failures == 0:

    print(
        "✓ Visit categories represented"
    )

realism_failures += visit_failures


# ========================================
# 6. Admission Category Coverage
# ========================================

admission_category_failures = 0

admission_category_failures += check_categories(
    tables["admission"],
    "admission_type",
    [
        "Emergency",
        "Planned"
    ],
    "admission"
)

admission_category_failures += check_categories(
    tables["admission"],
    "ward_type",
    [
        "General",
        "Semi-Private",
        "Private",
        "ICU"
    ],
    "admission"
)

admission_category_failures += check_categories(
    tables["admission"],
    "admission_status",
    [
        "Discharged",
        "Ongoing"
    ],
    "admission"
)

if admission_category_failures == 0:

    print(
        "✓ Admission categories represented"
    )

realism_failures += admission_category_failures


# ========================================
# 7. Billing Category Coverage
# ========================================

billing_category_failures = 0

billing_category_failures += check_categories(
    tables["billing"],
    "bill_category",
    [
        "Consultation",
        "Procedure",
        "Room",
        "Pharmacy",
        "Diagnostic",
        "Surgery"
    ],
    "billing"
)

billing_category_failures += check_categories(
    tables["billing"],
    "payment_status",
    [
        "Paid",
        "Pending",
        "Partial"
    ],
    "billing"
)

if billing_category_failures == 0:

    print(
        "✓ Billing categories represented"
    )

realism_failures += billing_category_failures


# ========================================
# 8. Diagnostic Category Coverage
# ========================================

diagnostic_category_failures = 0

diagnostic_category_failures += check_categories(
    tables["diagnostic"],
    "test_category",
    [
        "Pathology",
        "Radiology",
        "Cardiology"
    ],
    "diagnostic"
)

diagnostic_category_failures += check_categories(
    tables["diagnostic"],
    "test_status",
    [
        "Completed",
        "Pending"
    ],
    "diagnostic"
)

if diagnostic_category_failures == 0:

    print(
        "✓ Diagnostic categories represented"
    )

realism_failures += diagnostic_category_failures


# ========================================
# 9. Surgery Category Coverage
# ========================================

surgery_category_failures = 0

surgery_category_failures += check_categories(
    tables["surgery"],
    "procedure_category",
    [
        "Surgery",
        "Procedure"
    ],
    "surgery"
)

surgery_category_failures += check_categories(
    tables["surgery"],
    "procedure_status",
    [
        "Completed",
        "Cancelled"
    ],
    "surgery"
)

if surgery_category_failures == 0:

    print(
        "✓ Surgery categories represented"
    )

realism_failures += surgery_category_failures


# ========================================
# 10. Doctor Experience Range
# ========================================

doctor_experience_failures = 0

doctors = tables["doctor"]

invalid_experience = doctors[
    (doctors["experience_years"] < 2)
    |
    (doctors["experience_years"] > 30)
]

if len(invalid_experience) > 0:

    doctor_experience_failures = len(
        invalid_experience
    )

    print(
        f"✗ Doctor experience outside "
        f"2-30 years: "
        f"{doctor_experience_failures}"
    )

else:

    print(
        "✓ Doctor experience within "
        "configured range"
    )

realism_failures += doctor_experience_failures


# ========================================
# 11. Consultation Fee Range
# ========================================

consultation_fee_failures = 0

invalid_fees = doctors[
    (doctors["consultation_fee"] < 500)
    |
    (doctors["consultation_fee"] > 2500)
]

if len(invalid_fees) > 0:

    consultation_fee_failures = len(
        invalid_fees
    )

    print(
        f"✗ Consultation fees outside "
        f"500-2500 range: "
        f"{consultation_fee_failures}"
    )

else:

    print(
        "✓ Consultation fees within "
        "configured range"
    )

realism_failures += consultation_fee_failures


# ========================================
# 12. Basic Workload Distribution
# ========================================

visit_hospital_counts = (
    tables["visit"]
    .groupby("hospital_id")
    .size()
)

workload_failures = 0

for hospital_id in tables["hospital"]["hospital_id"]:

    count = visit_hospital_counts.get(
        hospital_id,
        0
    )

    if count == 0:

        workload_failures += 1

        print(
            f"✗ Hospital {hospital_id}: "
            f"no patient visits"
        )


if workload_failures == 0:

    print(
        "✓ All hospitals have patient visits"
    )

realism_failures += workload_failures


# ========================================
# 13. Patient Visit Activity
# ========================================

patient_visit_counts = (
    tables["visit"]
    .groupby("patient_id")
    .size()
)

patients_with_visits = (
    patients["patient_id"]
    .isin(patient_visit_counts.index)
    .sum()
)

if patients_with_visits == 0:

    print(
        "✗ No patients have visits"
    )

    realism_failures += 1

else:

    print(
        f"✓ Patient visit activity "
        f"({patients_with_visits}/"
        f"{len(patients)} patients)"
    )


# ========================================
# 14. Billing Category Coverage
#     vs Generated Billing Count
# ========================================

billing_count = len(
    tables["billing"]
)

if billing_count == 0:

    print(
        "✗ No billing records generated"
    )

    realism_failures += 1

else:

    print(
        f"✓ Billing activity present "
        f"({billing_count} records)"
    )


# ========================================
# Realism Summary
# ========================================

print("----------------------------------------")

print(
    f"Realism/distribution failures : "
    f"{realism_failures}"
)

# ========================================
# Final Summary
# ========================================

print("\n========================================")
print("VALIDATION SUMMARY")
print("========================================")

print(
    f"Record count failures      : "
    f"{count_failures}"
)

print(
    f"Primary key failures       : "
    f"{primary_key_failures}"
)

print(
    f"Foreign key failures       : "
    f"{foreign_key_failures}"
)

print(
    f"Relationship failures      : "
    f"{relationship_failures}"
)

print(
    f"Date/business failures     : "
    f"{date_failures}"
)

print(
    f"Financial failures         : "
    f"{financial_failures}"
)

print(
    f"Schema/data quality failures : "
    f"{quality_failures}"
)

print(
    f"Realism/distribution failures : "
    f"{realism_failures}"
)

total_failures = (
    count_failures
    + primary_key_failures
    + foreign_key_failures
    + relationship_failures
    + date_failures
    + financial_failures
    + quality_failures
    + realism_failures
)

print("----------------------------------------")

if total_failures == 0:

    print("✓ ALL VALIDATIONS PASSED")

else:

    print(
        f"✗ {total_failures} VALIDATION "
        f"FAILURES FOUND"
    )

print("========================================")