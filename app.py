# =========================================================
# DEEP HEART PRO - FINAL APP.PY
# =========================================================

import streamlit as st
import database_helper as db
import auth
import model_handler as mh
import pandas as pd
from datetime import datetime
import pytz
import matplotlib.pyplot as plt
import seaborn as sns

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Deep Heart Pro",
    page_icon="🫀",
    layout="wide"
)

# =========================================================
# CONSTANTS
# =========================================================

LOW_RISK_THRESHOLD = 0.30
MODERATE_RISK_THRESHOLD = 0.45
HIGH_RISK_THRESHOLD = 0.75

GENDER_MAP = {"Male": 1, "Female": 0}

CP_MAP = {
    "Typical Angina": 0,
    "Atypical Angina": 1,
    "Non-Anginal Pain": 2,
    "Asymptomatic": 3
}

RESTECG_MAP = {
    "Normal": 0,
    "ST-T Wave Abnormality": 1,
    "Left Ventricular Hypertrophy": 2
}

SLOPE_MAP = {
    "Up": 0,
    "Flat": 1,
    "Down": 2
}

THAL_MAP = {
    "Normal": 1,
    "Fixed Defect": 2,
    "Reversible Defect": 3
}

REV_GENDER_MAP = {v: k for k, v in GENDER_MAP.items()}
REV_CP_MAP = {v: k for k, v in CP_MAP.items()}
REV_RESTECG_MAP = {v: k for k, v in RESTECG_MAP.items()}
REV_SLOPE_MAP = {v: k for k, v in SLOPE_MAP.items()}
REV_THAL_MAP = {v: k for k, v in THAL_MAP.items()}

# =========================================================
# DATABASE INIT
# =========================================================

@st.cache_resource
def initialize_database():
    return db.DatabaseManager()

db_manager = initialize_database()
db_manager.init_db()

# =========================================================
# APPLICATION CLASS
# =========================================================

