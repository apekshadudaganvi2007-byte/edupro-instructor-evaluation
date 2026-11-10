import pandas as pd
import numpy as np
from scipy import stats

# 1. Load the Excel Sheets
file_path = "EduPro Online Platform.xlsx"
teachers = pd.read_excel(file_path, sheet_name="Teachers")
courses = pd.read_excel(file_path, sheet_name="Courses")
transactions = pd.read_excel(file_path, sheet_name="Transactions")

# Clean column names (strip accidental whitespace)
for df_temp in [teachers, courses, transactions]:
    df_temp.columns = df_temp.columns.str.strip()

print("--- DATA OVERVIEW ---")
print(f"Teachers: {teachers.shape[0]} rows | Missing: {teachers.isnull().sum().sum()}")
print(f"Courses: {courses.shape[0]} rows | Missing: {courses.isnull().sum().sum()}")
print(f"Transactions: {transactions.shape[0]} rows | Missing: {transactions.isnull().sum().sum()}")

# 2. Data Integration (Merge Transactions + Teachers + Courses)
df = transactions.merge(teachers, on="TeacherID", how="left").merge(courses, on="CourseID", how="left")

# 3. KPI Calculations per Instructor
instructor_kpis = df.groupby(
    ["TeacherID", "TeacherName", "Gender", "Expertise", "YearsOfExperience", "TeacherRating"]
).agg(
    TotalEnrollments=("TransactionID", "count"),
    UniqueCoursesTaught=("CourseID", "nunique"),
    AvgCourseRating=("CourseRating", "mean"),
    CourseRatingStd=("CourseRating", "std")
).reset_index()

# Rating Consistency Index (1 / (1 + std_dev); closer to 1.0 = highly consistent)
instructor_kpis["CourseRatingStd"] = instructor_kpis["CourseRatingStd"].fillna(0)
instructor_kpis["RatingConsistencyIndex"] = (1 / (1 + instructor_kpis["CourseRatingStd"])).round(3)

# Enrollment Influence Ratio (Enrollments per unit of TeacherRating)
instructor_kpis["EnrollmentInfluenceRatio"] = (
    instructor_kpis["TotalEnrollments"] / instructor_kpis["TeacherRating"]
).round(2)

# 4. Statistical & Analytical Insights (Use these numbers in your reports!)
print("\n--- CORE KPIS ---")
print(f"Overall Average Teacher Rating: {teachers['TeacherRating'].mean():.2f}")
print(f"Overall Average Course Rating: {courses['CourseRating'].mean():.2f}")
print(f"Total Enrollments Analyzed: {len(df)}")

# Experience Impact Score (Pearson Correlation)
corr_teacher, p_val_t = stats.pearsonr(teachers["YearsOfExperience"], teachers["TeacherRating"])
corr_course, p_val_c = stats.pearsonr(instructor_kpis["YearsOfExperience"], instructor_kpis["AvgCourseRating"])
print("\n--- EXPERIENCE IMPACT ---")
print(f"Experience vs Teacher Rating Correlation (r): {corr_teacher:.3f} (p={p_val_t:.4f})")
print(f"Experience vs Avg Course Rating Correlation (r): {corr_course:.3f} (p={p_val_c:.4f})")

# Enrollment vs Teacher Rating Correlation
corr_enroll, p_val_e = stats.pearsonr(instructor_kpis["TeacherRating"], instructor_kpis["TotalEnrollments"])
print(f"Teacher Rating vs Total Enrollments Correlation (r): {corr_enroll:.3f} (p={p_val_e:.4f})")

print("\n--- TOP 5 INSTRUCTORS BY TEACHER RATING ---")
print(instructor_kpis.sort_values(by=["TeacherRating", "TotalEnrollments"], ascending=False)[
    ["TeacherName", "Expertise", "YearsOfExperience", "TeacherRating", "AvgCourseRating", "TotalEnrollments", "RatingConsistencyIndex"]
].head(5).to_string(index=False))

print("\n--- BOTTOM 5 INSTRUCTORS BY TEACHER RATING ---")
print(instructor_kpis.sort_values(by=["TeacherRating", "TotalEnrollments"], ascending=True)[
    ["TeacherName", "Expertise", "YearsOfExperience", "TeacherRating", "AvgCourseRating", "TotalEnrollments"]
].head(5).to_string(index=False))

print("\n--- COURSE RATING BY CATEGORY ---")
print(df.groupby("CourseCategory").agg(
    Enrollments=("TransactionID", "count"),
    AvgCourseRating=("CourseRating", "mean"),
    AvgTeacherRating=("TeacherRating", "mean")
).round(2).to_string())

print("\n--- COURSE RATING BY LEVEL ---")
print(df.groupby("CourseLevel").agg(
    Enrollments=("TransactionID", "count"),
    AvgCourseRating=("CourseRating", "mean"),
    AvgTeacherRating=("TeacherRating", "mean")
).round(2).to_string())

print("\n--- PERFORMANCE BY GENDER ---")
print(teachers.groupby("Gender").agg(
    Count=("TeacherID", "count"),
    AvgTeacherRating=("TeacherRating", "mean"),
    AvgExperience=("YearsOfExperience", "mean")
).round(2).to_string())

# Save processed summary for quick inspection
instructor_kpis.to_csv("instructor_kpi_summary.csv", index=False)
print("\nSaved 'instructor_kpi_summary.csv' successfully!")