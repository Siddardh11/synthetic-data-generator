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
# 13. DAY-OF-WEEK VISIT VOLUME
# ========================================

print_section("13. DAY-OF-WEEK VISIT VOLUME")

weekday_order = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday"
]

weekday_counts = (
    visit["visit_date"]
    .dt.day_name()
    .value_counts()
    .reindex(
        weekday_order,
        fill_value=0
    )
)

print(weekday_counts)

print("\nPercentage:")

weekday_percentage = (
    weekday_counts
    / weekday_counts.sum()
    * 100
)

print(
    weekday_percentage.round(2)
)


# ========================================
# 14. Revenue By Hospital
# ========================================

print_section("14. REVENUE BY HOSPITAL")

revenue_by_hospital = (
    billing
    .groupby("hospital_id")["total_amount"]
    .sum()
    .sort_values(ascending=False)
)

print(revenue_by_hospital)


# ========================================
# 15. Revenue By Department
# ========================================

print_section("15. REVENUE BY DEPARTMENT")

revenue_by_department = (
    billing
    .groupby("department_id")["total_amount"]
    .sum()
    .sort_values(ascending=False)
)

print(revenue_by_department)


# ========================================
# 16. Admission Length of Stay
# ========================================

print_section("16. LENGTH OF STAY")

print(
    admission["length_of_stay"]
    .describe()
)


# ========================================
# 17. Surgery Distribution
# ========================================

print_section("17. SURGERY / PROCEDURE DISTRIBUTION")

print(
    surgery["procedure_category"]
    .value_counts()
)

print(
    surgery["procedure_status"]
    .value_counts()
)


# ========================================
# 18. BILLING BY WARD TYPE
# ========================================

print_section("18. BILLING BY WARD TYPE")

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
# 19. ROOM BILLING BY WARD
# ========================================

print_section("19. ROOM BILLING BY WARD")

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
# 20. PHARMACY BILLING BY WARD
# ========================================

print_section("20. PHARMACY BILLING BY WARD")

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
# 21. LENGTH OF STAY VS BILLING
# ========================================

print_section("21. LENGTH OF STAY VS BILLING")

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
# 22. BILLING BY SURGERY / PROCEDURE
# ========================================

print_section("22. BILLING BY SURGERY / PROCEDURE")

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
# 23. DIAGNOSTIC BILLING
# ========================================

print_section("23. DIAGNOSTIC BILLING")

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
# 24. BILLING PER DAY OF STAY
# ========================================

print_section("24. BILLING PER DAY OF STAY")

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
# 25. BILLING CORRELATION SUMMARY
# ========================================

print_section("25. BILLING CORRELATION SUMMARY")


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
# 26. DATE COVERAGE
# ========================================

print_section("26. DATE COVERAGE")

date_columns = {
    "patient.registration_date": patient["registration_date"],
    "visit.visit_date": visit["visit_date"],
    "admission.admission_date": admission["admission_date"],
    "billing.bill_date": billing["bill_date"],
    "diagnostic.test_date": diagnostic["test_date"],
    "surgery.procedure_date": surgery["procedure_date"],
}

date_summary = []

for column_name, series in date_columns.items():
    parsed = pd.to_datetime(series, errors="coerce")
    date_summary.append({
        "table_column": column_name,
        "min_date": parsed.min(),
        "max_date": parsed.max(),
        "null_dates": int(parsed.isna().sum()),
        "unique_dates": int(parsed.dt.date.nunique()),
    })

date_summary_df = pd.DataFrame(date_summary)
print(date_summary_df.to_string(index=False))

overall_min_date = min(
    x for x in date_summary_df["min_date"] if pd.notna(x)
)
overall_max_date = max(
    x for x in date_summary_df["max_date"] if pd.notna(x)
)

coverage_days = (overall_max_date - overall_min_date).days + 1
coverage_months = coverage_days / 30.4375

print("\nOverall minimum date:", overall_min_date.date())
print("Overall maximum date:", overall_max_date.date())
print("Coverage days:", coverage_days)
print("Approximate coverage months:", round(coverage_months, 2))
print(
    "Status:",
    "PASS" if 18 <= coverage_months <= 24 else "REVIEW"
)


