import streamlit as st
import pandas as pd
import os
import base64
import hashlib
from datetime import datetime
import logging
import sys
import urllib.parse
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib import colors
import warnings

# Suppress all warnings globally
warnings.filterwarnings('ignore')

# Configure logging for Streamlit Cloud
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="OMOTEC Mentors Assessment App", layout="wide", initial_sidebar_state="expanded")

CSV_FILE = "assessment_data.csv"
DEFAULT_DATA_FILE = "EVALUATOR_INPUT.csv"
EVALUATOR_STORE = "evaluators.csv"

# Predefined course options
COURSE_OPTIONS = [
    "", "Introduction to Coding", "Robotics Basics", "AI Fundamentals", 
    "3D Printing", "Electronics 101", "Data Analytics", 
    "Mechanical Design", "STEM Project Management", 
    "Advanced Programming", "Circuit Design"
]

CSV_COLUMNS = [
    "Trainer ID", "Trainer Name", "Department", "DOJ", "Branch", "Discipline", "Course", "Date of assessment",
    "Has Knowledge of STEM (5)", "Ability to integrate STEM With related activities (10)",
    "Discusses Up-to-date information related to STEM (5)", "Provides Course Outline (5)", "Language Fluency (5)",
    "Preparation with Lesson Plan / Practicals (5)", "Time Based Activity (5)", "Student Engagement Ideas (5)",
    "Pleasing Look (5)", "Poised & Confident (5)", "Well Modulated Voice (5)",
    "LEVEL #1 Course :1", "LEVEL #1 Course :2", "LEVEL #1 Course :3", "LEVEL #1 Course :4", "LEVEL #1 Course :5",
    "LEVEL #1 Course :6", "LEVEL #1 Course :7", "LEVEL #1 Course :8", "LEVEL #1 Course :9", "LEVEL #1 Course :10",
    "LEVEL #1 TOTAL", "LEVEL #1 AVERAGE", "LEVEL #1 STATUS", "LEVEL #1 Reminder", "LEVEL #1 Score Card Status",
    "LEVEL #2 Course :1", "LEVEL #2 Course :2", "LEVEL #2 Course :3", "LEVEL #2 Course :4", "LEVEL #2 Course :5",
    "LEVEL #2 Course :6", "LEVEL #2 Course :7", "LEVEL #2 Course :8", "LEVEL #2 Course :9", "LEVEL #2 Course :10",
    "LEVEL #2 TOTAL", "LEVEL #2 AVERAGE", "LEVEL #2 STATUS", "LEVEL #2 Reminder", "LEVEL #2 Score Card Status",
    "LEVEL #3 Course :1", "LEVEL #3 Course :2", "LEVEL #3 Course :3", "LEVEL #3 Course :4", "LEVEL #3 Course :5",
    "LEVEL #3 Course :6", "LEVEL #3 Course :7", "LEVEL #3 Course :8", "LEVEL #3 Course :9", "LEVEL #3 Course :10",
    "LEVEL #3 TOTAL", "LEVEL #3 AVERAGE", "LEVEL #3 STATUS", "LEVEL #3 Reminder", "LEVEL #3 Score Card Status",
    "LEVEL #1", "LEVEL #2", "LEVEL #3", "Evaluator Username", "Evaluator Role", "Manager Referral"
] + [f"{param} Course :{i}" for param in [
    "Has Knowledge of STEM (5)", "Ability to integrate STEM With related activities (10)",
    "Discusses Up-to-date information related to STEM (5)", "Provides Course Outline (5)", "Language Fluency (5)",
    "Preparation with Lesson Plan / Practicals (5)", "Time Based Activity (5)", "Student Engagement Ideas (5)",
    "Pleasing Look (5)", "Poised & Confident (5)", "Well Modulated Voice (5)"
] for i in range(1, 11)] + [
    f"{level} Course :{i} TOTAL" for level in ["LEVEL #1", "LEVEL #2", "LEVEL #3"] for i in range(1, 11)
] + [
    f"{level} Course :{i} AVERAGE" for level in ["LEVEL #1", "LEVEL #2", "LEVEL #3"] for i in range(1, 11)
] + [
    f"{level} Course :{i} STATUS" for level in ["LEVEL #1", "LEVEL #2", "LEVEL #3"] for i in range(1, 11)
] + [
    f"{level} Course :{i} Remarks" for level in ["LEVEL #1", "LEVEL #2", "LEVEL #3"] for i in range(1, 11)
]

EVALUATOR_COLUMNS = ["username", "password_hash", "full_name", "email", "role", "created_at"]

def hash_password(password: str) -> str:
    try:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()
    except Exception as e:
        logger.error(f"Error hashing password: {str(e)}")
        return ""

def verify_password(password: str, stored_hash: str) -> bool:
    try:
        return hash_password(password) == stored_hash
    except Exception as e:
        logger.error(f"Error verifying password: {str(e)}")
        return False

def load_data():
    try:
        if not os.path.exists(CSV_FILE):
            if os.path.exists(DEFAULT_DATA_FILE):
                df = pd.read_csv(DEFAULT_DATA_FILE)
            else:
                df = pd.DataFrame(columns=CSV_COLUMNS)
            df.to_csv(CSV_FILE, index=False)
        else:
            df = pd.read_csv(CSV_FILE)

        for col in CSV_COLUMNS:
            if col not in df.columns:
                df[col] = ""
        return df[CSV_COLUMNS]
    except Exception as e:
        logger.error(f"Error loading data: {str(e)}")
        st.error("Failed to load assessment data. Please try again later.")
        return pd.DataFrame(columns=CSV_COLUMNS)

def generate_new_trainer_id():
    try:
        if os.path.exists(DEFAULT_DATA_FILE):
            df = pd.read_csv(DEFAULT_DATA_FILE)
            if "Trainer ID" in df.columns:
                existing_ids = df["Trainer ID"].dropna().astype(str)
                numbers = []
                for tid in existing_ids:
                    if tid.startswith("TR00"):
                        num_part = tid.replace("TR00", "")
                        if num_part.isdigit():
                            numbers.append(int(num_part))
                next_number = max(numbers) + 1 if numbers else 1
                return f"TR00{next_number}"
    except Exception as e:
        logger.error(f"Trainer ID generation failed: {str(e)}")
        st.error("Failed to generate Trainer ID. Using default ID.")
    return "TR001"

def save_new_trainer_to_input(trainer_id, trainer_name, department, trainer_email=""):
    try:
        if os.path.exists(DEFAULT_DATA_FILE):
            df = pd.read_csv(DEFAULT_DATA_FILE)
        else:
            df = pd.DataFrame(columns=["Trainer ID", "Trainer Name", "Department", "Branch", "Email"])
        
        if "Trainer ID" not in df.columns:
            df["Trainer ID"] = ""
        if "Trainer Name" not in df.columns:
            df["Trainer Name"] = ""
        if "Department" not in df.columns:
            df["Department"] = ""
        if "Branch" not in df.columns:
            df["Branch"] = ""
        if "Email" not in df.columns:
            df["Email"] = ""
            
        if trainer_id in df["Trainer ID"].values:
            idx = df.index[df["Trainer ID"] == trainer_id][0]
            df.at[idx, "Trainer Name"] = trainer_name
            df.at[idx, "Department"] = department
            df.at[idx, "Email"] = trainer_email
        else:
            new_entry = {
                "Trainer ID": trainer_id,
                "Trainer Name": trainer_name,
                "Department": department,
                "Branch": "",
                "Email": trainer_email
            }
            df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
        df.to_csv(DEFAULT_DATA_FILE, index=False)
        return df
    except Exception as e:
        logger.error(f"Error saving new trainer: {str(e)}")
        st.error("Failed to save new trainer information.")
        return pd.DataFrame(columns=["Trainer ID", "Trainer Name", "Department", "Branch", "Email"])