class StreamlitApp:
    def __init__(self, db_manager_instance, model_predictor_instance):
        self.db_manager = db_manager_instance
        self.predictor = model_predictor_instance
        self.auth_service = auth.AuthenticationService(self.db_manager)
        self._initialize_session_state()

    def _initialize_session_state(self):
        if "logged_in" not in st.session_state:
            st.session_state.logged_in = False
        if "auth_mode" not in st.session_state:
            st.session_state.auth_mode = "login"
        if "editing_patient_id" not in st.session_state:
            st.session_state.editing_patient_id = None
        if "editing_record_id" not in st.session_state:
            st.session_state.editing_record_id = None

    def _calculate_risk_status(self, prob):
        if prob < LOW_RISK_THRESHOLD:
            return "🟢 Low Risk"
        elif prob < MODERATE_RISK_THRESHOLD:
            return "🟡 Moderate Risk"
        elif prob < HIGH_RISK_THRESHOLD:
            return "🟠 High Risk"
        return "🔴 Critical Risk"

    def _validate_contact_number(self, contact):
        if not contact.strip():
            return False, "Contact number required."
        if not contact.startswith('92'):
            return False, "Contact number must start with '92'."
        if not contact.isdigit():
            return False, "Contact number must contain only digits."
        if len(contact) != 12:
            return False, "Contact number must be exactly 12 digits long (e.g., 923XXXXXXXXX)."
        return True, "Success"

    def _validate_patient(self, name, contact):
        if not name.strip():
            return False, "Patient name required"
        return self._validate_contact_number(contact)

    def run(self):
        if not st.session_state.logged_in:
            if st.session_state.auth_mode == "login":
                self.auth_service.login_page()
            elif st.session_state.auth_mode == "signup":
                self.auth_service.signup_page()
            elif st.session_state.auth_mode == "forgot":
                self.auth_service.forgot_password_page()
        else:
            self._render_main_app()

    def _render_main_app(self):
        self._render_sidebar()

        menu = st.session_state.get("menu", "Dashboard")

        if menu == "Logout":
            st.session_state.logged_in = False
            st.session_state.auth_mode = "login"
            st.rerun()
        elif menu == "Dashboard":
            self._render_dashboard()
        elif menu == "Patients":
            self._render_patients()
        elif menu == "Add Patient":
            self._render_add_patient()
        elif menu == "Medical Records":
            self._render_medical_records()
        elif menu == "Profile":
            self._render_profile()
        elif menu == "Risk Trends":
            self._render_risk_trends()

    def _render_sidebar(self):
        st.sidebar.title(f"👨‍⚕️ Dr. {st.session_state.user_name}")
        menu_selection = st.sidebar.radio(
            "Navigation",
            [
                "Dashboard",
                "Patients",
                "Add Patient",
                "Medical Records",
                "Risk Trends",
                "Profile",
                "Logout"
            ]
        )
        st.session_state.menu = menu_selection

    def _render_dashboard(self):
        st.title("📈 Clinical Dashboard")
        patients_df = self.db_manager.get_patients(st.session_state.user_id)
        total_patients = len(patients_df)
        all_probs = []

        if not patients_df.empty:
            for _, patient in patients_df.iterrows():
                recs = self.db_manager.get_records(patient["id"])
                if not recs.empty:
                    all_probs.append(recs.iloc[0]["Probability"])

        high_risk = len([x for x in all_probs if x >= MODERATE_RISK_THRESHOLD])
        critical_risk = len([x for x in all_probs if x >= HIGH_RISK_THRESHOLD])
        avg_risk = (round(sum(all_probs) / len(all_probs) * 100, 1) if all_probs else 0)

        pak_tz = pytz.timezone("Asia/Karachi")
        pkt_now = datetime.now(pak_tz).strftime("%I:%M %p")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Patients", total_patients)
        c2.metric("High Risk", high_risk)
        c3.metric("Critical Cases", critical_risk)
        c4.metric("Average Risk", f"{avg_risk}%")

        st.write("---")
        st.subheader("📊 Risk Distribution")

        if all_probs:
            risk_df = pd.DataFrame({
                "Risk Probability": [x * 100 for x in all_probs]
            })
            st.bar_chart(risk_df)
        st.caption(f"Last Updated (PKT): {pkt_now}")

    def _render_patients(self):
        st.title("🧑 Patients List")
        patients_df = self.db_manager.get_patients(st.session_state.user_id)
        patient_data = []

        for _, patient in patients_df.iterrows():
            records = self.db_manager.get_records(patient["id"])
            if not records.empty:
                latest = records.iloc[0]
                prob = latest["Probability"]
                patient_data.append({
                    "ID": patient["id"],
                    "Name": patient["name"],
                    "Age": patient["age"],
                    "Contact": patient["contact_no"],
                    "Probability": f"{prob * 100:.1f}%",
                    "Status": self._calculate_risk_status(prob),
                    "Last Visit": latest["visit_date"]
                })
            else:
                patient_data.append({
                    "ID": patient["id"],
                    "Name": patient["name"],
                    "Age": patient["age"],
                    "Contact": patient["contact_no"],
                    "Probability": "N/A",
                    "Status": "⚪ No Data",
                    "Last Visit": "No History"
                })

        df = pd.DataFrame(patient_data)
        search = st.text_input("🔍 Search Patients")

        if search:
            df = df[
                df["Name"].str.contains(search, case=False, na=False) |
                df["Contact"].str.contains(search, case=False, na=False)
            ]

        st.dataframe(df, use_container_width=True, hide_index=True)
        st.write("---")

        if not df.empty:
            patient_ids = df["ID"].tolist()
            selected_patient = st.selectbox(
                "Select Patient",
                patient_ids,
                format_func=lambda x: f"{df[df['ID']==x]['Name'].iloc[0]} (ID: {x})"
            )

            c1, c2 = st.columns(2)
            with c1:
                if st.button("✏ Edit Patient"):
                    st.session_state.editing_patient_id = selected_patient

            with c2:
                if st.button("🗑 Delete Patient"):
                    self.db_manager.delete_patient(selected_patient)
                    st.success("Patient deleted successfully")
                    st.rerun()

        if st.session_state.editing_patient_id is not None:
            patient_df = self.db_manager.get_patients(
                st.session_state.user_id,
                st.session_state.editing_patient_id
            )
            if not patient_df.empty:
                patient = patient_df.iloc[0]
                with st.expander(f"Edit Patient: {patient['name']}", expanded=True):
                    with st.form("edit_patient_form"):
                        edit_name = st.text_input("Patient Name", value=patient["name"])
                        edit_contact = st.text_input("Contact", value=patient["contact_no"])
                        edit_age = st.number_input("Age", min_value=1, max_value=120, value=int(patient["age"]))

                        col1, col2 = st.columns(2)
                        with col1:
                            if st.form_submit_button("Update"):
                                valid, msg = self._validate_patient(edit_name, edit_contact)
                                if not valid:
                                    st.error(msg)
                                else:
                                    self.db_manager.update_patient(
                                        st.session_state.editing_patient_id,
                                        edit_name,
                                        edit_contact,
                                        edit_age
                                    )
                                    st.success("Patient updated")
                                    st.session_state.editing_patient_id = None
                                    st.rerun()
                        with col2:
                            if st.form_submit_button("Cancel"):
                                st.session_state.editing_patient_id = None
                                st.rerun()

    def _render_add_patient(self):
        st.title("🩺 Cardiac Risk Analysis")
        existing_patients = self.db_manager.get_patients(st.session_state.user_id)
        options = ["-- Register New Patient --"]

        if not existing_patients.empty:
            options += (existing_patients["name"] + " | " + existing_patients["contact_no"]).tolist()

        selection = st.selectbox("Select Patient", options)

        with st.form("patient_form"):
            st.subheader("Patient Information")

            is_new = False
            p_id = None

            if selection == "-- Register New Patient --":
                c1, c2, c3 = st.columns(3)
                p_name = c1.text_input("Full Name")
                p_age = c2.number_input("Age", min_value=1, max_value=120, value=30)
                p_contact = c3.text_input("Contact No")
                is_new = True
            else:
                selected_contact = selection.split(" | ")[-1]
                p_info = existing_patients[existing_patients["contact_no"] == selected_contact].iloc[0]

                # =========================================================
                # FIX: convert numpy/pandas types → Python native types
                # =========================================================
                p_info = p_info.copy()

                p_id = int(p_info["id"])
                p_name = str(p_info["name"])
                p_age = int(p_info["age"])
                p_contact = str(p_info["contact_no"])

                st.info(f"{p_name} | Age: {p_age}")

            st.write("---")
            st.subheader("Clinical Metrics")

            col1, col2 = st.columns(2)
            with col1:
                gender = st.selectbox("Gender", list(GENDER_MAP.keys()))
                chest_pain = st.selectbox("Chest Pain Type", list(CP_MAP.keys()))
                rbp = st.number_input("Resting Blood Pressure", min_value=50, max_value=300, value=120)
                chol = st.number_input("Cholesterol", min_value=50, max_value=700, value=200)
                fbs = st.selectbox("Fasting Blood Sugar > 120", [0, 1])
                restecg = st.selectbox("Rest ECG", list(RESTECG_MAP.keys()))
            with col2:
                mhr = st.number_input("Max Heart Rate", min_value=30, max_value=250, value=150)
                eia = st.selectbox("Exercise Induced Angina", [0, 1])
                st_dep = st.number_input("ST Depression", value=0.0)
                slope = st.selectbox("ST Slope", list(SLOPE_MAP.keys()))
                vessels = st.number_input("Major Vessels", min_value=0, max_value=4, value=0)
                thal = st.selectbox("Thalassemia", list(THAL_MAP.keys()))

            submitted = st.form_submit_button("Run Analysis")

            if submitted:
                valid, msg = self._validate_patient(p_name, p_contact)
                if not valid:
                    st.error(msg)
                else:
                    input_data = {
                        "Age": int(p_age),
                        "Gender": int(GENDER_MAP[gender]),
                        "ChestPainType": int(CP_MAP[chest_pain]),
                        "RestingBloodPressure": int(rbp),
                        "Cholesterol": int(chol),
                        "FastingBloodSugar": int(fbs),
                        "RestECG": int(RESTECG_MAP[restecg]),
                        "MaxHeartRate": int(mhr),
                        "ExerciseInducedAngina": int(eia),
                        "ST_Depression": float(st_dep),
                        "ST_Slope": int(SLOPE_MAP[slope]),
                        "MajorVessels": int(vessels),
                        "Thalassemia": int(THAL_MAP[thal])
                    }

                    with st.spinner("Analyzing cardiac risk..."):
                        try:
                            target, prob, category, status = self.predictor.predict_heart_risk(input_data)

                            if status == "Success":
                                if is_new:
                                    existing = existing_patients[existing_patients["contact_no"] == p_contact]
                                    if existing.empty:
                                        p_id = self.db_manager.create_patient(
                                            st.session_state.user_id,
                                            p_name,
                                            p_contact,
                                            p_age
                                        )
                                    else:
                                        p_id = existing.iloc[0]["id"]

                                self.db_manager.create_medical_record(p_id, input_data, target, prob)

                                latest_record = self.db_manager.get_records(p_id)
                                st.success("Medical record saved successfully ✔")
                                st.write("🔎 Latest DB Record:")
                                st.dataframe(latest_record.head(1))

                                st.success(
                                    f"""
                                    Analysis Complete

                                    Risk Category: {category}
                                    Probability: {prob * 100:.1f}%
                                    """
                                )
                                st.progress(min(prob, 1.0))
                            else:
                                st.error(status)
                        except Exception as e:
                            st.error(f"Prediction Error: {e}")

    def _render_medical_records(self):
        st.title("📋 Medical Records")
        all_records = []
        patients_df = self.db_manager.get_patients(st.session_state.user_id)

        for _, patient in patients_df.iterrows():
            recs = self.db_manager.get_records(patient["id"])
            if not recs.empty:
                recs = recs.copy()
                recs["Patient"] = patient["name"]
                recs["Contact"] = patient["contact_no"]
                recs["Gender"] = recs["Gender"].map(REV_GENDER_MAP)
                recs["ChestPainType"] = recs["ChestPainType"].map(REV_CP_MAP)
                recs["RestECG"] = recs["RestECG"].map(REV_RESTECG_MAP)
                recs["ST_Slope"] = recs["ST_Slope"].map(REV_SLOPE_MAP)
                recs["Thalassemia"] = recs["Thalassemia"].map(REV_THAL_MAP)
                recs["Probability"] = recs["Probability"].apply(lambda x: f"{x * 100:.1f}%")
                all_records.append(recs)

        if all_records:
            final_df = pd.concat(all_records, ignore_index=True)
            final_df = final_df.sort_values(by="visit_date", ascending=False)
            st.dataframe(final_df, use_container_width=True, hide_index=True)
            st.write("---")

            record_ids = final_df["id"].tolist()
            selected_record = st.selectbox("Select Medical Record", record_ids, format_func=lambda x: f"Record #{x}")

            c1, c2 = st.columns(2)
            with c1:
                if st.button("✏ Edit Record"):
                    st.session_state.editing_record_id = selected_record

            with c2:
                if st.button("🗑 Delete Record"):
                    self.db_manager.delete_medical_record(selected_record)
                    st.success("Medical record deleted")
                    st.rerun()

            if st.session_state.editing_record_id is not None:
                original_record_df = None
                for _, patient in patients_df.iterrows():
                    temp_df = self.db_manager.get_records(patient["id"])
                    if not temp_df.empty:
                        match = temp_df[temp_df["id"] == st.session_state.editing_record_id]
                        if not match.empty:
                            original_record_df = match
                            break

                if original_record_df is not None:
                    rec = original_record_df.iloc[0]
                    with st.expander(f"Edit Record #{rec['id']}", expanded=True):
                        with st.form("edit_record_form"):
                            st.subheader("Clinical Metrics")

                            col1, col2 = st.columns(2)
                            with col1:
                                edit_age = st.number_input("Age", value=int(rec["Age"]), min_value=1, max_value=120)
                                edit_gender = st.selectbox("Gender", list(GENDER_MAP.keys()), index=int(rec["Gender"]))
                                edit_cp = st.selectbox("Chest Pain Type", list(CP_MAP.keys()), index=int(rec["ChestPainType"]))
                                edit_rbp = st.number_input("Resting Blood Pressure", min_value=50, max_value=300, value=int(rec["RestingBloodPressure"]))
                                edit_chol = st.number_input("Cholesterol", min_value=50, max_value=700, value=int(rec["Cholesterol"]))
                                edit_fbs = st.selectbox("Fasting Blood Sugar > 120", [0, 1], index=int(rec["FastingBloodSugar"]))
                                edit_restecg = st.selectbox("Rest ECG", list(RESTECG_MAP.keys()), index=int(rec["RestECG"]))

                            with col2:
                                edit_mhr = st.number_input("Max Heart Rate", min_value=30, max_value=250, value=int(rec["MaxHeartRate"]))
                                edit_eia = st.selectbox("Exercise Induced Angina", [0, 1], index=int(rec["ExerciseInducedAngina"]))
                                edit_st_dep = st.number_input("ST Depression", value=float(rec["ST_Depression"]))
                                edit_slope = st.selectbox("ST Slope", list(SLOPE_MAP.keys()), index=int(rec["ST_Slope"]))
                                edit_vessels = st.number_input("Major Vessels", min_value=0, max_value=4, value=int(rec["MajorVessels"]))
                                thal_index = max(int(rec["Thalassemia"]) - 1, 0)
                                edit_thal = st.selectbox("Thalassemia", list(THAL_MAP.keys()), index=thal_index)

                            c1, c2 = st.columns(2)
                            with c1:
                                if st.form_submit_button("Update Record"):
                                    updated_data = {
                                        "Age": edit_age,
                                        "Gender": GENDER_MAP[edit_gender],
                                        "ChestPainType": CP_MAP[edit_cp],
                                        "RestingBloodPressure": edit_rbp,
                                        "Cholesterol": edit_chol,
                                        "FastingBloodSugar": edit_fbs,
                                        "RestECG": RESTECG_MAP[edit_restecg],
                                        "MaxHeartRate": edit_mhr,
                                        "ExerciseInducedAngina": edit_eia,
                                        "ST_Depression": edit_st_dep,
                                        "ST_Slope": SLOPE_MAP[edit_slope],
                                        "MajorVessels": edit_vessels,
                                        "Thalassemia": THAL_MAP[edit_thal]
                                    }

                                    try:
                                        target, prob, cat, status = self.predictor.predict_heart_risk(updated_data)
                                        self.db_manager.update_medical_record(
                                            st.session_state.editing_record_id,
                                            updated_data,
                                            target,
                                            prob
                                        )
                                        st.success("Medical record updated successfully")
                                        st.session_state.editing_record_id = None
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Update Error: {e}")

                            with c2:
                                if st.form_submit_button("Cancel"):
                                    st.session_state.editing_record_id = None
                                    st.rerun()
        else:
            st.info("No medical records found.")

    def _render_profile(self):
        st.title("👨‍⚕️ Doctor Profile")
        doctor_df = self.db_manager.get_doctors(st.session_state.user_id)

        if not doctor_df.empty:
            doctor_info = doctor_df.iloc[0]
            with st.form("doctor_profile_form"):
                st.subheader("Personal Information")
                col1, col2 = st.columns(2)
                with col1:
                    edit_first_name = st.text_input("First Name", value=doctor_info["first_name"])
                    edit_contact = st.text_input("Contact No", value=doctor_info["contact_no"])
                with col2:
                    edit_last_name = st.text_input("Last Name", value=doctor_info["last_name"])
                    edit_qualification = st.text_input("Qualification (MBBS/MD)", value=doctor_info["qualification"])
                
                st.text_input("Email", value=doctor_info["email"], disabled=True)

                if st.form_submit_button("Update Profile"):
                    valid, msg = self._validate_contact_number(edit_contact)
                    if not valid:
                        st.error(msg)
                    else:
                        self.db_manager.update_doctor(
                            st.session_state.user_id,
                            edit_first_name,
                            edit_last_name,
                            edit_contact,
                            edit_qualification
                        )
                        st.success("Profile updated successfully!")
                        st.session_state.user_name = f"{edit_first_name} {edit_last_name}"
                        st.rerun()
        else:
            st.error("Doctor information not found.")

    def _render_risk_trends(self):
        st.title("📈 Health Risk Trends")
        all_records = []
        patients_df = self.db_manager.get_patients(st.session_state.user_id)

        for _, patient in patients_df.iterrows():
            recs = self.db_manager.get_records(patient["id"])
            if not recs.empty:
                recs = recs.copy()
                recs["Patient"] = patient["name"]
                recs["Contact"] = patient["contact_no"]
                all_records.append(recs)

        if not all_records:
            st.info("No medical records available to analyze trends.")
            return

        df_trends = pd.concat(all_records, ignore_index=True)
        df_trends['visit_date'] = pd.to_datetime(df_trends['visit_date'])
        df_trends['Risk Category'] = df_trends['Probability'].apply(self._calculate_risk_status)

        st.subheader("Risk Category Distribution")
        risk_counts = df_trends['Risk Category'].value_counts().reset_index()
        risk_counts.columns = ['Risk Category', 'Count']
        fig_pie, ax_pie = plt.subplots()
        ax_pie.pie(risk_counts['Count'], labels=risk_counts['Risk Category'], autopct='%1.1f%%', startangle=90, wedgeprops={'edgecolor': 'black'})
        ax_pie.axis('equal') # Equal aspect ratio ensures that pie is drawn as a circle.
        st.pyplot(fig_pie)

        st.subheader("Average Risk Probability Over Time")
        # Group by date and calculate average probability
        daily_avg_risk = df_trends.groupby(df_trends['visit_date'].dt.date)['Probability'].mean().reset_index()
        daily_avg_risk.columns = ['Date', 'Average Probability']
        
        if not daily_avg_risk.empty:
            fig_line, ax_line = plt.subplots(figsize=(10, 5))
            sns.lineplot(x='Date', y='Average Probability', data=daily_avg_risk, marker='o', ax=ax_line)
            ax_line.set_title('Average Heart Disease Risk Over Time')
            ax_line.set_xlabel('Date')
            ax_line.set_ylabel('Average Probability')
            ax_line.tick_params(axis='x', rotation=45)
            st.pyplot(fig_line)
        else:
            st.info("No sufficient data to show average risk over time.")

        st.subheader("Risk Distribution by Age Group")
        # Define age groups
        bins = [0, 18, 30, 45, 60, 75, 100]
        labels = ['<18', '18-29', '30-44', '45-59', '60-74', '75+']
        df_trends['Age Group'] = pd.cut(df_trends['Age'], bins=bins, labels=labels, right=False)
        
        age_risk = df_trends.groupby('Age Group')['Probability'].mean().reset_index()
        if not age_risk.empty: 
            fig_bar, ax_bar = plt.subplots(figsize=(10, 5))
            sns.barplot(x='Age Group', y='Probability', data=age_risk, palette='viridis', ax=ax_bar)
            ax_bar.set_title('Average Heart Disease Risk by Age Group')
            ax_bar.set_xlabel('Age Group')
            ax_bar.set_ylabel('Average Probability')
            st.pyplot(fig_bar)
        else:
            st.info("No sufficient data to show risk distribution by age group.")


if __name__ == "__main__":
    predictor_instance = mh.HeartRiskPredictor()
    app = StreamlitApp(db_manager, predictor_instance)
    app.run()