# ========================================
# 27. YEAR / MONTH VISIT TRENDS
# ========================================

print_section("27. YEAR / MONTH VISIT TRENDS")

visit["visit_year"] = visit["visit_date"].dt.year
visit["visit_month"] = visit["visit_date"].dt.month

year_month_visits = (
    visit.groupby(["visit_year", "visit_month"])
    .size()
    .reset_index(name="visit_count")
)

print(year_month_visits.to_string(index=False))

print("\nVisits by year:")
print(visit["visit_year"].value_counts().sort_index())


# ========================================
# 28. QUARTERLY VISIT TRENDS
# ========================================

print_section("28. QUARTERLY VISIT TRENDS")

quarterly_visits = (
    visit.groupby(visit["visit_date"].dt.to_period("Q"))
    .size()
)

print(quarterly_visits)

print("\nQuarter percentages:")
print(
    (quarterly_visits / quarterly_visits.sum() * 100).round(2)
)


# ========================================
# 29. SEASONAL / MONTHLY VARIATION
# ========================================

print_section("29. SEASONAL / MONTHLY VARIATION")

monthly_counts = (
    visit.groupby(visit["visit_date"].dt.month)
    .size()
    .reindex(range(1, 13), fill_value=0)
)

monthly_summary = pd.DataFrame({
    "month": monthly_counts.index,
    "visit_count": monthly_counts.values,
    "percentage": (
        monthly_counts / monthly_counts.sum() * 100
    ).round(2),
})

print(monthly_summary.to_string(index=False))
print("\nHighest-volume month(s):")
print(monthly_counts[monthly_counts == monthly_counts.max()])
print("\nLowest-volume month(s):")
print(monthly_counts[monthly_counts == monthly_counts.min()])
print(
    "\nStatus:",
    "PASS" if monthly_counts.max() > monthly_counts.min()
    else "REVIEW"
)


# ========================================
# 30. ADMISSIONS BY HOSPITAL
# ========================================

print_section("30. ADMISSIONS BY HOSPITAL")

admissions_by_hospital = (
    admission.groupby("hospital_id")
    .size()
    .sort_values(ascending=False)
)

print(admissions_by_hospital)

print("\nPercentage:")
print(
    (admissions_by_hospital / admissions_by_hospital.sum() * 100).round(2)
)


# ========================================
# 31. ADMISSIONS BY DEPARTMENT
# ========================================

print_section("31. ADMISSIONS BY DEPARTMENT")

admissions_by_department = (
    admission.groupby("department_id")
    .size()
    .sort_values(ascending=False)
)

print(admissions_by_department)


# ========================================
# 32. ICU VS INPATIENT ACTIVITY
# ========================================

print_section("32. ICU VS INPATIENT ACTIVITY")

inpatient_visits = visit[
    visit["visit_type"].isin(["IP", "Inpatient"])
]

icu_admissions = admission[
    admission["ward_type"] == "ICU"
]

print("Total visits:", len(visit))
print("Inpatient visits:", len(inpatient_visits))
print("ICU admissions:", len(icu_admissions))

print(
    "Inpatient visit percentage:",
    round(len(inpatient_visits) / len(visit) * 100, 2),
    "%"
)

print(
    "ICU admission percentage:",
    round(len(icu_admissions) / len(admission) * 100, 2),
    "%"
)


# ========================================
# 33. DIAGNOSTIC TESTS BY DEPARTMENT
# ========================================

print_section("33. DIAGNOSTIC TESTS BY DEPARTMENT")

# Use department_id from the visit table explicitly.
# This avoids column-name collisions if diagnostic.csv
# already contains a department_id column.

visit_context = (
    visit[
        ["visit_id", "department_id", "hospital_id", "visit_type"]
    ]
    .rename(
        columns={
            "department_id": "visit_department_id",
            "hospital_id": "visit_hospital_id",
            "visit_type": "visit_type_from_visit",
        }
    )
)

