import requests
import pandas as pd
import numpy as np

try:
    # Fetching data for dataset
    tutoring_session_api = requests.get('http://127.0.0.1:8002/sessions/unprotected')
    tutoring_session_api.raise_for_status()
    tutoring_session_api_data = tutoring_session_api.json()

    student_api = requests.get('http://127.0.0.1:8002/students/unprotected')
    student_api.raise_for_status()
    student_api_data = student_api.json()

    # Create DataFrames
    vdf = pd.DataFrame(tutoring_session_api_data)
    odf = pd.DataFrame(student_api_data)

    # 1. Describe the dataset
    print(f"\n--- Describing the tutoring_sessions DataFrame ---\n shape the session: {vdf.shape}")
    print(vdf.describe())
    print(vdf.info())

    print(f"\n--- Describing the students DataFrame ---\n shape the student: {vdf.shape}")
    print(odf.describe())
    print(odf.info())

    # --- 2. Find and replace null values ---
    # Check for missing values
    print("\nMissing values in tutoring sessions:")
    print(vdf.isnull().sum())

    print("\nMissing values in students:")
    print(odf.isnull().sum())

    # --- Handling missing values in tutoring_sessions (vdf) ---
    # Replace null values in numerical columns with the median (to avoid outliers impacting the mean)
    vdf['duration'] = vdf['duration'].fillna(vdf['duration'].median())

    # Replace null date with the most frequent date (mode)
    vdf['date'] = pd.to_datetime(vdf['date'], errors='coerce')
    vdf['date'] = vdf['date'].fillna(vdf['date'].mode()[0])  # Replace with mode (most frequent)

    # --- Handling missing values in students (odf) ---
    if 'age' in odf.columns:
        odf['age'] = odf['age'].fillna(odf['age'].median())  # Replace missing ages with median value

    print("\nMissing values after imputation in tutoring_sessions:")
    print(vdf.isnull().sum())

    print("\nMissing values after imputation in students:")
    print(odf.isnull().sum())

    # --- 3. Basic Data Preprocessing ---
    # Convert 'date' to datetime format
    vdf['date'] = pd.to_datetime(vdf['date'], errors='coerce')

    # --- Encode Categorical Features ---
    # One-Hot Encoding for 'subject'
    vdf = pd.get_dummies(vdf, columns=['subject'], drop_first=True)  # Drop first to avoid collinearity

    # Label Encoding for 'session_duration_category'
    vdf['session_duration_category'] = pd.cut(vdf['duration'], bins=[0, 30, 60, 120],
                                              labels=['short', 'medium', 'long'])
    vdf['session_duration_category'] = vdf['session_duration_category'].map({'short': 0, 'medium': 1, 'long': 2})

    # --- Handle Encoding for students ---
    # One-Hot Encoding for 'student_age_category'
    if 'age' in odf.columns:
        odf['student_age_category'] = pd.cut(odf['age'], bins=[0, 18, 25, 100], labels=['Under 18', '18-25', 'Over 25'])
        odf = pd.get_dummies(odf, columns=['student_age_category'], drop_first=True)  # One-Hot Encoding


    # --- 4. Create New Features ---
    # Feature Engineering for tutoring_sessions (vdf)
    vdf['session_weekday'] = vdf['date'].dt.dayofweek  # 0=Monday, 6=Sunday
    vdf['session_hour'] = vdf['date'].dt.hour  # Hour of the day
    vdf['session_month'] = vdf['date'].dt.month  # Month of the year
    vdf['session_year'] = vdf['date'].dt.year  # Year of session
    vdf['is_weekend'] = vdf['session_weekday'].apply(lambda x: 1 if x >= 5 else 0)  # 1 if weekend, 0 if weekday

    # Create 'session_duration_category' based on the duration
    vdf['session_duration_category'] = pd.cut(vdf['duration'], bins=[0, 30, 60, 120],
                                              labels=['short', 'medium', 'long'])

    # --- Feature Engineering for students (odf) ---
    if 'enrollment_date' in odf.columns:
        odf['enrollment_year'] = odf['enrollment_date'].dt.year  # Extract enrollment year
        odf['enrollment_duration'] = (pd.to_datetime('today') - odf['enrollment_date']).dt.days  # Duration in days

    # --- Display cleaned data (sample) ---
    print("\nCleaned Tutoring Sessions DataFrame (First 5 rows):")
    print(vdf.head())

    print("\nCleaned Students DataFrame (First 5 rows):")
    print(odf.head())

    # Merge the two DataFrames on the 'student_id' column (assumed common column)
    merged_df = pd.merge(vdf, odf, on='student_id', how='left')  # Left join to retain all tutoring sessions

    # Check if any null values remain in the merged dataset
    print("\nMissing values after merging the datasets:")
    print(merged_df.isnull().sum())

    # --- Display merged data (sample) ---
    print("\nMerged DataFrame (First 5 rows):")
    print(merged_df.head())

    # Saving the final DataFrames to CSV files for further analysis
    vdf.to_csv('cleaned_tutoring_sessions.csv', index=False)
    odf.to_csv('cleaned_students.csv', index=False)
    merged_df.to_csv('merged_tutoring_sessions_and_students.csv', index=False)

except requests.exceptions.RequestException as e:
    print(f"Error fetching data from API: {e}")