def load_evaluators():
    try:
        if not os.path.exists(EVALUATOR_STORE):
            df = pd.DataFrame(columns=EVALUATOR_COLUMNS)
            df.to_csv(EVALUATOR_STORE, index=False)
        else:
            df = pd.read_csv(EVALUATOR_STORE)
        for col in EVALUATOR_COLUMNS:
            if col not in df.columns:
                df[col] = ""
        return df[EVALUATOR_COLUMNS].copy()
    except Exception as e:
        logger.error(f"Error loading evaluators: {str(e)}")
        st.error("Failed to load evaluator data.")
        return pd.DataFrame(columns=EVALUATOR_COLUMNS)

def save_evaluators(df):
    try:
        df.to_csv(EVALUATOR_STORE, index=False)
    except Exception as e:
        logger.error(f"Error saving evaluators: {str(e)}")
        st.error("Failed to save evaluator data.")

def evaluator_section(df_main):
    try:
        st.subheader("🧑‍🏫 Evaluator Dashboard")

        # CSS for tab animations and level heading backgrounds
        st.markdown("""
        <style>
        .stTabs [role="tab"] {
            animation: slideIn 0.5s ease-in-out;
        }
        @keyframes slideIn {
            0% { transform: translateX(-20px); opacity: 0; }
            100% { transform: translateX(0); opacity: 1; }
        }
        .level-1-heading {
            background-color: #0FA753 !important;
            padding: 10px;
            border-radius: 5px;
            color: white;
        }
        .level-2-heading {
            background-color: #00A191 !important;
            padding: 10px;
            border-radius: 5px;
            color: white;
        }
        .level-3-heading {
            background-color: #8EC200 !important;
            padding: 10px;
            border-radius: 5px;
            color: white;
        }
        </style>
        """, unsafe_allow_html=True)

        if "logged_in" not in st.session_state or not st.session_state.get("logged_in"):
            st.warning("Please login to access the evaluator panel.")
            return

        df = df_main.copy()
        if "Trainer ID" not in df.columns:
            st.error("❌ 'Trainer ID' column missing in data.")
            return

        evaluator_role = st.selectbox(
            "Select Evaluator Role",
            ["Technical Evaluator", "School Operations Evaluator"],
            key="evaluator_role"
        )
        evaluator_username = st.session_state.get("logged_user", "")

        relevant_params = {
            "Technical Evaluator": [
                "Has Knowledge of STEM (5)",
                "Ability to integrate STEM With related activities (10)",
                "Discusses Up-to-date information related to STEM (5)",
                "Provides Course Outline (5)",
                "Language Fluency (5)",
                "Preparation with Lesson Plan / Practicals (5)"
            ],
            "School Operations Evaluator": [
                "Time Based Activity (5)",
                "Student Engagement Ideas (5)",
                "Pleasing Look (5)",
                "Poised & Confident (5)",
                "Well Modulated Voice (5)"
            ]
        }

        mode = st.radio("Select Trainer ID Mode", ["Enter Existing Trainer ID", "New Trainer Creation ID"])
        trainer_id, trainer_name, department, trainer_email = "", "", "", ""

        # Enhancement 1: By default shows first record "Priyas's name" when logged in, Enhance to not show this in default
        # Solution: Set index=None in selectbox to start with no selection
        if mode.startswith("Enter"):
            try:
                if os.path.exists(DEFAULT_DATA_FILE):
                    eval_inputs_df = pd.read_csv(DEFAULT_DATA_FILE).fillna("")
                    if "Trainer ID" not in eval_inputs_df.columns:
                        st.error("❌ 'Trainer ID' column missing in EVALUATOR_INPUT.csv.")
                        return
                    available_ids = [""] + eval_inputs_df["Trainer ID"].dropna().unique().tolist()  # Add empty option
                    selected_id = st.selectbox("Select Existing Trainer ID", available_ids, index=0)  # Default to empty
                    if selected_id:
                        trainer_data = eval_inputs_df[eval_inputs_df["Trainer ID"] == selected_id].iloc[0].to_dict()
                        trainer_id = trainer_data.get("Trainer ID", "")
                        trainer_name = trainer_data.get("Trainer Name", "")
                        department = trainer_data.get("Department", "")
                        trainer_email = trainer_data.get("Email", "")
                        st.success(f"Loaded Trainer ID: {trainer_id}")
                else:
                    st.error("EVALUATOR_INPUT.csv not found.")
                    return
            except Exception as e:
                logger.error(f"Error loading existing trainer data: {str(e)}")
                st.error("Failed to load trainer data.")
                return

            # Make details editable
            trainer_name = st.text_input("Trainer Name", value=trainer_name)
            department = st.text_input("Department", value=department)
            trainer_email = st.text_input("Trainer Email", value=trainer_email)

        # New Trainer ID
        else:
            trainer_id = st.text_input("Enter New Trainer ID (leave blank to auto-generate)")
            trainer_name = st.text_input("Trainer Name")
            department = st.text_input("Department")
            trainer_email = st.text_input("Trainer Email")
            if trainer_id.strip() == "":
                if trainer_name and department and trainer_email:
                    st.info("Trainer ID will be auto-generated upon submission.")
                else:
                    st.warning("Please enter Trainer Name, Department, and Email for auto-generation.")

        # Display previous assessments
        past_assessments = df[df["Trainer ID"] == trainer_id] if trainer_id else pd.DataFrame()
        if not past_assessments.empty:
            st.markdown("### 🔁 Previous Assessments")
            st.dataframe(past_assessments, use_container_width=True)

        levels = ["LEVEL #1", "LEVEL #2", "LEVEL #3"]
        level_status, submissions, assessment_data = {}, {}, {}

        try:
            for level in levels:
                level_rows = past_assessments[past_assessments[level] == "QUALIFIED"]
                evaluators = level_rows["Evaluator Username"].tolist()
                has_tech = any("technical" in s.lower() for s in level_rows["Evaluator Role"].fillna(""))
                has_ops = any("school" in s.lower() for s in level_rows["Evaluator Role"].fillna(""))
                if has_tech and has_ops:
                    level_status[level] = "QUALIFIED"
                else:
                    level_status[level] = "NOT QUALIFIED"
                submissions[f"{level}_submissions"] = len(set(evaluators))
        except Exception as e:
            logger.error(f"Error processing level statuses: {str(e)}")
            st.error("Failed to process assessment levels.")

        # Enhancement 10: Update to make Level 2 should be unlocked automatically once all the assessments for 10 courses been marked as qualified in Level 1 and not with the current option where have to mark manually
        # Enhancement 11: Resolve this error + Once level 1 is completed with all Course 1 to Course 10 status as QUALIFIED, automatically option to for level 2 assessments should be enabled without any manual option
        # Enhancement 12: Resolve this error + Once level 2 is completed with all Course 1 to Course 10 status as QUALIFIED, automatically option to for level 3 assessments should be enabled without any manual option
        # Solution: Check if all 10 courses in previous level are qualified based on past_assessments
        level_1_qualified = all(past_assessments.get(f"LEVEL #1 Course :{i} STATUS", "") == "QUALIFIED" for i in range(1, 11)) if not past_assessments.empty else False
        level_2_qualified = all(past_assessments.get(f"LEVEL #2 Course :{i} STATUS", "") == "QUALIFIED" for i in range(1, 11)) if not past_assessments.empty else False

        for level in levels:
            level_class = f"level-{level.split('#')[1]}-heading"
            st.markdown(f'<div class="{level_class}">🔹 {level} Assessment</div>', unsafe_allow_html=True)

            with st.expander(f"{level} Assessment"):
                try:
                    courses = {}
                    course_params = {f"Course :{i}": {} for i in range(1, 11)}
                    manager_referral = ""
                    status = "NOT QUALIFIED"

                    if level_status.get(level) == "QUALIFIED" and submissions.get(f"{level}_submissions", 0) >= 2:
                        st.write(f"{level} already qualified by both evaluators.")
                    elif level_status.get(level) == "QUALIFIED" and submissions.get(f"{level}_submissions", 0) == 1:
                        st.write(f"{level} qualified by one evaluator. Awaiting second evaluation.")
                    else:
                        eligible = (
                            level == "LEVEL #1" or
                            (level == "LEVEL #2" and level_1_qualified) or
                            (level == "LEVEL #3" and level_2_qualified)
                        )
                        if eligible:
                            st.markdown(f"### {level} Courses")
                            tabs = st.tabs([f"Course :{i}" for i in range(1, 11)])
                            all_courses_filled = True
                            all_courses_passed = True

                            for i, tab in enumerate(tabs, 1):
                                with tab:
                                    course_key = f"{level} Course :{i}"
                                    course_name = ""
                                    course_select = st.selectbox(
                                        f"{course_key} Select Course Name",
                                        options=COURSE_OPTIONS,
                                        key=f"course_select_{level}_{i}_{trainer_id}",
                                        placeholder="Select course"
                                    )

                                    if evaluator_role == "Technical Evaluator":
                                        param_has_stem = st.number_input("Has Knowledge of STEM (5)", 0, 5, key=f"stem_{level}_{i}_{trainer_id}")
                                        param_integration = st.number_input("Ability to integrate STEM With related activities (10)", 0, 10, key=f"integration_{level}_{i}_{trainer_id}")
                                        param_up_to_date = st.number_input("Discusses Up-to-date information related to STEM (5)", 0, 5, key=f"uptodate_{level}_{i}_{trainer_id}")
                                        param_outline = st.number_input("Provides Course Outline (5)", 0, 5, key=f"outline_{level}_{i}_{trainer_id}")
                                        param_language = st.number_input("Language Fluency (5)", 0, 5, key=f"language_{level}_{i}_{trainer_id}")
                                        param_preparation = st.number_input("Preparation with Lesson Plan / Practicals (5)", 0, 5, key=f"preparation_{level}_{i}_{trainer_id}")

                                        course_params[f"Course :{i}"] = {
                                            "Has Knowledge of STEM (5)": param_has_stem,
                                            "Ability to integrate STEM With related activities (10)": param_integration,
                                            "Discusses Up-to-date information related to STEM (5)": param_up_to_date,
                                            "Provides Course Outline (5)": param_outline,
                                            "Language Fluency (5)": param_language,
                                            "Preparation with Lesson Plan / Practicals (5)": param_preparation
                                        }

                                    elif evaluator_role == "School Operations Evaluator":
                                        param_time = st.number_input("Time Based Activity (5)", 0, 5, key=f"time_{level}_{i}_{trainer_id}")
                                        param_engagement = st.number_input("Student Engagement Ideas (5)", 0, 5, key=f"engagement_{level}_{i}_{trainer_id}")
                                        param_pleasing = st.number_input("Pleasing Look (5)", 0, 5, key=f"pleasing_{level}_{i}_{trainer_id}")
                                        param_poised = st.number_input("Poised & Confident (5)", 0, 5, key=f"poised_{level}_{i}_{trainer_id}")
                                        param_voice = st.number_input("Well Modulated Voice (5)", 0, 5, key=f"voice_{level}_{i}_{trainer_id}")

                                        course_params[f"Course :{i}"] = {
                                            "Time Based Activity (5)": param_time,
                                            "Student Engagement Ideas (5)": param_engagement,
                                            "Pleasing Look (5)": param_pleasing,
                                            "Poised & Confident (5)": param_poised,
                                            "Well Modulated Voice (5)": param_voice
                                        }

                                    # Enhancement 9: When one assessment is marked as "Redo", ensure to display where are the attempts added
                                    # Solution: Track attempts in session state or CSV column
                                    if f"attempt_{level}_{i}_{trainer_id}" not in st.session_state:
                                        st.session_state[f"attempt_{level}_{i}_{trainer_id}"] = 1
                                    attempt = st.session_state[f"attempt_{level}_{i}_{trainer_id}"]
                                    st.info(f"Attempt: {attempt}")

                                    remarks = st.text_area("Remarks", key=f"remarks_{level}_{i}_{trainer_id}")

                                    if evaluator_role == "Technical Evaluator":
                                        if st.button(f"Calculate Score", key=f"calc_{level}_{i}_{trainer_id}"):
                                            try:
                                                calculated_total = (
                                                    param_has_stem + param_integration + param_up_to_date +
                                                    param_outline + param_language + param_preparation
                                                )
                                                calculated_avg = calculated_total / 6.0 if 6 > 0 else 0.0
                                                st.session_state[f"total_{level}_{i}_{trainer_id}"] = calculated_total
                                                st.session_state[f"avg_{level}_{i}_{trainer_id}"] = calculated_avg
                                                st.success(f"Calculated Total: {calculated_total}, Average: {calculated_avg:.2f}")

                                                # Update EVALUATOR_INPUT.csv
                                                save_new_trainer_to_input(trainer_id, trainer_name, department, trainer_email)

                                                # Update assessment_data.csv for this course
                                                course_entry = {
                                                    "Trainer ID": trainer_id,
                                                    "Trainer Name": trainer_name,
                                                    "Department": department,
                                                    "Date of assessment": datetime.today().date().strftime("%Y-%m-%Y"),
                                                    "Evaluator Username": evaluator_username,
                                                    "Evaluator Role": evaluator_role,
                                                    f"{course_key}": course_select,
                                                    f"{course_key} TOTAL": calculated_total,
                                                    f"{course_key} AVERAGE": calculated_avg,
                                                    f"{course_key} STATUS": st.session_state.get(f"status_{level}_{i}_{trainer_id}", "REDO"),
                                                    f"{course_key} Remarks": remarks
                                                }
                                                for param, value in course_params[f"Course :{i}"].items():
                                                    course_entry[f"{param} Course :{i}"] = value

                                                updated_df = df.copy()
                                                if trainer_id in updated_df["Trainer ID"].values:
                                                    idx = updated_df.index[updated_df["Trainer ID"] == trainer_id].tolist()[-1]
                                                    for key, value in course_entry.items():
                                                        updated_df.at[idx, key] = value
                                                else:
                                                    updated_df = pd.concat([updated_df, pd.DataFrame([course_entry])], ignore_index=True)
                                                updated_df.to_csv(CSV_FILE, index=False)

                                                # Enhancement 2: Once added scores in one assessment and calculated, does not reflect in other sections
                                                # Solution: Rerun the app to refresh displays
                                                st.rerun()

                                            except Exception as e:
                                                logger.error(f"Error updating data on Calculate Score: {str(e)}")
                                                st.error("Failed to update assessment data.")
                                    elif evaluator_role == "School Operations Evaluator":
                                        if st.button(f"Calculate Score", key=f"calc_{level}_{i}_{trainer_id}"):
                                            try:
                                                calculated_total = (
                                                    param_time + param_engagement + param_pleasing +
                                                    param_poised + param_voice
                                                )
                                                calculated_avg = calculated_total / 5.0 if 5 > 0 else 0.0
                                                st.session_state[f"total_{level}_{i}_{trainer_id}"] = calculated_total
                                                st.session_state[f"avg_{level}_{i}_{trainer_id}"] = calculated_avg
                                                st.success(f"Calculated Total: {calculated_total}, Average: {calculated_avg:.2f}")

                                                # Update EVALUATOR_INPUT.csv
                                                save_new_trainer_to_input(trainer_id, trainer_name, department, trainer_email)

                                                # Update assessment_data.csv for this course
                                                course_entry = {
                                                    "Trainer ID": trainer_id,
                                                    "Trainer Name": trainer_name,
                                                    "Department": department,
                                                    "Date of assessment": datetime.today().date().strftime("%Y-%m-%Y"),
                                                    "Evaluator Username": evaluator_username,
                                                    "Evaluator Role": evaluator_role,
                                                    f"{course_key}": course_select,
                                                    f"{course_key} TOTAL": calculated_total,
                                                    f"{course_key} AVERAGE": calculated_avg,
                                                    f"{course_key} STATUS": st.session_state.get(f"status_{level}_{i}_{trainer_id}", "REDO"),
                                                    f"{course_key} Remarks": remarks
                                                }
                                                for param, value in course_params[f"Course :{i}"].items():
                                                    course_entry[f"{param} Course :{i}"] = value

                                                updated_df = df.copy()
                                                if trainer_id in updated_df["Trainer ID"].values:
                                                    idx = updated_df.index[updated_df["Trainer ID"] == trainer_id].tolist()[-1]
                                                    for key, value in course_entry.items():
                                                        updated_df.at[idx, key] = value
                                                else:
                                                    updated_df = pd.concat([updated_df, pd.DataFrame([course_entry])], ignore_index=True)
                                                updated_df.to_csv(CSV_FILE, index=False)

                                                # Enhancement 2: Refresh
                                                st.rerun()

                                            except Exception as e:
                                                logger.error(f"Error updating data on Calculate Score: {str(e)}")
                                                st.error("Failed to update assessment data.")

                                    calculated_total = st.session_state.get(f"total_{level}_{i}_{trainer_id}", 0)
                                    calculated_avg = st.session_state.get(f"avg_{level}_{i}_{trainer_id}", 0.0)
                                    status_overall = st.selectbox(f"Course :{i} STATUS", ["CLEARED", "REDO"], key=f"status_{level}_{i}_{trainer_id}")
                                    if status_overall == "REDO":
                                        st.session_state[f"attempt_{level}_{i}_{trainer_id}"] += 1  # Increment attempt on REDO
                                    course_passed = st.checkbox(f"{course_key} Passed", key=f"course_pass_{level}_{i}_{trainer_id}")

                                    final_course = course_name if course_name else course_select
                                    courses[course_key] = {
                                        "name": final_course,
                                        "passed": course_passed,
                                        "total": calculated_total,
                                        "average": calculated_avg,
                                        "status_overall": status_overall,
                                        "params": course_params[f"Course :{i}"],
                                        "remarks": remarks
                                    }
                                    if not final_course or not course_passed:
                                        all_courses_filled = False
                                        all_courses_passed = False
                                    st.session_state[f"course_passed_{level}_{i}_{trainer_id}"] = course_passed

                            # Check if all courses are passed and named
                            all_courses_filled = all(
                                courses.get(f"{level} Course :{i}", {}).get("name") and 
                                courses.get(f"{level} Course :{i}", {}).get("passed") 
                                for i in range(1, 11)
                            )
                            all_courses_passed = all(
                                st.session_state.get(f"course_passed_{level}_{i}_{trainer_id}", False)
                                for i in range(1, 11)
                            )

                            level_status_key = f"{level}_status_{evaluator_role}"
                            status_options = ["QUALIFIED", "NOT QUALIFIED"]
                            default_status_index = 0 if all_courses_filled and all_courses_passed else 1
                            status = st.selectbox(
                                f"{level} Status",
                                status_options,
                                index=default_status_index,
                                key=level_status_key
                            )

                            if level == "LEVEL #3":
                                manager_referral = st.text_input(
                                    "Manager Referral (Required for Level 3)",
                                    key=f"manager_referral_{level}_{trainer_id}"
                                )

                            # Enhancement 7: Add button option to Save Assessment in DB to save the assessment data entered in the appropriate CSV file under the appropriate Trainer ID row.
                            # Solution: Add Save button to compile and save course data without full submission
                            if st.button("Save Assessment in DB", key=f"save_{level}_{trainer_id}"):
                                try:
                                    entry = {
                                        "Trainer ID": trainer_id,
                                        "Trainer Name": trainer_name,
                                        "Department": department,
                                        "Date of assessment": datetime.today().date().strftime("%Y-%m-%Y"),
                                        "Evaluator Username": evaluator_username,
                                        "Evaluator Role": evaluator_role
                                    }
                                    for i in range(1, 11):
                                        course_key = f"{level} Course :{i}"
                                        course_data = courses.get(course_key, {})
                                        entry[course_key] = course_data.get("name", "")
                                        entry[f"{course_key} TOTAL"] = course_data.get("total", 0)
                                        entry[f"{course_key} AVERAGE"] = course_data.get("average", 0.0)
                                        entry[f"{course_key} STATUS"] = course_data.get("status_overall", "REDO")
                                        entry[f"{course_key} Remarks"] = course_data.get("remarks", "")
                                        for param in relevant_params[evaluator_role]:
                                            entry[f"{param} Course :{i}"] = course_data.get("params", {}).get(param, 0)

                                    updated_df = df.copy()
                                    if trainer_id in updated_df["Trainer ID"].values:
                                        idx = updated_df.index[updated_df["Trainer ID"] == trainer_id].tolist()[-1]
                                        for key, value in entry.items():
                                            updated_df.at[idx, key] = value
                                    else:
                                        updated_df = pd.concat([updated_df, pd.DataFrame([entry])], ignore_index=True)
                                    updated_df.to_csv(CSV_FILE, index=False)
                                    st.success("Assessment saved to DB.")
                                    st.rerun()
                                except Exception as e:
                                    logger.error(f"Error saving assessment: {str(e)}")
                                    st.error("Failed to save assessment.")

                            # Enhancement 8: For course 2 assessment, ensure to keep the same reminder added for course 1 assessment with the same functionality as Course 1
                            # Solution: Reminder is per level, so it's already shared across courses in the level

                            reminder = st.text_area("Reminder", key=f"reminder_{level}_{trainer_id}")
                            reminder_email = st.text_input("Reminder Email", key=f"reminder_email_{level}_{trainer_id}")

                            # Enhancement 3: Error when clicked on "Reminder email prepared for"
                            # Solution: Add button to prepare reminder email, handle errors
                            if st.button("Prepare Reminder Email", key=f"prepare_reminder_{level}_{trainer_id}"):
                                try:
                                    if reminder_email:
                                        st.session_state[f"prepared_email_{level}_{trainer_id}"] = reminder_email
                                        st.success(f"Reminder email prepared for {reminder_email}")
                                    else:
                                        st.warning("Enter a reminder email first.")
                                except Exception as e:
                                    logger.error(f"Error preparing reminder email: {str(e)}")
                                    st.error("Failed to prepare reminder email.")

                            # Enhancement 4: Error as Does not send email when clicked on [SEND EMAIL]
                            # Enhancement 5: Change from “Open in Gmail” to “Open to send mail”
                            # Enhancement 6: Remove Unnecessary data in mail: Keep only default data so evaluator can add email contents
                            # Solution: Add Send Email button, use smtplib to send, minimal body
                            if st.button("Open to send mail", key=f"open_mail_{level}_{trainer_id}"):
                                try:
                                    msg = EmailMessage()
                                    msg['Subject'] = f"Reminder for {level}"
                                    msg['From'] = 'your_email@example.com'  # Replace with actual
                                    msg['To'] = reminder_email
                                    msg.set_content(reminder)  # Only reminder text, no unnecessary data

                                    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:  # Example for Gmail
                                        smtp.login('your_email@example.com', 'your_password')  # Use secrets
                                        smtp.send_message(msg)
                                    st.success("Email sent successfully!")
                                except Exception as e:
                                    logger.error(f"Error sending email: {str(e)}")
                                    st.error("Failed to send email.")

                            if st.button("Submit Evaluation", key=f"submit_{level}_{trainer_id}"):
                                try:
                                    entry = {
                                        "Trainer ID": trainer_id,
                                        "Trainer Name": trainer_name,
                                        "Department": department,
                                        "Date of assessment": datetime.today().date().strftime("%Y-%m-%Y"),
                                        "Evaluator Username": evaluator_username,
                                        "Evaluator Role": evaluator_role,
                                        f"{level}": status,
                                        f"{level} Reminder": reminder,
                                        "Manager Referral": manager_referral if level == "LEVEL #3" else ""
                                    }

                                    total_score = 0
                                    param_count = len(relevant_params[evaluator_role])
                                    for i in range(1, 11):
                                        course_key = f"{level} Course :{i}"
                                        course_data = courses.get(course_key, {})
                                        entry[course_key] = course_data.get("name", "")
                                        entry[f"{course_key} TOTAL"] = course_data.get("total", 0)
                                        entry[f"{course_key} AVERAGE"] = course_data.get("average", 0.0)
                                        entry[f"{course_key} STATUS"] = course_data.get("status_overall", "REDO")
                                        entry[f"{course_key} Remarks"] = course_data.get("remarks", "")
                                        for param in relevant_params[evaluator_role]:
                                            entry[f"{param} Course :{i}"] = course_data.get("params", {}).get(param, 0)
                                        total_score += course_data.get("total", 0)
                                    entry[f"{level} TOTAL"] = total_score
                                    entry[f"{level} AVERAGE"] = total_score / (param_count * 10) if param_count * 10 > 0 else 0.0

                                    for lvl in levels:
                                        all_courses_filled = all(courses.get(f"{lvl} Course :{i}", {}).get("name") and courses.get(f"{lvl} Course :{i}", {}).get("passed") for i in range(1, 11))
                                        if lvl in ["LEVEL #1", "LEVEL #2"] and entry.get(lvl) == "QUALIFIED" and submissions.get(f"{lvl}_submissions", 0) >= 2:
                                            if not all_courses_filled or entry.get(f"{lvl} AVERAGE", 0.0) < 75.0:
                                                entry[lvl] = "NOT QUALIFIED"
                                                st.warning(f"{lvl} requires 10 completed courses with at least 75% average.")
                                        if lvl == "LEVEL #3" and entry.get(lvl) == "QUALIFIED" and submissions.get(f"{lvl}_submissions", 0) >= 2:
                                            if not all_courses_filled or entry.get(f"{lvl} AVERAGE", 0.0) < 90.0 or not entry.get("Manager Referral"):
                                                entry[lvl] = "NOT QUALIFIED"
                                                st.warning(f"{lvl} requires 10 completed courses, 90% average, and Manager Referral.")

                                    updated_df = pd.concat([df_main, pd.DataFrame([entry])], ignore_index=True)
                                    updated_df.to_csv(CSV_FILE, index=False)

                                    st.success(f"✅ Assessment Saved for Trainer ID: {trainer_id}")

                                    # Enhancement 13: Resolve this error + “Tried adding all 3 courses assessment, submitted the evaluation, nowhere the scores were updated, not in evaluator page nor in viewer section”
                                    # Solution: Rerun after submit to refresh all sections
                                    st.rerun()

                                    st.markdown("### 📥 Download Submitted Assessment")
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        csv_data = pd.DataFrame([entry]).to_csv(index=False)
                                        st.download_button(
                                            label="Download Assessment CSV",
                                            data=csv_data,
                                            file_name=f"assessment_{trainer_id}_{datetime.now().strftime('%Y%m%d')}.csv",
                                            mime="text/csv",
                                            key=f"download_button_eval_csv_{trainer_id}"
                                        )
                                    with col2:
                                        try:
                                            buffer = BytesIO()
                                            pdf = canvas.Canvas(buffer, pagesize=A4)
                                            pdf.setFont("Helvetica", 12)
                                            y = 750
                                            pdf.drawString(100, y, f"Trainer Assessment Report")
                                            y -= 20
                                            pdf.drawString(100, y, f"Trainer ID: {trainer_id}")
                                            y -= 20
                                            pdf.drawString(100, y, f"Trainer Name: {trainer_name}")
                                            y -= 20
                                            pdf.drawString(100, y, f"Department: {department}")
                                            y -= 20
                                            pdf.drawString(100, y, f"Date: {datetime.today().date()}")
                                            y -= 30
                                            for lvl in levels:
                                                pdf.drawString(100, y, f"{lvl} Assessment")
                                                y -= 20
                                                pdf.drawString(100, y, f"Status: {entry.get(lvl, 'N/A')}")
                                                y -= 20
                                                pdf.drawString(100, y, f"Total: {entry.get(f'{lvl} TOTAL', 'N/A')}")
                                                y -= 20
                                                pdf.drawString(100, y, f"Average: {entry.get(f'{lvl} AVERAGE', 'N/A'):.2f}")
                                                y -= 20
                                                pdf.drawString(100, y, f"Reminder: {entry.get(f'{lvl} Reminder', 'N/A')}")
                                                y -= 20
                                                if lvl == "LEVEL #3":
                                                    pdf.drawString(100, y, f"Manager Referral: {entry.get('Manager Referral', 'N/A')}")
                                                    y -= 20
                                                for i in range(1, 11):
                                                    pdf.drawString(100, y, f"Course :{i}: {entry.get(f'{lvl} Course :{i}', 'N/A')}")
                                                    y -= 20
                                                    for param in relevant_params[evaluator_role]:
                                                        pdf.drawString(120, y, f"{param}: {entry.get(f'{param} Course :{i}', 'N/A')}")
                                                        y -= 20
                                                    pdf.drawString(120, y, f"TOTAL: {entry.get(f'{lvl} Course :{i} TOTAL', 'N/A')}")
                                                    y -= 20
                                                    pdf.drawString(120, y, f"AVERAGE: {entry.get(f'{lvl} Course :{i} AVERAGE', 'N/A'):.2f}")
                                                    y -= 20
                                                    pdf.drawString(120, y, f"STATUS: {entry.get(f'{lvl} Course :{i} STATUS', 'N/A')}")
                                                    y -= 20
                                                    pdf.drawString(120, y, f"Remarks: {entry.get(f'{lvl} Course :{i} Remarks', 'N/A')}")
                                                    y -= 20
                                                    if y < 50:
                                                        pdf.showPage()
                                                        pdf.setFont("Helvetica", 12)
                                                        y = 750
                                                if y < 50:
                                                    pdf.showPage()
                                                    pdf.setFont("Helvetica", 12)
                                                    y = 750
                                            pdf.save()
                                            pdf_data = buffer.getvalue()
                                            buffer.close()
                                            st.download_button(
                                                label="Download Assessment PDF",
                                                data=pdf_data,
                                                file_name=f"assessment_{trainer_id}_{datetime.now().strftime('%Y%m%d')}.pdf",
                                                mime="application/pdf",
                                                key=f"download_button_eval_pdf_{trainer_id}"
                                            )
                                        except Exception as e:
                                            logger.error(f"Error generating PDF: {str(e)}")
                                            st.error("Failed to generate PDF report.")
                                except Exception as e:
                                    logger.error(f"Error submitting evaluation: {str(e)}")
                                    st.error("Failed to submit evaluation. Please try again.")
                except Exception as e:
                    logger.error(f"Error in assessment section: {str(e)}")
                    st.error("Failed to process assessment section.")
        if st.button("View All Trainers", key="view_all_trainers"):
            try:
                if os.path.exists(DEFAULT_DATA_FILE):
                    all_trainers = pd.read_csv(DEFAULT_DATA_FILE)[["Trainer ID", "Trainer Name", "Department", "Branch"]].drop_duplicates()
                    st.markdown("### 🆔 All Trainers")
                    st.dataframe(all_trainers, use_container_width=True)
                else:
                    st.error("EVALUATOR_INPUT.csv not found.")
            except Exception as e:
                logger.error(f"Error viewing all trainers: {str(e)}")
                st.error("Failed to display trainer list.")

        if st.button("Logout", key="evaluator_logout"):
            try:
                for key in ["logged_in", "role", "logged_user"]:
                    if key in st.session_state:
                        del st.session_state[key]
                st.success("Logged out successfully!")
                st.rerun()
            except Exception as e:
                logger.error(f"Error during logout: {str(e)}")
                st.error("Failed to logout. Please try again.")
    except Exception as e:
        logger.error(f"Error in evaluator section: {str(e)}")
        st.error("An unexpected error occurred in the Evaluator Dashboard.")
        