diagnostic_department = diagnostic.merge(
    visit_context,
    on="visit_id",
    how="left",
)

print(
    diagnostic_department.groupby("visit_department_id")
    .size()
    .sort_values(ascending=False)
)

print("\nDiagnostic tests by test name:")
print(
    diagnostic["test_name"]
    .value_counts()
)


# ========================================
# 34. MULTIPLE ADMISSIONS PER PATIENT
# ========================================

print_section("34. MULTIPLE ADMISSIONS PER PATIENT")

patient_admissions = admission.groupby("patient_id").size()

admission_frequency = (
    patient_admissions.value_counts().sort_index()
)

print(admission_frequency)

multiple_admission_patients = patient_admissions[
    patient_admissions > 1
]

print(
    "\nPatients with multiple admissions:",
    len(multiple_admission_patients)
)

print(
    "Percentage of admitted patients with multiple admissions:",
    round(
        len(multiple_admission_patients)
        / patient_admissions.size
        * 100,
        2,
    ) if patient_admissions.size else 0,
    "%"
)


# ========================================
# 35. LENGTH OF STAY BY WARD / TYPE
# ========================================

print_section("35. LENGTH OF STAY BY WARD / ADMISSION TYPE")

print("\nLOS by ward:")
print(
    admission.groupby("ward_type")["length_of_stay"]
    .agg(["count", "mean", "median", "min", "max"])
    .sort_values("mean", ascending=False)
)

print("\nLOS by admission type:")
print(
    admission.groupby("admission_type")["length_of_stay"]
    .agg(["count", "mean", "median", "min", "max"])
    .sort_values("mean", ascending=False)
)


# ========================================
# 36. CONSULTATION FEE BY SPECIALIZATION
# ========================================

print_section("36. CONSULTATION FEE BY SPECIALIZATION")

print(
    doctor.groupby("specialization")["consultation_fee"]
    .agg(["count", "mean", "median", "min", "max"])
    .sort_values("mean", ascending=False)
)

print(
    "\nDistinct consultation fees:",
    doctor["consultation_fee"].nunique()
)


# ========================================
# 37. DOCTOR / DEPARTMENT / HOSPITAL CONSISTENCY
# ========================================

print_section("37. DOCTOR / DEPARTMENT / HOSPITAL CONSISTENCY")

doctor_lookup = doctor[
    ["doctor_id", "department_id", "hospital_id"]
].drop_duplicates("doctor_id")

visit_doctor_check = visit.merge(
    doctor_lookup,
    on="doctor_id",
    how="left",
    suffixes=("_visit", "_doctor"),
)

visit_department_mismatch = (
    visit_doctor_check["department_id_visit"]
    != visit_doctor_check["department_id_doctor"]
)

visit_hospital_mismatch = (
    visit_doctor_check["hospital_id_visit"]
    != visit_doctor_check["hospital_id_doctor"]
)

print(
    "Visit → Doctor department mismatches:",
    int(visit_department_mismatch.sum())
)

print(
    "Visit → Doctor hospital mismatches:",
    int(visit_hospital_mismatch.sum())
)

admission_doctor_check = admission.merge(
    doctor_lookup,
    on="doctor_id",
    how="left",
    suffixes=("_admission", "_doctor"),
)

admission_department_mismatch = (
    admission_doctor_check["department_id_admission"]
    != admission_doctor_check["department_id_doctor"]
)

admission_hospital_mismatch = (
    admission_doctor_check["hospital_id_admission"]
    != admission_doctor_check["hospital_id_doctor"]
)

print(
    "Admission → Doctor department mismatches:",
    int(admission_department_mismatch.sum())
)

print(
    "Admission → Doctor hospital mismatches:",
    int(admission_hospital_mismatch.sum())
)


# ========================================
# 38. FINANCIAL FORMULA CHECKS
# ========================================

print_section("38. FINANCIAL FORMULA CHECKS")

total_difference = (
    billing["gross_amount"]
    - billing["discount_amount"]
    - billing["total_amount"]
).abs()

insurance_patient_difference = (
    billing["insurance_amount"]
    + billing["patient_amount"]
    - billing["total_amount"]
).abs()

