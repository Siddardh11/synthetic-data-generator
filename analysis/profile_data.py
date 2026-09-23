import pandas as pd
from pathlib import Path


# ========================================
# Paths
# ========================================

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"


# ========================================
# Load data
# ========================================

hospital = pd.read_csv(OUTPUT_DIR / "hospital.csv")
department = pd.read_csv(OUTPUT_DIR / "department.csv")
doctor = pd.read_csv(OUTPUT_DIR / "doctor.csv")
patient = pd.read_csv(OUTPUT_DIR / "patient.csv")
visit = pd.read_csv(OUTPUT_DIR / "visit.csv")
admission = pd.read_csv(OUTPUT_DIR / "admission.csv")
billing = pd.read_csv(OUTPUT_DIR / "billing.csv")
diagnostic = pd.read_csv(OUTPUT_DIR / "diagnostic_test.csv")
surgery = pd.read_csv(OUTPUT_DIR / "surgery.csv")


# ========================================
# Helper
# ========================================

def print_section(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


# ========================================
# 1. Hospital Visit Distribution
# ========================================

print_section("1. VISITS BY HOSPITAL")

hospital_visits = (
    visit.groupby("hospital_id")
    .size()
    .sort_values(ascending=False)
)

print(hospital_visits)


# ========================================
# 2. Department Visit Distribution
# ========================================

print_section("2. VISITS BY DEPARTMENT")

department_visits = (
    visit.groupby("department_id")
    .size()
    .sort_values(ascending=False)
)

print(department_visits)


# ========================================
# 3. Doctor Workload
# ========================================

print_section("3. DOCTOR WORKLOAD")

doctor_workload = (
    visit.groupby("doctor_id")
    .size()
    .sort_values(ascending=False)
)

print(doctor_workload.head(20))

print("\nDoctor workload statistics:")
print(doctor_workload.describe())


# ========================================
# 4. Patient Visit Frequency
# ========================================

print_section("4. PATIENT VISIT FREQUENCY")

patient_visits = (
    visit.groupby("patient_id")
    .size()
)

visit_frequency = (
    patient_visits
    .value_counts()
    .sort_index()
)

print(visit_frequency)

print("\nMeaning:")
print("1 = patients with 1 visit")
print("2 = patients with 2 visits")
print("3 = patients with 3 visits")
print("etc.")


# ========================================
# 5. Visit Type Distribution
# ========================================

print_section("5. VISIT TYPE DISTRIBUTION")

print(
    visit["visit_type"]
    .value_counts()
)

print("\nPercentage:")

print(
    visit["visit_type"]
    .value_counts(normalize=True)
    .mul(100)
    .round(2)
)


# ========================================
# 6. Visit Status Distribution
# ========================================

print_section("6. VISIT STATUS DISTRIBUTION")

print(
    visit["visit_status"]
    .value_counts()
)

print(
    visit["visit_status"]
    .value_counts(normalize=True)
    .mul(100)
    .round(2)
)


# ========================================
# 7. Admission Type Distribution
# ========================================

print_section("7. ADMISSION TYPE DISTRIBUTION")

print(
    admission["admission_type"]
    .value_counts()
)

print(
    admission["admission_type"]
    .value_counts(normalize=True)
    .mul(100)
    .round(2)
)


# ========================================
# 8. Ward Distribution
# ========================================

print_section("8. WARD DISTRIBUTION")

print(
    admission["ward_type"]
    .value_counts()
)

print(
    admission["ward_type"]
    .value_counts(normalize=True)
    .mul(100)
    .round(2)
)


# ========================================
# 9. Diagnostic Test Distribution
# ========================================

print_section("9. DIAGNOSTIC TEST DISTRIBUTION")

print(
    diagnostic["test_name"]
    .value_counts()
)


# ========================================
# 10. Billing Category Distribution
# ========================================

print_section("10. BILLING CATEGORY DISTRIBUTION")

print(
    billing["bill_category"]
    .value_counts()
)

print(
    billing["bill_category"]
    .value_counts(normalize=True)
    .mul(100)
    .round(2)
)


# ========================================
# 11. Payment Status Distribution
# ========================================

print_section("11. PAYMENT STATUS DISTRIBUTION")

print(
    billing["payment_status"]
    .value_counts()
)

print(
    billing["payment_status"]
    .value_counts(normalize=True)
    .mul(100)
    .round(2)
)


# ========================================
# 12. Monthly Visit Volume
# ========================================

print_section("12. MONTHLY VISIT VOLUME")

visit["visit_date"] = pd.to_datetime(
    visit["visit_date"]
)

monthly_visits = (
    visit
    .set_index("visit_date")
    .resample("ME")
    .size()
)

print(monthly_visits)


# ========================================
# 13. Revenue By Hospital
# ========================================

print_section("13. REVENUE BY HOSPITAL")

revenue_by_hospital = (
    billing
    .groupby("hospital_id")["total_amount"]
    .sum()
    .sort_values(ascending=False)
)

print(revenue_by_hospital)


# ========================================
# 14. Revenue By Department
# ========================================

print_section("14. REVENUE BY DEPARTMENT")

revenue_by_department = (
    billing
    .groupby("department_id")["total_amount"]
    .sum()
    .sort_values(ascending=False)
)

print(revenue_by_department)


# ========================================
# 15. Admission Length of Stay
# ========================================

print_section("15. LENGTH OF STAY")

print(
    admission["length_of_stay"]
    .describe()
)


# ========================================
# 16. Surgery Distribution
# ========================================

print_section("16. SURGERY / PROCEDURE DISTRIBUTION")

print(
    surgery["procedure_category"]
    .value_counts()
)

print(
    surgery["procedure_status"]
    .value_counts()
)


# ========================================
# 17. BILLING BY WARD TYPE
# ========================================

print_section("17. BILLING BY WARD TYPE")

# Link billing records to admissions.
#
# Only billing records containing admission_id
# will be included in this analysis.

billing_with_admission = billing.merge(
    admission[
        [
            "admission_id",
            "ward_type",
            "length_of_stay"
        ]
    ],
    on="admission_id",
    how="inner"
)

print("\nAverage total billing by ward:")

ward_billing_summary = (
    billing_with_admission
    .groupby("ward_type")["total_amount"]
    .agg(
        [
            "count",
            "mean",
            "median",
            "min",
            "max"
        ]
    )
    .sort_values("mean", ascending=False)
)

print(ward_billing_summary)


# ========================================
# 18. ROOM BILLING BY WARD
# ========================================

print_section("18. ROOM BILLING BY WARD")

room_billing = billing_with_admission[
    billing_with_admission["bill_category"] == "Room"
]

if not room_billing.empty:

    room_billing_summary = (
        room_billing
        .groupby("ward_type")["total_amount"]
        .agg(
            [
                "count",
                "mean",
                "median",
                "min",
                "max"
            ]
        )
        .sort_values("mean", ascending=False)
    )

    print(room_billing_summary)

else:
    print("No room billing records found.")


# ========================================
# 19. PHARMACY BILLING BY WARD
# ========================================

print_section("19. PHARMACY BILLING BY WARD")

pharmacy_billing = billing_with_admission[
    billing_with_admission["bill_category"] == "Pharmacy"
]

if not pharmacy_billing.empty:

    pharmacy_billing_summary = (
        pharmacy_billing
        .groupby("ward_type")["total_amount"]
        .agg(
            [
                "count",
                "mean",
                "median",
                "min",
                "max"
            ]
        )
        .sort_values("mean", ascending=False)
    )

    print(pharmacy_billing_summary)

else:
    print("No pharmacy billing records found.")


# ========================================
# 20. LENGTH OF STAY VS BILLING
# ========================================

print_section("20. LENGTH OF STAY VS BILLING")

los_billing = (
    billing_with_admission
    .groupby("length_of_stay")["total_amount"]
    .agg(
        [
            "count",
            "mean",
            "median"
        ]
    )
    .sort_index()
)

print(los_billing)


# ========================================
# LOS / BILLING CORRELATION
# ========================================

if len(billing_with_admission) > 1:

    los_correlation = (
        billing_with_admission[
            [
                "length_of_stay",
                "total_amount"
            ]
        ]
        .corr()
        .loc[
            "length_of_stay",
            "total_amount"
        ]
    )

    print("\nCorrelation between LOS and total billing:")
    print(round(los_correlation, 3))

else:

    los_correlation = None

    print("\nNot enough data to calculate LOS correlation.")


# ========================================
# 21. BILLING BY SURGERY / PROCEDURE
# ========================================

print_section("21. BILLING BY SURGERY / PROCEDURE")

# We do NOT assume that surgery.csv contains
# a procedure_cost column.
#
# Instead, we first identify admissions that
# have a surgery/procedure.

procedure_admissions = (
    surgery["admission_id"]
    .dropna()
    .drop_duplicates()
)

# Mark admissions that contain a procedure.

admission_procedure_flag = admission[
    ["admission_id"]
].copy()

admission_procedure_flag["has_procedure"] = (
    admission_procedure_flag["admission_id"]
    .isin(procedure_admissions)
)

# Calculate total billing for each admission.

admission_total_billing = (
    billing_with_admission
    .groupby("admission_id")["total_amount"]
    .sum()
    .reset_index()
)

# Combine procedure information with billing.

procedure_billing_analysis = admission_procedure_flag.merge(
    admission_total_billing,
    on="admission_id",
    how="left"
)

procedure_billing_analysis["total_amount"] = (
    procedure_billing_analysis["total_amount"]
    .fillna(0)
)

print("\nAverage total admission billing:")

procedure_summary = (
    procedure_billing_analysis
    .groupby("has_procedure")["total_amount"]
    .agg(
        [
            "count",
            "mean",
            "median",
            "min",
            "max"
        ]
    )
)

procedure_summary.index = [
    "No Procedure",
    "Has Procedure"
]

print(procedure_summary)


# ========================================
# Procedure Category Analysis
# ========================================

print("\nBilling by procedure category:")

procedure_categories = surgery[
    [
        "admission_id",
        "procedure_category",
        "procedure_status"
    ]
].drop_duplicates()

procedure_category_billing = procedure_categories.merge(
    admission_total_billing,
    on="admission_id",
    how="left"
)

procedure_category_billing["total_amount"] = (
    procedure_category_billing["total_amount"]
    .fillna(0)
)

print(
    procedure_category_billing
    .groupby("procedure_category")["total_amount"]
    .agg(
        [
            "count",
            "mean",
            "median",
            "min",
            "max"
        ]
    )
    .sort_values("mean", ascending=False)
)


# ========================================
# 22. DIAGNOSTIC BILLING
# ========================================

print_section("22. DIAGNOSTIC BILLING")

# Link diagnostic tests to billing through visit_id.

billing_with_diagnostic = billing.merge(
    diagnostic[
        [
            "visit_id",
            "test_name"
        ]
    ],
    on="visit_id",
    how="inner"
)

diagnostic_billing = billing_with_diagnostic[
    billing_with_diagnostic["bill_category"] == "Diagnostic"
]

if not diagnostic_billing.empty:

    print("\nDiagnostic billing by test:")

    diagnostic_billing_summary = (
        diagnostic_billing
        .groupby("test_name")["total_amount"]
        .agg(
            [
                "count",
                "mean",
                "median",
                "min",
                "max"
            ]
        )
        .sort_values("mean", ascending=False)
    )

    print(diagnostic_billing_summary)

else:

    print("No diagnostic billing records found.")


# ========================================
# 23. BILLING PER DAY OF STAY
# ========================================

print_section("23. BILLING PER DAY OF STAY")

# First calculate total billing per admission.

admission_billing = (
    billing_with_admission
    .groupby(
        [
            "admission_id",
            "ward_type",
            "length_of_stay"
        ]
    )["total_amount"]
    .sum()
    .reset_index()
)

# Avoid division by zero.

admission_billing["billing_per_day"] = (
    admission_billing["total_amount"]
    /
    admission_billing["length_of_stay"].clip(lower=1)
)

print(
    admission_billing
    .groupby("ward_type")["billing_per_day"]
    .agg(
        [
            "count",
            "mean",
            "median",
            "min",
            "max"
        ]
    )
    .sort_values("mean", ascending=False)
)


# ========================================
# 24. BILLING CORRELATION SUMMARY
# ========================================

print_section("24. BILLING CORRELATION SUMMARY")


# ----------------------------------------
# Ward billing
# ----------------------------------------

print("Average admission-related billing by ward:")

print(
    billing_with_admission
    .groupby("ward_type")["total_amount"]
    .mean()
    .sort_values(ascending=False)
)


# ----------------------------------------
# Room billing
# ----------------------------------------

print("\nAverage room billing by ward:")

if not room_billing.empty:

    print(
        room_billing
        .groupby("ward_type")["total_amount"]
        .mean()
        .sort_values(ascending=False)
    )

else:

    print("No room billing records found.")


# ----------------------------------------
# Pharmacy billing
# ----------------------------------------

print("\nAverage pharmacy billing by ward:")

if not pharmacy_billing.empty:

    print(
        pharmacy_billing
        .groupby("ward_type")["total_amount"]
        .mean()
        .sort_values(ascending=False)
    )

else:

    print("No pharmacy billing records found.")


# ----------------------------------------
# LOS correlation
# ----------------------------------------

print("\nLOS vs total billing correlation:")

if los_correlation is not None:

    print(round(los_correlation, 3))

else:

    print("Not available.")


# ----------------------------------------
# Procedure comparison
# ----------------------------------------

print("\nAverage billing: admissions with vs without procedure:")

print(
    procedure_summary["mean"]
)


# ========================================
# 25. DATASET RECORD SUMMARY
# ========================================

print_section("25. DATASET RECORD SUMMARY")

print("Hospital records   :", len(hospital))
print("Department records :", len(department))
print("Doctor records     :", len(doctor))
print("Patient records    :", len(patient))
print("Visit records      :", len(visit))
print("Admission records  :", len(admission))
print("Billing records    :", len(billing))
print("Diagnostic records :", len(diagnostic))
print("Surgery records    :", len(surgery))


# ========================================
# Complete
# ========================================

print_section("PROFILE COMPLETE")

print("All profiling analysis completed successfully.")