def viewer_section(df_main):
    try:
        st.subheader("👀 Viewer Dashboard")
        if "logged_in" not in st.session_state or not st.session_state.get("logged_in"):
            st.warning("Please login to access the viewer panel.")
            return

        df = df_main.copy()
        if "Trainer ID" not in df.columns:
            st.error("❌ 'Trainer ID' column missing in data.")
            return

        st.markdown("### 📋 Trainer Assessments")
        trainer_filter = st.text_input("Filter by Trainer Name or ID", "", help="Press Enter to Apply")

        filtered = df.copy()
        if trainer_filter:
            try:
                mask = filtered["Trainer ID"].astype(str).str.contains(trainer_filter, case=False, na=False) | \
                       filtered["Trainer Name"].astype(str).str.contains(trainer_filter, case=False, na=False)
                filtered = filtered[mask]
            except Exception as e:
                logger.error(f"Error filtering trainers: {str(e)}")
                st.error("Failed to apply trainer filter.")

        if not filtered.empty:
            st.markdown("#### Matching Trainer Assessments")
            st.dataframe(filtered.fillna("No data entered"), use_container_width=True)

        trainer_ids = sorted(filtered["Trainer ID"].dropna().unique().tolist())
        selected_trainer = st.selectbox("Select Trainer for Detailed Report", [""] + trainer_ids)
        if selected_trainer:
            trainer_report = df[df["Trainer ID"] == selected_trainer]
            if trainer_report.empty:
                st.info("No data entered for this trainer.")
            else:
                st.markdown(f"##### Reports for Trainer ID: {selected_trainer}")
                st.dataframe(trainer_report.fillna("No data entered"))

            col1, col2 = st.columns(2)
            with col1:
                csv_data = trainer_report.fillna("No data entered").to_csv(index=False)
                st.download_button(
                    label="Download Trainer Report CSV",
                    data=csv_data,
                    file_name=f"trainer_{selected_trainer}_reports.csv",
                    mime="text/csv",
                    key=f"download_button_trainer_csv_{selected_trainer}"
                )
            with col2:
                try:
                    buffer = BytesIO()
                    pdf = canvas.Canvas(buffer, pagesize=A4)
                    pdf.setFont("Helvetica", 12)
                    y = 750
                    pdf.drawString(100, y, f"Trainer Report: {selected_trainer}")
                    y -= 20
                    pdf.drawString(100, y, f"Generated on: {datetime.now().strftime('%d-%m-%Y %I:%M %p IST')}")
                    y -= 30
                    for level in ["LEVEL #1", "LEVEL #2", "LEVEL #3"]:
                        pdf.drawString(100, y, f"{level} Assessment")
                        y -= 20
                        for i in range(1, 11):
                            course = trainer_report.iloc[-1].get(f"{level} Course :{i}", "N/A") if not trainer_report.empty else "N/A"
                            pdf.drawString(100, y, f"Course :{i}: {course}")
                            y -= 20
                            if y < 50:
                                pdf.showPage()
                                pdf.setFont("Helvetica", 12)
                                y = 750
                    pdf.showPage()
                    pdf.save()
                    pdf_data = buffer.getvalue()
                    buffer.close()
                    st.download_button(
                        label="Download Trainer PDF",
                        data=pdf_data,
                        file_name=f"trainer_{selected_trainer}_assessment.pdf",
                        mime="application/pdf",
                        key=f"download_button_pdf_{selected_trainer}"
                    )
                except Exception as e:
                    logger.error(f"Error generating PDF: {str(e)}")
                    st.error("Failed to generate PDF report.")

        if st.button("View All Trainers", key="view_all_trainers"):
            try:
                if os.path.exists(DEFAULT_DATA_FILE):
                    all_trainers = pd.read_csv(DEFAULT_DATA_FILE)[["Trainer ID", "Trainer Name", "Department", "Branch"]].drop_duplicates()
                    st.markdown("### 🆔 All Trainers")
                    st.dataframe(all_trainers, use_container_width=True)
                else:
                    st.error("EVALUATOR_INPUT.csv not found.")
            except Exception as e:
                logger.error(f"Error viewing all trainers: {str(e)}")
                st.error("Failed to display trainer list.")

        if st.button("Logout", key="viewer_logout"):
            try:
                for key in ["logged_in", "role", "logged_user"]:
                    if st.session_state.get(key):
                        del st.session_state[key]
                st.success("Logged out successfully!")
                st.rerun()
            except Exception as e:
                logger.error(f"Error during logout: {str(e)}")
                st.error("Failed to logout. Please try again.")
    except Exception as e:
        logger.error(f"Error in viewer section: {str(e)}")
        st.error("An unexpected error occurred in the Viewer Dashboard.")