print(
    "Gross - discount != total:",
    int((total_difference > 0.01).sum())
)

print(
    "Insurance + patient != total:",
    int((insurance_patient_difference > 0.01).sum())
)

print(
    "Maximum gross/discount difference:",
    round(total_difference.max(), 4)
)

print(
    "Maximum insurance/patient difference:",
    round(insurance_patient_difference.max(), 4)
)


# ========================================
# 39. DATE LOGIC CHECKS
# ========================================

print_section("39. DATE LOGIC CHECKS")

admission_dates = pd.to_datetime(
    admission["admission_date"],
    errors="coerce",
)

discharge_dates = pd.to_datetime(
    admission["discharge_date"],
    errors="coerce",
)

discharged_mask = (
    admission["admission_status"] == "Discharged"
)

invalid_discharge_dates = (
    discharged_mask
    & discharge_dates.notna()
    & (discharge_dates < admission_dates)
)

calculated_los = (
    discharge_dates - admission_dates
).dt.days

los_mismatch = (
    discharged_mask
    & (
        calculated_los
        != admission["length_of_stay"]
    )
)

ongoing_with_discharge = (
    (admission["admission_status"] == "Ongoing")
    & discharge_dates.notna()
)

print(
    "Discharge date before admission date:",
    int(invalid_discharge_dates.sum())
)

print(
    "LOS calculation mismatches:",
    int(los_mismatch.sum())
)

print(
    "Ongoing admissions with discharge date:",
    int(ongoing_with_discharge.sum())
)


# ========================================
# 40. DATE FORMAT / NULL CHECK
# ========================================

print_section("40. DATE FORMAT / NULL CHECK")

table_objects = {
    "hospital": hospital,
    "department": department,
    "doctor": doctor,
    "patient": patient,
    "visit": visit,
    "admission": admission,
    "billing": billing,
    "diagnostic": diagnostic,
    "surgery": surgery,
}

print("Null values by table:")

for table_name, table_df in table_objects.items():
    print(
        f"{table_name:<12}: "
        f"{int(table_df.isna().sum().sum())}"
    )

print("\nDate parsing failures:")

for column_name, series in date_columns.items():
    invalid_count = int(
        pd.to_datetime(series, errors="coerce").isna().sum()
    )
    print(
        f"{column_name:<30}: {invalid_count}"
    )


# ========================================
# 41. DUPLICATE ID CHECK
# ========================================

print_section("41. DUPLICATE ID CHECK")

id_columns = {
    "hospital": "hospital_id",
    "department": "department_id",
    "doctor": "doctor_id",
    "patient": "patient_id",
    "visit": "visit_id",
    "admission": "admission_id",
    "billing": "bill_id",
    "diagnostic": "diagnostic_id",
    "surgery": "procedure_id",
}

duplicate_failures = []

for table_name, id_column in id_columns.items():

    table_df = table_objects[table_name]

    if id_column in table_df.columns:
        duplicate_count = int(
            table_df[id_column].duplicated().sum()
        )

        print(
            f"{table_name:<12}: "
            f"{duplicate_count} duplicate IDs"
        )

        if duplicate_count > 0:
            duplicate_failures.append(table_name)


# ========================================
# 42. CANCELLED VISITS
# ========================================

print_section("42. CANCELLED VISITS")

cancelled_visits = visit[
    visit["visit_status"] == "Cancelled"
]

print("Cancelled visits:", len(cancelled_visits))
print(
    "Cancelled percentage:",
    round(len(cancelled_visits) / len(visit) * 100, 2),
    "%"
)

print("\nCancelled visits by hospital:")
print(
    cancelled_visits.groupby("hospital_id")
    .size()
    .sort_values(ascending=False)
)

print("\nCancelled visits by department:")
print(
    cancelled_visits.groupby("department_id")
    .size()
    .sort_values(ascending=False)
)


# ========================================
# 43. PAYMENT STATUS / EDGE CASES
# ========================================

print_section("43. PAYMENT STATUS / EDGE CASES")

print("Payment status:")
print(billing["payment_status"].value_counts())

