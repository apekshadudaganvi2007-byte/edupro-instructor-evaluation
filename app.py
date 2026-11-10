import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="EduPro Instructor & Course Evaluation", layout="wide")

@st.cache_data
def load_data():
    file_path = "EduPro Online Platform.xlsx"
    teachers = pd.read_excel(file_path, sheet_name="Teachers")
    courses = pd.read_excel(file_path, sheet_name="Courses")
    transactions = pd.read_excel(file_path, sheet_name="Transactions")

    for d in [teachers, courses, transactions]:
        d.columns = d.columns.str.strip()

    df = transactions.merge(teachers, on="TeacherID", how="left").merge(courses, on="CourseID", how="left")
    return teachers, courses, transactions, df

teachers, courses, transactions, df = load_data()

# --- SIDEBAR CONTROLS ---
st.sidebar.header("Filter Dashboard")

expertise_options = sorted(df["Expertise"].dropna().unique())
selected_expertise = st.sidebar.multiselect("Instructor Expertise", expertise_options, default=expertise_options)

category_options = sorted(df["CourseCategory"].dropna().unique())
selected_category = st.sidebar.multiselect("Course Category", category_options, default=category_options)

level_options = sorted(df["CourseLevel"].dropna().unique())
selected_level = st.sidebar.multiselect("Course Level", level_options, default=level_options)

min_rating, max_rating = float(df["TeacherRating"].min()), float(df["TeacherRating"].max())
rating_range = st.sidebar.slider("Teacher Rating Range", min_rating, max_rating, (min_rating, max_rating))

# Filter Data
filtered_df = df[
    (df["Expertise"].isin(selected_expertise)) &
    (df["CourseCategory"].isin(selected_category)) &
    (df["CourseLevel"].isin(selected_level)) &
    (df["TeacherRating"].between(rating_range[0], rating_range[1]))
]

# --- HEADER & KPI CARDS ---
st.title("EduPro: Instructor Performance & Course Quality Evaluation")
st.markdown("Interactive analytical dashboard evaluating teaching effectiveness, experience impact, and course ratings.")

if filtered_df.empty:
    st.warning("No records match your selected filters. Please adjust the sidebar filters.")
    st.stop()

# Instructor-level aggregation on filtered data
inst_summary = filtered_df.groupby(
    ["TeacherID", "TeacherName", "Gender", "Expertise", "YearsOfExperience", "TeacherRating"]
).agg(
    TotalEnrollments=("TransactionID", "count"),
    AvgCourseRating=("CourseRating", "mean"),
    RatingStd=("CourseRating", "std")
).reset_index()

inst_summary["RatingStd"] = inst_summary["RatingStd"].fillna(0)
inst_summary["ConsistencyIndex"] = (1 / (1 + inst_summary["RatingStd"])).round(3)
inst_summary["EnrollmentInfluenceRatio"] = (inst_summary["TotalEnrollments"] / inst_summary["TeacherRating"]).round(2)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Avg Teacher Rating", f"{inst_summary['TeacherRating'].mean():.2f} / 5.0")
col2.metric("Avg Course Rating", f"{filtered_df['CourseRating'].mean():.2f} / 5.0")
col3.metric("Total Enrollments", f"{len(filtered_df):,}")
col4.metric("Avg Consistency Index", f"{inst_summary['ConsistencyIndex'].mean():.3f}")

st.divider()

# --- ROW 1: LEADERBOARD & EXPERIENCE SCATTER ---
left_col, right_col = st.columns(2)

with left_col:
    st.subheader("Instructor Performance Leaderboard (Top 10)")
    top_10 = inst_summary.sort_values(by=["TeacherRating", "TotalEnrollments"], ascending=False).head(10)
    fig_leader = px.bar(
        top_10,
        x="TeacherRating",
        y="TeacherName",
        color="Expertise",
        orientation="h",
        hover_data=["YearsOfExperience", "AvgCourseRating", "TotalEnrollments", "ConsistencyIndex"],
        title="Top 10 Instructors by Rating"
    )
    fig_leader.update_layout(yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig_leader, use_container_width=True)

with right_col:
    st.subheader("Experience vs. Rating Impact")
    fig_exp = px.scatter(
        inst_summary,
        x="YearsOfExperience",
        y="TeacherRating",
        size="TotalEnrollments",
        color="Expertise",
        hover_name="TeacherName",
        trendline="ols",
        title="Years of Experience vs. Teacher Rating (Bubble Size = Enrollments)"
    )
    st.plotly_chart(fig_exp, use_container_width=True)

# --- ROW 2: COURSE QUALITY HEATMAP & EXPERTISE COMPARISON ---
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Course Quality Heatmap (Category vs. Level)")
    heatmap_data = filtered_df.pivot_table(
        index="CourseCategory",
        columns="CourseLevel",
        values="CourseRating",
        aggfunc="mean"
    ).round(2)
    fig_heat = px.imshow(
        heatmap_data,
        text_auto=True,
        color_continuous_scale="Blues",
        aspect="auto",
        title="Average Course Rating by Category & Level"
    )
    st.plotly_chart(fig_heat, use_container_width=True)

with col_b:
    st.subheader("Expertise-Wise Course Rating Distribution")
    fig_box = px.box(
        filtered_df,
        x="Expertise",
        y="CourseRating",
        color="Expertise",
        title="Course Rating Distribution Across Instructor Expertise"
    )
    st.plotly_chart(fig_box, use_container_width=True)

# --- DATA TABLE ---
st.subheader("Detailed Instructor KPI Table")
st.dataframe(
    inst_summary.sort_values(by="TeacherRating", ascending=False),
    use_container_width=True
)