def admin_section(df_main):
    try:
        st.subheader("👨‍💼 Super Administrator Section")

        if "logged_in" not in st.session_state or not st.session_state.get("logged_in"):
            st.warning("Please login to access the admin panel.")
            return

        evaluators_df = load_evaluators()
        st.markdown("### 🧑‍💻 Existing Evaluators")
        try:
            if not evaluators_df.empty:
                st.dataframe(evaluators_df[["username", "full_name", "email", "role", "created_at"]], use_container_width=True)
            else:
                st.info("No evaluators found in the system.")
        except Exception as e:
            logger.error(f"Error displaying evaluators list: {str(e)}")
            st.error("Failed to display evaluators list.")

        cols = st.columns([1, 1, 1, 1])
        if cols[0].button("Add New Evaluator"):
            st.session_state.admin_section = "add_evaluator"
        if cols[1].button("Existing Evaluators"):
            st.session_state.admin_section = "existing_evaluators"
        if cols[2].button("Edit Evaluator"):
            st.session_state.admin_section = "edit_evaluator"
        if cols[3].button("Delete Evaluator"):
            st.session_state.admin_section = "delete_evaluator"

        section = st.session_state.get("admin_section", "trainer_reports")
        evaluators_df = load_evaluators()

        if section == "add_evaluator":
            st.markdown("### 🧑‍💻 Add New Evaluator")
            with st.form("add_eval_form", clear_on_submit=True):
                new_username = st.text_input("Username", key="new_eval_user")
                new_password = st.text_input("Password", type="password", key="new_eval_pass")
                confirm_password = st.text_input("Confirm Password", type="password", key="new_eval_confirm_pass")
                full_name = st.text_input("Full Name", key="new_eval_name")
                email = st.text_input("Email", key="new_eval_email")
                role_select = st.selectbox("Role", ["Evaluator", "Viewer", "Super Administrator"], key="new_eval_role")
                submitted = st.form_submit_button("Add Evaluator")
                if submitted:
                    try:
                        if not new_username or not new_password:
                            st.error("Username and password are required.")
                        elif new_password != confirm_password:
                            st.error("Passwords do not match.")
                        elif new_username in evaluators_df["username"].values:
                            st.error("Username already exists.")
                        else:
                            new_entry = {
                                "username": new_username,
                                "password_hash": hash_password(new_password),
                                "full_name": full_name,
                                "email": email,
                                "role": role_select,
                                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }
                            evaluators_df = pd.concat([evaluators_df, pd.DataFrame([new_entry])], ignore_index=True)
                            save_evaluators(evaluators_df)
                            st.success(f"Evaluator '{new_username}' added.")
                            st.session_state.admin_section = "trainer_reports"
                    except Exception as e:
                        logger.error(f"Error adding evaluator: {str(e)}")
                        st.error("Failed to add new evaluator.")

        elif section == "existing_evaluators":
            st.markdown("### 🧑‍💻 Existing Evaluators")
            try:
                st.dataframe(evaluators_df[["username", "full_name", "email", "role", "created_at"]])
                if st.button("Back to Main"):
                    st.session_state.admin_section = "trainer_reports"
            except Exception as e:
                logger.error(f"Error displaying evaluators: {str(e)}")
                st.error("Failed to display evaluators list.")

        elif section == "edit_evaluator":
            st.markdown("### 🧑‍💻 Edit Evaluator")
            selected_eval = st.selectbox("Select Evaluator to Edit", [""] + evaluators_df["username"].tolist(), key="select_eval_edit")
            if selected_eval:
                try:
                    row = evaluators_df[evaluators_df["username"] == selected_eval].iloc[0].to_dict()
                    with st.form(f"edit_eval_form_{selected_eval}"):
                        st.markdown(f"**Username:** {row['username']} (immutable)")
                        edit_full_name = st.text_input("Full Name", value=row.get("full_name", ""), key=f"name_{selected_eval}")
                        edit_email = st.text_input("Email", value=row.get("email", ""), key=f"email_{selected_eval}")
                        edit_role = st.selectbox("Role", ["Evaluator", "Viewer", "Super Administrator"],
                                                 index=["Evaluator", "Viewer", "Super Administrator"].index(row.get("role", "Evaluator")),
                                                 key=f"role_{selected_eval}")
                        change_password = st.checkbox("Change Password", key=f"chpass_{selected_eval}")
                        new_pass = ""
                        confirm_pass = ""
                        if change_password:
                            new_pass = st.text_input("New Password", type="password", key=f"newpass_{selected_eval}")
                            confirm_pass = st.text_input("Confirm New Password", type="password", key=f"confirmpass_{selected_eval}")
                        edit_submitted = st.form_submit_button("Save Changes")
                        if edit_submitted:
                            try:
                                if change_password and new_pass != confirm_pass:
                                    st.error("Passwords do not match.")
                                else:
                                    idx = evaluators_df.index[evaluators_df["username"] == selected_eval][0]
                                    evaluators_df.at[idx, "full_name"] = edit_full_name
                                    evaluators_df.at[idx, "email"] = edit_email
                                    evaluators_df.at[idx, "role"] = edit_role
                                    if change_password and new_pass:
                                        evaluators_df.at[idx, "password_hash"] = hash_password(new_pass)
                                    save_evaluators(evaluators_df)
                                    st.success(f"Evaluator '{selected_eval}' updated.")
                            except Exception as e:
                                logger.error(f"Error editing evaluator: {str(e)}")
                                st.error("Failed to edit evaluator.")
                except Exception as e:
                    logger.error(f"Error editing evaluator: {str(e)}")
                    st.error("Failed to edit evaluator.")
            if st.button("Back to Main"):
                st.session_state.admin_section = "trainer_reports"

        elif section == "delete_evaluator":
            st.markdown("### 🧑‍💻 Delete Evaluator")
            selected_eval = st.selectbox("Select Evaluator to Delete", [""] + evaluators_df["username"].tolist(), key="select_eval_delete")
            if selected_eval:
                if st.button(f"Confirm Delete Evaluator '{selected_eval}'"):
                    try:
                        evaluators_df = evaluators_df[evaluators_df["username"] != selected_eval].reset_index(drop=True)
                        save_evaluators(evaluators_df)
                        st.warning(f"Evaluator '{selected_eval}' deleted.")
                    except Exception as e:
                        logger.error(f"Error deleting evaluator: {str(e)}")
                        st.error("Failed to delete evaluator.")
            if st.button("Back to Main"):
                st.session_state.admin_section = "trainer_reports"

        else:
            st.markdown("---")
            st.markdown("### 📋 Trainer Reports Overview")

            trainer_filter = st.text_input("Filter by Trainer Name or ID", "", help="Press Enter to Apply")
            
            filtered = df_main.copy()
            if trainer_filter:
                try:
                    mask = filtered["Trainer ID"].astype(str).str.contains(trainer_filter, case=False, na=False) | \
                           filtered["Trainer Name"].astype(str).str.contains(trainer_filter, case=False, na=False)
                    filtered = filtered[mask]
                except Exception as e:
                    logger.error(f"Error filtering trainers: {str(e)}")
                    st.error("Failed to apply trainer filter.")

            if not filtered.empty:
                st.markdown("#### Matching Trainer Assessments")
                st.dataframe(filtered)

            trainer_ids = sorted(filtered["Trainer ID"].dropna().unique().tolist())
            selected_trainer = st.selectbox("Select Trainer for Detailed Report", [""] + trainer_ids)
            if selected_trainer:
                trainer_reports = df_main[df_main["Trainer ID"] == selected_trainer]
                st.markdown(f"##### Reports for Trainer ID: {selected_trainer}")
                st.dataframe(trainer_reports)

                col1, col2, col3 = st.columns(3)
                with col1:
                    csv_data = trainer_reports.to_csv(index=False)
                    st.download_button(
                        label="Download Trainer Report CSV",
                        data=csv_data,
                        file_name=f"trainer_{selected_trainer}_reports.csv",
                        mime="text/csv",
                        key=f"download_button_trainer_csv_{selected_trainer}"
                    )
                with col2:
                    csv_data_all = filtered.to_csv(index=False)
                    st.download_button(
                        label="Download All Filtered Reports CSV",
                        data=csv_data_all,
                        file_name="filtered_trainer_reports.csv",
                        mime="text/csv",
                        key="download_button_filtered_csv"
                    )
                with col3:
                    try:
                        buffer = BytesIO()
                        pdf = canvas.Canvas(buffer, pagesize=A4)
                        pdf.setFont("Helvetica", 12)
                        y = 750
                        pdf.drawString(100, y, "Evaluator and Trainer Report")
                        y -= 20
                        pdf.drawString(100, y, f"Generated on: {datetime.now().strftime('%d-%m-%Y %I:%M %p IST')}")
                        y -= 30
                        pdf.drawString(100, y, "Evaluators")
                        y -= 20
                        pdf.setFillColor(colors.black)
                        pdf.drawString(100, y, "Username  Full Name  Email  Role  Created At")
                        y -= 20
                        for _, row in evaluators_df.iterrows():
                            text = f"{row['username']}  {row['full_name']}  {row['email']}  {row['role']}  {row['created_at']}"
                            pdf.drawString(100, y, text)
                            y -= 20
                            if y < 50:
                                pdf.showPage()
                                pdf.setFont("Helvetica", 12)
                                y = 750
                        y -= 20
                        pdf.drawString(100, y, "Trainers")
                        y -= 20
                        pdf.drawString(100, y, "Trainer ID  Trainer Name  Branch  Department")
                        y -= 20
                        if os.path.exists(DEFAULT_DATA_FILE):
                            trainers_df = pd.read_csv(DEFAULT_DATA_FILE)
                            for _, row in trainers_df.iterrows():
                                text = f"{row['Trainer ID']}  {row['Trainer Name']}  {row.get('Branch', '')}  {row.get('Department', '')}"
                                pdf.drawString(100, y, text)
                                y -= 20
                                if y < 50:
                                    pdf.showPage()
                                    pdf.setFont("Helvetica", 12)
                                    y = 750
                        pdf.showPage()
                        pdf.save()
                        pdf_data = buffer.getvalue()
                        buffer.close()
                        st.download_button(
                            label="Download Evaluators/Trainers PDF",
                            data=pdf_data,
                            file_name="evaluators_trainers_report.pdf",
                            mime="application/pdf",
                            key="download_button_admin_pdf"
                        )
                    except Exception as e:
                        logger.error(f"Error generating PDF: {str(e)}")
                        st.error("Failed to generate PDF report.")

        if st.button("Logout", key="admin_logout"):
            try:
                for key in ["logged_in", "role", "logged_user"]:
                    if key in st.session_state:
                        del st.session_state[key]
                st.success("Logged out successfully!")
                st.rerun()
            except Exception as e:
                logger.error(f"Error during logout: {str(e)}")
                st.error("Failed to logout. Please try again.")
    except Exception as e:
        logger.error(f"Error in admin section: {str(e)}")
        st.error("An unexpected error occurred in the Admin Dashboard.")