print(
    "\nOngoing admissions:",
    int((admission["admission_status"] == "Ongoing").sum())
)

print(
    "Cancelled visits:",
    len(cancelled_visits)
)

print(
    "Patients with repeat visits:",
    int((patient_visits > 1).sum())
)

print(
    "Patients with repeat admissions:",
    int((patient_admissions > 1).sum())
)

print("Diagnostic tests:", len(diagnostic))
print("Procedures / surgeries:", len(surgery))


# ========================================
# 44. CROSS-TABLE ACTIVITY SUMMARY
# ========================================

print_section("44. CROSS-TABLE ACTIVITY SUMMARY")

hospital_activity = pd.DataFrame({
    "visits": visit.groupby("hospital_id").size(),
    "admissions": admission.groupby("hospital_id").size(),
    "revenue": billing.groupby("hospital_id")["total_amount"].sum(),
}).fillna(0)

print(
    hospital_activity.sort_values(
        "visits",
        ascending=False
    )
)

department_activity = pd.DataFrame({
    "visits": visit.groupby("department_id").size(),
    "admissions": admission.groupby("department_id").size(),
    "revenue": billing.groupby("department_id")["total_amount"].sum(),
    "diagnostics": diagnostic_department.groupby("visit_department_id").size(),
}).fillna(0)

print("\nDepartment activity:")
print(
    department_activity.sort_values(
        "visits",
        ascending=False
    )
)


# ========================================
# 45. AUTOMATED STATUS SUMMARY
# ========================================

print_section("45. AUTOMATED STATUS SUMMARY")

status_results = {
    "18-24 month coverage":
        "PASS" if 18 <= coverage_months <= 24 else "REVIEW",

    "Monthly variation":
        "PASS" if monthly_counts.max() > monthly_counts.min()
        else "REVIEW",

    "Visit doctor-department relationship":
        "PASS" if not visit_department_mismatch.any()
        else "FAIL",

    "Visit doctor-hospital relationship":
        "PASS" if not visit_hospital_mismatch.any()
        else "FAIL",

    "Admission doctor-department relationship":
        "PASS" if not admission_department_mismatch.any()
        else "FAIL",

    "Admission doctor-hospital relationship":
        "PASS" if not admission_hospital_mismatch.any()
        else "FAIL",

    "Gross-discount-total":
        "PASS" if (total_difference <= 0.01).all()
        else "FAIL",

    "Insurance+patient-total":
        "PASS" if (insurance_patient_difference <= 0.01).all()
        else "FAIL",

    "Discharge >= admission":
        "PASS" if not invalid_discharge_dates.any()
        else "FAIL",

    "LOS calculation":
        "PASS" if not los_mismatch.any()
        else "FAIL",

    "Ongoing discharge handling":
        "PASS" if not ongoing_with_discharge.any()
        else "FAIL",

    "Duplicate primary IDs":
        "PASS" if not duplicate_failures
        else "FAIL",

    "Cancelled visits":
        "PASS" if len(cancelled_visits) > 0
        else "REVIEW",

    "Patient revisits":
        "PASS" if (patient_visits > 1).any()
        else "REVIEW",

    "Multiple admissions":
        "PASS" if (patient_admissions > 1).any()
        else "REVIEW",

    "Diagnostic test variation":
        "PASS" if diagnostic["test_name"].nunique() > 1
        else "REVIEW",

    "Consultation fee variation":
        "PASS" if doctor["consultation_fee"].nunique() > 1
        else "REVIEW",
}

status_df = pd.DataFrame({
    "requirement": list(status_results.keys()),
    "status": list(status_results.values()),
})

print(status_df.to_string(index=False))

print(
    "\nPASS:",
    int((status_df["status"] == "PASS").sum())
)

print(
    "REVIEW:",
    int((status_df["status"] == "REVIEW").sum())
)

print(
    "FAIL:",
    int((status_df["status"] == "FAIL").sum())
)




# ========================================
# 26. DATASET RECORD SUMMARY
# ========================================

print_section("26. DATASET RECORD SUMMARY")

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