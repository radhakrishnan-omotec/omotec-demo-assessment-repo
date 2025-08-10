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
        st.warning("Failed to generate Trainer ID. Using default ID.")
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

def send_email_reminder(email, level, trainer_id, trainer_name, reminder):
    try:
        email_body = f"Reminder for {level} Assessment\nTrainer ID: {trainer_id}\nTrainer Name: {trainer_name}\nReminder: {reminder}"
        email_subject = f"{level} Assessment Reminder for Trainer {trainer_id}"
        mailto_link = f"mailto:{urllib.parse.quote(email)}?subject={urllib.parse.quote(email_subject)}&body={urllib.parse.quote(email_body)}"
        return mailto_link
    except Exception as e:
        logger.error(f"Error preparing email reminder for {level}: {str(e)}")
        st.error(f"Failed to prepare reminder email for {level}.")
        return None

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
            background-color: #A69500 !important; /* Gold */
            padding: 10px;
            border-radius: 5px;
            color: white;
        }
        .level-2-heading {
            background-color: #00A191 !important; /* Bright */
            padding: 10px;
            border-radius: 5px;
            color: white;
        }
        .level-3-heading {
            background-color: #8EC200 !important; /* Brighter */
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

        evaluator_role = st.selectbox("Select Evaluator Role", ["Technical Evaluator", "School Operations Evaluator"], key="evaluator_role")
        evaluator_username = st.session_state.get("logged_user", "")

        relevant_params = {
            "Technical Evaluator": [
                "Has Knowledge of STEM (5)", "Ability to integrate STEM With related activities (10)",
                "Discusses Up-to-date information related to STEM (5)", "Provides Course Outline (5)",
                "Language Fluency (5)", "Preparation with Lesson Plan / Practicals (5)"
            ],
            "School Operations Evaluator": [
                "Time Based Activity (5)", "Student Engagement Ideas (5)", "Pleasing Look (5)",
                "Poised & Confident (5)", "Well Modulated Voice (5)"
            ]
        }

        mode = st.radio("Select Trainer ID Mode", ["Enter Existing Trainer ID", "New Trainer Creation ID"])
        trainer_id = ""
        trainer_name = ""
        department = ""
        trainer_email = ""

        if mode.startswith("Enter"):
            try:
                if os.path.exists(DEFAULT_DATA_FILE):
                    eval_inputs_df = pd.read_csv(DEFAULT_DATA_FILE).fillna("")
                    if "Trainer ID" not in eval_inputs_df.columns:
                        st.error("❌ 'Trainer ID' column missing in EVALUATOR_INPUT.csv.")
                        return
                    available_ids = eval_inputs_df["Trainer ID"].dropna().unique().tolist()
                    if not available_ids:
                        st.warning("No Trainer IDs found in EVALUATOR_INPUT.csv.")
                        return
                    selected_id = st.selectbox("Select Existing Trainer ID", available_ids)
                    trainer_data = eval_inputs_df[eval_inputs_df["Trainer ID"] == selected_id].iloc[0].to_dict()
                    trainer_id = trainer_data.get("Trainer ID", "")
                    trainer_name = trainer_data.get("Trainer Name", "")
                    department = trainer_data.get("Department", "")
                    trainer_email = trainer_data.get("Email", "")
                    st.success(f"Loaded Trainer: {trainer_name} ({department})")
                    if trainer_email:
                        st.info(f"Trainer Email: {trainer_email}")
                    else:
                        st.warning("No email found for this trainer in EVALUATOR_INPUT.csv")
                else:
                    st.error("EVALUATOR_INPUT.csv not found.")
                    return
            except Exception as e:
                logger.error(f"Error loading existing trainer data: {str(e)}")
                st.error("Failed to load trainer data.")
                return

        else:
            trainer_id = st.text_input("Enter New Trainer ID (leave blank to auto-generate)")
            trainer_name = st.text_input("Trainer Name (for new ID)")
            department = st.text_input("Department (for new ID)")
            trainer_email = st.text_input("Trainer Email (for new ID)")
            if trainer_id.strip() == "":
                if trainer_name and department and trainer_email:
                    try:
                        trainer_id = generate_new_trainer_id()
                        st.success(f"Auto-generated Trainer ID: {trainer_id}")
                        save_new_trainer_to_input(trainer_id, trainer_name, department, trainer_email)
                        st.success(f"Trainer {trainer_name} ({trainer_id}) added to existing trainers list.")
                    except Exception as e:
                        logger.error(f"Error creating new trainer: {str(e)}")
                        st.error("Failed to create new trainer.")
                else:
                    st.warning("Please enter Trainer Name, Department, and Email to auto-generate Trainer ID.")

        past_assessments = df[df["Trainer ID"] == trainer_id] if trainer_id else pd.DataFrame()
        if not past_assessments.empty:
            st.markdown("### 🔁 Previous Assessments")
            st.dataframe(past_assessments, use_container_width=True)

        levels = ["LEVEL #1", "LEVEL #2", "LEVEL #3"]
        level_status = {}
        submissions = {}
        assessment_data = {}

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

        for level in levels:
            # Apply bright background colors to level headings
            level_class = f"level-{level.split('#')[1]}-heading"
            st.markdown(f'<div class="{level_class}">🔹 {level} Assessment</div>', unsafe_allow_html=True)
            with st.expander(f"{level} Assessment"):
                try:
                    if level_status.get(level) == "QUALIFIED" and submissions.get(f"{level}_submissions", 0) >= 2:
                        st.write(f"{level} already qualified by both evaluators.")
                    elif level_status.get(level) == "QUALIFIED" and submissions.get(f"{level}_submissions", 0) == 1:
                        st.write(f"{level} qualified by one evaluator. Awaiting second evaluation.")
                    else:
                        if level == "LEVEL #1" or \
                           (level == "LEVEL #2" and level_status.get("LEVEL #1") == "QUALIFIED") or \
                           (level == "LEVEL #3" and level_status.get("LEVEL #2") == "QUALIFIED"):
                            # Course inputs in horizontal tabs
                            st.markdown(f"### {level} Courses")
                            courses = {}
                            all_courses_filled = True
                            course_params = {f"Course :{i}": {} for i in range(1, 11)}
                            tabs = st.tabs([f"Course :{i}" for i in range(1, 11)])
                            for i, tab in enumerate(tabs, 1):
                                with tab:
                                    # Course inputs (moved above parameters)
                                    course_key = f"{level} Course :{i}"
                                    course_name = st.text_input(
                                        f"{course_key} Name",
                                        key=f"course_{level}_{i}_{trainer_id}",
                                        placeholder="Type course name or select below"
                                    )
                                    course_select = st.selectbox(
                                        f"{course_key} Select",
                                        options=COURSE_OPTIONS,
                                        key=f"course_select_{level}_{i}_{trainer_id}"
                                    )
                                    # Role-specific parameters for this course
                                    st.markdown(f"#### Parameters for Course :{i}")
                                    part_params = [p for p in relevant_params[evaluator_role] if any(p in col for col in df.columns)]
                                    for k in part_params:
                                        value = past_assessments[k].iloc[0] if not past_assessments.empty and k in past_assessments.columns else ""
                                        course_params[f"Course :{i}"][k] = st.text_input(
                                            f"{k} (Course :{i})",
                                            value=value,
                                            key=f"{k}_{level}_course_{i}_{trainer_id}"
                                        )
                                    # TOTAL, AVERAGE, STATUS (moved above Course Passed)
                                    total = st.number_input(
                                        f"Course :{i} TOTAL",
                                        min_value=0, max_value=100, step=1,
                                        key=f"total_{level}_course_{i}_{trainer_id}"
                                    )
                                    avg = st.number_input(
                                        f"Course :{i} AVERAGE",
                                        min_value=0.0, max_value=100.0, step=0.1,
                                        key=f"avg_{level}_course_{i}_{trainer_id}"
                                    )
                                    status_overall = st.selectbox(
                                        f"Course :{i} STATUS",
                                        ["CLEARED", "REDO"],
                                        key=f"status_{level}_course_{i}_{trainer_id}"
                                    )
                                    # Course Passed checkbox
                                    course_passed = st.checkbox(
                                        f"{course_key} Passed",
                                        key=f"course_pass_{level}_{i}_{trainer_id}"
                                    )
                                    final_course = course_name if course_name else course_select
                                    courses[course_key] = {
                                        "name": final_course,
                                        "passed": course_passed,
                                        "total": total,
                                        "average": avg,
                                        "status_overall": status_overall,
                                        "params": course_params[f"Course :{i}"]
                                    }
                                    if not final_course or not course_passed:
                                        all_courses_filled = False

                                    

                            # Level assessment inputs
                            level_status_key = f"{level}_status_{evaluator_role}"
                            status_options = ["NOT QUALIFIED"] if not all_courses_filled else ["QUALIFIED", "NOT QUALIFIED"]
                            status = st.selectbox(f"{level} Status", status_options, key=level_status_key)

                            manager_referral = ""
                            if level == "LEVEL #3":
                                manager_referral = st.text_input(
                                    "Manager Referral (Required for Level 3)",
                                    key=f"manager_referral_{level}_{trainer_id}"
                                )

                            
                            reminder_email = st.text_input(
                                "Evaluator Email for Reminder", key=f"reminder_email_{level}_{trainer_id}"
                            )
                            reminder = st.text_area("Reminder Message Content", key=f"reminder_{level}_{trainer_id}")

                            # New SEND EMAIL button with updated logic
                            if st.button("SEND EMAIL", key=f"send_email_{level}_{trainer_id}"):
                                try:
                                    if not reminder_email or '@' not in reminder_email:
                                        st.error("No valid recipient email found. Please enter a valid email address for sending reminders.")
                                    else:
                                        email_body = f"Reminder for Trainer ID: {trainer_id}\n"
                                        email_body += f"Trainer Name: {trainer_name}\n"
                                        email_body += f"Department: {department}\n"
                                        email_body += f"Date of Assessment: {datetime.today().date()}\n"
                                        email_body += f"Evaluator: {evaluator_username} ({evaluator_role})\n"
                                        email_body += f"\nReminder Message:\n{reminder or 'No reminder message provided.'}\n"

                                        # Include brief course status summary
                                        email_body += f"\nAssessment Overview for {level}:\n"
                                        for i in range(1, 11):
                                            course_key = f"{level} Course :{i}"  # Fixed course_key format
                                            course_data = courses.get(course_key, {})
                                            course_name = course_data.get("name", "N/A")
                                            course_passed = course_data.get("passed", False)
                                            email_body += f"  Course :{i}: {course_name} ({'Passed' if course_passed else 'Not Passed'})\n"

                                        if manager_referral and level == "LEVEL #3":
                                            email_body += f"\nManager Referral: {manager_referral}\n"

                                        email_subject = f"Reminder for Trainer {trainer_id} - {level} - {datetime.today().date()}"
                                        mailto_link = f"mailto:{urllib.parse.quote(reminder_email)}?subject={urllib.parse.quote(email_subject)}&body={urllib.parse.quote(email_body)}"

                                        st.markdown(f'<a href="{mailto_link}" target="_blank">Open Email Client for Reminder</a>', unsafe_allow_html=True)
                                        st.success(f"Reminder email prepared for {reminder_email} (Simulation)")
                                except Exception as e:
                                    logger.error(f"Error preparing reminder email for {level}: {str(e)}")
                                    st.error(f"Failed to prepare reminder email for {level}.")

                            # Send Score Card button for this level
                            send_report_enabled = status == "QUALIFIED" and submissions.get(f"{level}_submissions", 0) >= 2 and all_courses_filled
                            score_status = st.selectbox(
                                "Status of Score Card",
                                ["Score Cards has not been sent"] if not send_report_enabled else ["Score Cards has been sent", "Score Cards has not been sent"],
                                key=f"score_status_{level}_{trainer_id}",
                                help="Select the status of the score card. 'Score Cards has not been sent' enables sending."
                            )
                            send_score_card_disabled = score_status != "Score Cards has not been sent"
                            if st.button("SEND SCORE CARD", disabled=send_score_card_disabled, key=f"send_score_card_{level}_{trainer_id}"):
                                try:
                                    if not trainer_email or '@' not in trainer_email:
                                        st.error("No valid trainer email found. Please ensure the trainer's email is provided in EVALUATOR_INPUT.csv or during new trainer creation.")
                                    else:
                                        email_body = f"Score Card for Trainer ID: {trainer_id}\n"
                                        email_body += f"Trainer Name: {trainer_name}\n"
                                        email_body += f"Department: {department}\n"
                                        email_body += f"Date of Assessment: {datetime.today().date()}\n"
                                        email_body += f"Evaluator: {evaluator_username} ({evaluator_role})\n"
                                        email_body += f"\nAssessment Details for {level}:\n"
                                        for i in range(1, 11):
                                            course_key = f"{level} Course :{i}"
                                            course_data = courses.get(course_key, {})
                                            email_body += f"\nCourse :{i}:\n"
                                            for param in relevant_params[evaluator_role]:
                                                param_value = course_data.get("params", {}).get(param, "N/A")
                                                email_body += f"  {param}: {param_value}\n"
                                            course_name = course_data.get("name", "N/A")
                                            course_passed = course_data.get("passed", False)
                                            email_body += f"  Course Name: {course_name} ({'Passed' if course_passed else 'Not Passed'})\n"
                                            email_body += f"  TOTAL: {course_data.get('total', 'N/A')}\n"
                                            email_body += f"  AVERAGE: {course_data.get('average', 'N/A')}\n"
                                            email_body += f"  STATUS: {course_data.get('status_overall', 'N/A')}\n"
                                        email_body += f"\n{level} Status: {status}\n"
                                        if manager_referral and level == "LEVEL #3":
                                            email_body += f"Manager Referral: {manager_referral}\n"
                                        email_body += f"Reminder: {reminder or 'None'}"
                                        email_subject = f"Score Card for Trainer {trainer_id} - {level} - {datetime.today().date()}"
                                        mailto_link = f"mailto:{urllib.parse.quote(trainer_email)}?subject={urllib.parse.quote(email_subject)}&body={urllib.parse.quote(email_body)}"
                                        st.markdown(f'<a href="{mailto_link}" target="_blank">Open Email Client</a>', unsafe_allow_html=True)
                                        st.success(f"Score card email prepared for Trainer ID: {trainer_id} to {trainer_email} for {level}")
                                        score_status = "Score Cards has been sent"
                                        st.session_state[f"score_status_{level}_{trainer_id}"] = score_status
                                except Exception as e:
                                    logger.error(f"Error sending score card for {level}: {str(e)}")
                                    st.error(f"Failed to prepare score card email for {level}.")

                            assessment_data[level] = {
                                "courses": courses,
                                "level_status": status,
                                "manager_referral": manager_referral if level == "LEVEL #3" else "",
                                "reminder": reminder,
                                "score_status": score_status
                            }
                        else:
                            st.warning(f"{level} is locked. Complete previous level(s) first.")
                except Exception as e:
                    logger.error(f"Error in {level} assessment: {str(e)}")
                    st.error(f"Failed to process {level} assessment.")

        if st.button("💾 Submit Evaluation", key="submit_evaluation"):
            try:
                if not trainer_id:
                    st.error("❌ Trainer ID is required.")
                    return

                entry = {
                    "Trainer ID": trainer_id,
                    "Trainer Name": trainer_name or "New",
                    "Department": department or "",
                    "DOJ": datetime.today().date(),
                    "Branch": "", "Discipline": "", "Course": "",
                    "Date of assessment": datetime.today().date(),
                    "Evaluator Username": evaluator_username,
                    "Evaluator Role": evaluator_role,
                }

                for level in levels:
                    if level_status.get(level) != "QUALIFIED" or submissions.get(f"{level}_submissions", 0) < 2:
                        data = assessment_data.get(level, {})
                        for i in range(1, 11):
                            course_key = f"{level} Course :{i}"
                            course_data = data.get("courses", {}).get(course_key, {})
                            entry[course_key] = course_data.get("name", "")
                            for param in relevant_params[evaluator_role]:
                                entry[f"{param} Course :{i}"] = course_data.get("params", {}).get(param, "")
                            entry[f"{course_key} TOTAL"] = course_data.get("total", 0)
                            entry[f"{course_key} AVERAGE"] = course_data.get("average", 0.0)
                            entry[f"{course_key} STATUS"] = course_data.get("status_overall", "REDO")
                        entry[f"{level} TOTAL"] = sum(data.get("courses", {}).get(f"{level} Course :{i}", {}).get("total", 0) for i in range(1, 11))
                        entry[f"{level} AVERAGE"] = sum(data.get("courses", {}).get(f"{level} Course :{i}", {}).get("average", 0.0) for i in range(1, 11)) / 10
                        entry[f"{level} STATUS"] = data.get("status_overall", "REDO")
                        entry[f"{level} Reminder"] = data.get("reminder", "")
                        entry[f"{level} Score Card Status"] = data.get("score_status", "Score Cards has not been sent")
                        entry[level] = data.get("level_status", "NOT QUALIFIED")
                        if level == "LEVEL #3" and data.get("manager_referral"):
                            entry["Manager Referral"] = data["manager_referral"]
                        break

                # Enforce Qualification Criteria
                for level in levels:
                    data = assessment_data.get(level, {})
                    courses = data.get("courses", {})
                    all_courses_filled = all(courses.get(f"{level} Course :{i}", {}).get("name") and courses.get(f"{level} Course :{i}", {}).get("passed") for i in range(1, 11))
                    if level == "LEVEL #1" and entry.get(level) == "QUALIFIED" and submissions.get(f"{level}_submissions", 0) >= 2:
                        if not all_courses_filled or entry.get(f"{level} AVERAGE", 0.0) < 75.0:
                            entry[level] = "NOT QUALIFIED"
                            st.warning(f"{level} requires 10 completed courses with at least 75% average.")
                    if level == "LEVEL #2" and entry.get(level) == "QUALIFIED" and submissions.get(f"{level}_submissions", 0) >= 2:
                        if not all_courses_filled or entry.get(f"{level} AVERAGE", 0.0) < 80.0:
                            entry[level] = "NOT QUALIFIED"
                            st.warning(f"{level} requires 10 completed courses with at least 80% average.")
                    if level == "LEVEL #3" and entry.get(level) == "QUALIFIED" and submissions.get(f"{level}_submissions", 0) >= 2:
                        if not all_courses_filled or entry.get(f"{level} AVERAGE", 0.0) < 90.0 or not entry.get("Manager Referral"):
                            entry[level] = "NOT QUALIFIED"
                            st.warning(f"{level} requires 10 completed courses, 90% average, and Manager Referral.")

                updated_df = pd.concat([df_main, pd.DataFrame([entry])], ignore_index=True)
                updated_df.to_csv(CSV_FILE, index=False)
                st.success(f"✅ Assessment Saved for Trainer ID: {trainer_id}")

                # Add download options for submitted assessment
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
                        pdf.drawString(100, y, f"Generated on: {datetime.now().strftime('%d-%m-%Y %I:%M %p IST')}")
                        y -= 20
                        pdf.drawString(100, y, f"Trainer: {trainer_name} (ID: {trainer_id})")
                        y -= 20
                        pdf.drawString(100, y, f"Evaluator: {evaluator_username} ({evaluator_role})")
                        y -= 30
                        pdf.drawString(100, y, "Assessment Summary")
                        y -= 20
                        pdf.drawString(100, y, f"Date of Assessment: {entry['Date of assessment']}")
                        y -= 20
                        pdf.drawString(100, y, f"LEVEL #1 TOTAL: {entry.get('LEVEL #1 TOTAL', 'N/A')}")
                        y -= 20
                        pdf.drawString(100, y, f"LEVEL #1 AVERAGE: {entry.get('LEVEL #1 AVERAGE', 'N/A')}")
                        y -= 20
                        pdf.drawString(100, y, f"LEVEL #1 STATUS: {entry.get('LEVEL #1 STATUS', 'N/A')}")
                        y -= 20
                        pdf.drawString(100, y, f"LEVEL #2 TOTAL: {entry.get('LEVEL #2 TOTAL', 'N/A')}")
                        y -= 20
                        pdf.drawString(100, y, f"LEVEL #2 AVERAGE: {entry.get('LEVEL #2 AVERAGE', 'N/A')}")
                        y -= 20
                        pdf.drawString(100, y, f"LEVEL #2 STATUS: {entry.get('LEVEL #2 STATUS', 'N/A')}")
                        y -= 20
                        pdf.drawString(100, y, f"LEVEL #3 TOTAL: {entry.get('LEVEL #3 TOTAL', 'N/A')}")
                        y -= 20
                        pdf.drawString(100, y, f"LEVEL #3 AVERAGE: {entry.get('LEVEL #3 AVERAGE', 'N/A')}")
                        y -= 20
                        pdf.drawString(100, y, f"LEVEL #3 STATUS: {entry.get('LEVEL #3 STATUS', 'N/A')}")
                        y -= 20
                        pdf.drawString(100, y, f"Manager Referral: {entry.get('Manager Referral', 'N/A')}")
                        y -= 30
                        for level in ["LEVEL #1", "LEVEL #2", "LEVEL #3"]:
                            pdf.drawString(100, y, f"{level} Courses")
                            y -= 20
                            for i in range(1, 11):
                                course = entry.get(f"{level} Course :{i}", "N/A")
                                pdf.drawString(100, y, f"Course :{i}: {course}")
                                y -= 20
                                for param in relevant_params[evaluator_role]:
                                    param_value = entry.get(f"{param} Course :{i}", "N/A")
                                    pdf.drawString(100, y, f"  {param}: {param_value}")
                                    y -= 20
                                pdf.drawString(100, y, f"  TOTAL: {entry.get(f'{level} Course :{i} TOTAL', 'N/A')}")
                                y -= 20
                                pdf.drawString(100, y, f"  AVERAGE: {entry.get(f'{level} Course :{i} AVERAGE', 'N/A')}")
                                y -= 20
                                pdf.drawString(100, y, f"  STATUS: {entry.get(f'{level} Course :{i} STATUS', 'N/A')}")
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
        st.subheader("📊 Viewer Dashboard")

        if "logged_in" not in st.session_state or not st.session_state.get("logged_in"):
            st.warning("Please login to access the viewer dashboard.")
            return

        st.markdown("### 🔍 Filter Assessments")
        branch = st.selectbox("Select Branch", options=["", "Lokhandwala", "Juhu", "Laxmi", "Malad", "Pune", "Bangalore", "Nagpur"], key="viewer_branch")
        department = st.selectbox("Select Department", options=["", "Coding", "Mechanical", "Design Thinking", "Electronics", "AI & Analytics"], key="viewer_department")
        search_term = st.text_input("Search by Trainer Name or ID", key="viewer_search", help="Enter a name or ID to filter trainers.")

        if os.path.exists(DEFAULT_DATA_FILE):
            try:
                eval_inputs_df = pd.read_csv(DEFAULT_DATA_FILE).fillna("")
                if "Trainer ID" not in eval_inputs_df.columns or "Trainer Name" not in eval_inputs_df.columns or "Branch" not in eval_inputs_df.columns or "Department" not in eval_inputs_df.columns:
                    st.error("❌ Required columns missing in EVALUATOR_INPUT.csv.")
                    return
                filtered_trainers = eval_inputs_df.copy()
                if branch:
                    filtered_trainers = filtered_trainers[filtered_trainers["Branch"] == branch]
                if department:
                    filtered_trainers = filtered_trainers[filtered_trainers["Department"] == department]
                if search_term:
                    filtered_trainers = filtered_trainers[
                        filtered_trainers["Trainer Name"].str.contains(search_term, case=False, na=False) |
                        filtered_trainers["Trainer ID"].str.contains(search_term, case=False, na=False)
                    ]
                if filtered_trainers.empty:
                    st.warning("No trainers match the selected filters.")
                    trainer_name = ""
                else:
                    trainer_name = st.selectbox("Select Trainer Name", options=[""] + sorted(filtered_trainers["Trainer Name"].unique().tolist()), key="viewer_trainer")
            except Exception as e:
                logger.error(f"Error filtering trainers: {str(e)}")
                st.error("Failed to load trainer data.")
                return
        else:
            st.error("EVALUATOR_INPUT.csv not found.")
            return

        df = df_main.copy()
        if trainer_name and os.path.exists(CSV_FILE):
            try:
                trainer_id = eval_inputs_df[eval_inputs_df["Trainer Name"] == trainer_name]["Trainer ID"].iloc[0]
                trainer_report = df[df["Trainer ID"] == trainer_id]
                if not trainer_report.empty:
                    st.markdown("### 📋 Assessment Records")
                    st.dataframe(trainer_report, use_container_width=True)
                    st.markdown(f"**Trainer ID:** {trainer_id} | **Name:** {trainer_name} | **Department:** {department or 'N/A'} | **Branch:** {branch or 'N/A'}")
                else:
                    st.warning("No assessment records found for the selected trainer.")
            except Exception as e:
                logger.error(f"Error loading trainer report: {str(e)}")
                st.error("Failed to load assessment records.")

        if trainer_name and not trainer_report.empty:
            col1, col2 = st.columns(2)
            with col1:
                csv_data = trainer_report.to_csv(index=False)
                st.download_button(
                    label="Download Trainer CSV",
                    data=csv_data,
                    file_name=f"trainer_{trainer_id}_assessment.csv",
                    mime="text/csv",
                    key=f"download_button_csv_{trainer_id}"
                )
            with col2:
                try:
                    buffer = BytesIO()
                    pdf = canvas.Canvas(buffer, pagesize=A4)
                    pdf.setFont("Helvetica", 12)
                    y = 750
                    pdf.drawString(100, y, f"Trainer Assessment Report")
                    y -= 20
                    pdf.drawString(100, y, f"Generated on: {datetime.now().strftime('%d-%m-%Y %I:%M %p IST')}")
                    y -= 20
                    pdf.drawString(100, y, f"Trainer: {trainer_name} (ID: {trainer_id})")
                    y -= 30
                    pdf.drawString(100, y, "Assessment Records")
                    y -= 20
                    for _, row in trainer_report.iterrows():
                        pdf.drawString(100, y, f"Date of Assessment: {row['Date of assessment']}")
                        y -= 20
                        pdf.drawString(100, y, f"LEVEL #1 TOTAL: {row['LEVEL #1 TOTAL']}")
                        y -= 20
                        pdf.drawString(100, y, f"LEVEL #1 AVERAGE: {row['LEVEL #1 AVERAGE']}")
                        y -= 20
                        pdf.drawString(100, y, f"LEVEL #1 STATUS: {row['LEVEL #1 STATUS']}")
                        y -= 20
                        pdf.drawString(100, y, f"LEVEL #2 TOTAL: {row['LEVEL #2 TOTAL']}")
                        y -= 20
                        pdf.drawString(100, y, f"LEVEL #2 AVERAGE: {row['LEVEL #2 AVERAGE']}")
                        y -= 20
                        pdf.drawString(100, y, f"LEVEL #2 STATUS: {row['LEVEL #2 STATUS']}")
                        y -= 20
                        pdf.drawString(100, y, f"LEVEL #3 TOTAL: {row['LEVEL #3 TOTAL']}")
                        y -= 20
                        pdf.drawString(100, y, f"LEVEL #3 AVERAGE: {row['LEVEL #3 AVERAGE']}")
                        y -= 20
                        pdf.drawString(100, y, f"LEVEL #3 STATUS: {row['LEVEL #3 STATUS']}")
                        y -= 20
                        pdf.drawString(100, y, f"Manager Referral: {row.get('Manager Referral', 'N/A')}")
                        y -= 30
                        if y < 50:
                            pdf.showPage()
                            pdf.setFont("Helvetica", 12)
                            y = 750
                    for level in ["LEVEL #1", "LEVEL #2", "LEVEL #3"]:
                        pdf.drawString(100, y, f"{level} Courses")
                        y -= 20
                        for i in range(1, 11):
                            course = trainer_report.iloc[-1].get(f"{level} Course :{i}", "N/A")
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
                        file_name=f"trainer_{trainer_id}_assessment.pdf",
                        mime="application/pdf",
                        key=f"download_button_pdf_{trainer_id}"
                    )
                except Exception as e:
                    logger.error(f"Error generating PDF: {str(e)}")
                    st.error("Failed to generate PDF report.")

        if st.button("View All Trainers", key="view_all_trainers"):
            try:
                if os.path.exists(DEFAULT_DATA_FILE):
                    all_trainers = eval_inputs_df[["Trainer ID", "Trainer Name", "Department", "Branch"]].drop_duplicates()
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

        # Display list of existing evaluators at the top
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
                full_name = st.text_input("Full Name", key="new_eval_name")
                email = st.text_input("Email", key="new_eval_email")
                role_select = st.selectbox("Role", ["Evaluator", "Viewer", "Super Administrator"], key="new_eval_role")
                submitted = st.form_submit_button("Add Evaluator")
                if submitted:
                    try:
                        if not new_username or not new_password:
                            st.error("Username and password are required.")
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
                        if change_password:
                            new_pass = st.text_input("New Password", type="password", key=f"newpass_{selected_eval}")
                        edit_submitted = st.form_submit_button("Save Changes")
                        if edit_submitted:
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

            col1, col2 = st.columns([3, 1])
            with col1:
                trainer_filter = st.text_input("Filter by Trainer Name or ID", "")
            with col2:
                display_trainers = st.button("Display Matching Trainers")
            
            filtered = df_main.copy()
            if trainer_filter:
                try:
                    mask = filtered["Trainer ID"].astype(str).str.contains(trainer_filter, case=False, na=False) | \
                           filtered["Trainer Name"].astype(str).str.contains(trainer_filter, case=False, na=False)
                    filtered = filtered[mask]
                except Exception as e:
                    logger.error(f"Error filtering trainers: {str(e)}")
                    st.error("Failed to apply trainer filter.")

            if display_trainers and not filtered.empty:
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
        st.warning("Failed to set background image.")

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