def set_background(image_file):
    try:
        with open(image_file, "rb") as image:
            img_bytes = base64.b64encode(image.read()).decode()
        page_bg_img = f"""
        <style>
        .stApp {{
            background-image: url("data:image/jpg;base64,{img_bytes}");
            background-size: cover;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        </style>
        """
        st.markdown(page_bg_img, unsafe_allow_html=True)
    except Exception as e:
        logger.error(f"Error setting background: {str(e)}")
        st.error("Failed to set background image.")

def login_ui():
    try:
        st.sidebar.title("🔐 Login Panel")

        role = st.radio("Select Role", ["Viewer", "Evaluator", "Super_Administrator"])
        bg_image = f"background{'' if role == 'Viewer' else '1' if role == 'Evaluator' else '2'}.jpg"
        if os.path.exists(bg_image):
            set_background(bg_image)

        col1, col2 = st.columns([4, 1])

        with col1:
            st.title("🧑‍💼 Assessment Login Form")
            username = st.text_input("Username", key="username_input")
            password = st.text_input("Password", type="password", key="password_input")
            login_btn = st.button("🔓 Login")

            if login_btn:
                try:
                    if (role == "Viewer" and username == "omotec" and password == "omotec") or \
                       (role == "Evaluator" and username == "omotec1" and password == "omotec123") or \
                       (role == "Super_Administrator" and username == "omotec2" and password == "omotec@123#"):
                        st.session_state.logged_in = True
                        st.session_state["role"] = role.replace("_", " ")
                        st.session_state["logged_user"] = username
                        st.success(f"✅ Logged in successfully as {role.replace('_', ' ')}!")
                        st.rerun()
                    else:
                        st.error("❌ Invalid Login Credentials")
                except Exception as e:
                    logger.error(f"Error during login: {str(e)}")
                    st.error("Failed to process login. Please try again.")

        with col2:
            if os.path.exists("NEW LOGO - OMOTEC.png"):
                st.image("NEW LOGO - OMOTEC.png", use_column_width=True)
    except Exception as e:
        logger.error(f"Error in login UI: {str(e)}")
        st.error("An unexpected error occurred in the Login Panel.")

def main():
    try:
        if "logged_in" not in st.session_state or not st.session_state.get("logged_in"):
            login_ui()
        else:
            df_main = load_data()
            role = st.session_state.get("role", "")
            if role == "Evaluator":
                evaluator_section(df_main)
            elif role == "Viewer":
                viewer_section(df_main)
            elif role == "Super Administrator":
                admin_section(df_main)
            else:
                st.warning("Invalid role. Please login with a valid role.")
    except Exception as e:
        logger.error(f"Error in main function: {str(e)}")
        st.error("An unexpected error occurred in the application.")

if __name__ == "__main__":
    main()