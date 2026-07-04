import sqlite3
import pandas as pd
import random
from datetime import datetime, timedelta


class DatabaseManager:

    DB_NAME = "heart_disease.db"

    def __init__(self):
        pass

    def _get_connection(self):
        """Returns SQLite database connection."""
        return sqlite3.connect(self.DB_NAME)

    # ==========================================
    # DATABASE INITIALIZATION
    # ==========================================

    def init_db(self):

        try:

            with self._get_connection() as conn:

                cursor = conn.cursor()

                # DOCTORS TABLE
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS doctors (

                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        first_name TEXT,
                        last_name TEXT,
                        email TEXT UNIQUE,
                        contact_no TEXT,
                        password TEXT,
                        qualification TEXT,
                        dob DATE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

                    )
                ''')

                # PATIENTS TABLE
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS patients (

                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        doc_id INTEGER,
                        name TEXT,
                        contact_no TEXT,
                        age INTEGER,

                        FOREIGN KEY(doc_id)
                        REFERENCES doctors(id)

                    )
                ''')

                # RECORDS TABLE
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS records (

                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        patient_id INTEGER,

                        Age INTEGER,
                        Gender INTEGER,
                        ChestPainType INTEGER,
                        RestingBloodPressure INTEGER,
                        Cholesterol INTEGER,
                        FastingBloodSugar INTEGER,
                        RestECG INTEGER,
                        MaxHeartRate INTEGER,
                        ExerciseInducedAngina INTEGER,
                        ST_Depression REAL,
                        ST_Slope INTEGER,
                        MajorVessels INTEGER,
                        Thalassemia INTEGER,

                        Target INTEGER,
                        Probability REAL,

                        visit_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                        FOREIGN KEY(patient_id)
                        REFERENCES patients(id)

                    )
                ''')

                conn.commit()

        except Exception as e:
            print(f"Error during initialization: {e}")

    # ==========================================
    # AUTHENTICATION
    # ==========================================

    def verify_login(self, email, password):

        with self._get_connection() as conn:

            cursor = conn.cursor()

            cursor.execute(
                "SELECT id, first_name, last_name FROM doctors WHERE email=? AND password=?",
                (email, password)
            )

            return cursor.fetchone()

    # ==========================================
    # DOCTOR CRUD
    # ==========================================

    def create_doctor(self, f_name, l_name, email, contact, pwd, qual, dob):

        try:

            with self._get_connection() as conn:

                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO doctors (
                        first_name,
                        last_name,
                        email,
                        contact_no,
                        password,
                        qualification,
                        dob
                    )

                    VALUES (?, ?, ?, ?, ?, ?, ?)

                """, (

                    f_name,
                    l_name,
                    email,
                    contact,
                    pwd,
                    qual,
                    str(dob)

                ))

                conn.commit()

                return True

        except Exception as e:

            print(f"Error creating doctor: {e}")

            return False

    def get_doctors(self, doc_ids=None):

        with self._get_connection() as conn:

            if doc_ids is None:

                return pd.read_sql(
                    "SELECT * FROM doctors",
                    conn
                )

            ids = [doc_ids] if isinstance(doc_ids, int) else doc_ids

            placeholders = ",".join(["?"] * len(ids))

            query = f"""
                SELECT *
                FROM doctors
                WHERE id IN ({placeholders})
            """

            return pd.read_sql(
                query,
                conn,
                params=ids
            )

    def update_doctor(self, doc_id, f_name, l_name, contact, qual):

        with self._get_connection() as conn:

            cursor = conn.cursor()

            cursor.execute("""
                UPDATE doctors

                SET
                    first_name=?,
                    last_name=?,
                    contact_no=?,
                    qualification=?

                WHERE id=?

            """, (

                f_name,
                l_name,
                contact,
                qual,
                doc_id

            ))

            conn.commit()

    def delete_doctor(self, doc_id):

        with self._get_connection() as conn:

            cursor = conn.cursor()

            cursor.execute(
                "DELETE FROM doctors WHERE id=?",
                (doc_id,)
            )

            conn.commit()

    # ==========================================
    # PATIENT CRUD
    # ==========================================

    def create_patient(self, doc_id, name, contact, age):

        with self._get_connection() as conn:

            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO patients (
                    doc_id,
                    name,
                    contact_no,
                    age
                )

                VALUES (?, ?, ?, ?)

            """, (

                doc_id,
                name,
                contact,
                age

            ))

            conn.commit()

            return cursor.lastrowid

    def get_patients(self, doc_id, patient_ids=None):

        with self._get_connection() as conn:

            if patient_ids is None:

                query = """
                    SELECT *
                    FROM patients
                    WHERE doc_id=?
                """

                return pd.read_sql(
                    query,
                    conn,
                    params=(doc_id,)
                )

            ids = [patient_ids] if isinstance(patient_ids, int) else patient_ids

            placeholders = ",".join(["?"] * len(ids))

            query = f"""
                SELECT *
                FROM patients
                WHERE doc_id=?
                AND id IN ({placeholders})
            """

            return pd.read_sql(
                query,
                conn,
                params=[doc_id] + ids
            )

    def update_patient(self, p_id, name, contact, age):

        with self._get_connection() as conn:

            cursor = conn.cursor()

            cursor.execute("""
                UPDATE patients

                SET
                    name=?,
                    contact_no=?,
                    age=?

                WHERE id=?

            """, (

                name,
                contact,
                age,
                p_id

            ))

            conn.commit()

    def delete_patient(self, p_id):

        with self._get_connection() as conn:

            cursor = conn.cursor()

            cursor.execute(
                "DELETE FROM records WHERE patient_id=?",
                (p_id,)
            )

            cursor.execute(
                "DELETE FROM patients WHERE id=?",
                (p_id,)
            )

            conn.commit()

    # ==========================================
    # MEDICAL RECORD CRUD
    # ==========================================

    def create_medical_record(self, patient_id, data_dict, target, prob):

        with self._get_connection() as conn:

            cursor = conn.cursor()

            vals = list(data_dict.values())

            query = """
                INSERT INTO records (

                    patient_id,
                    Age,
                    Gender,
                    ChestPainType,
                    RestingBloodPressure,
                    Cholesterol,
                    FastingBloodSugar,
                    RestECG,
                    MaxHeartRate,
                    ExerciseInducedAngina,
                    ST_Depression,
                    ST_Slope,
                    MajorVessels,
                    Thalassemia,
                    Target,
                    Probability

                )

                VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?
                )
            """

            cursor.execute(
                query,
                [patient_id] + vals + [target, prob]
            )

            conn.commit()

    def get_records(self, patient_id, record_ids=None):

        with self._get_connection() as conn:

            if record_ids is None:

                query = """
                    SELECT *
                    FROM records

                    WHERE patient_id=?

                    ORDER BY visit_date DESC
                """

                return pd.read_sql(
                    query,
                    conn,
                    params=(patient_id,)
                )

            ids = [record_ids] if isinstance(record_ids, int) else record_ids

            placeholders = ",".join(["?"] * len(ids))

            query = f"""
                SELECT *
                FROM records

                WHERE patient_id=?
                AND id IN ({placeholders})

                ORDER BY visit_date DESC
            """

            return pd.read_sql(
                query,
                conn,
                params=[patient_id] + ids
            )

    def update_medical_record(self, record_id, data_dict, target, prob):

        with self._get_connection() as conn:

            cursor = conn.cursor()

            vals = list(data_dict.values())

            query = """
                UPDATE records

                SET

                    Age=?,
                    Gender=?,
                    ChestPainType=?,
                    RestingBloodPressure=?,
                    Cholesterol=?,
                    FastingBloodSugar=?,
                    RestECG=?,
                    MaxHeartRate=?,
                    ExerciseInducedAngina=?,
                    ST_Depression=?,
                    ST_Slope=?,
                    MajorVessels=?,
                    Thalassemia=?,
                    Target=?,
                    Probability=?,
                    visit_date=CURRENT_TIMESTAMP

                WHERE id=?
            """

            cursor.execute(
                query,
                vals + [target, prob, record_id]
            )

            conn.commit()

    def delete_medical_record(self, record_id):

        with self._get_connection() as conn:

            cursor = conn.cursor()

            cursor.execute(
                "DELETE FROM records WHERE id=?",
                (record_id,)
            )

            conn.commit()

    # ==========================================
    # SAMPLE DATA
    # ==========================================

    def insert_sample_data(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
    
            # Check if sample doctor already exists
            cursor.execute(
                "SELECT id FROM doctors WHERE email=?", ("umair@example.com",)
            )
            doctor = cursor.fetchone()
    
            if doctor:
                print("Sample data already exists.")
                return
    
            # ---------------------------------
            # Insert Sample Doctor
            # ---------------------------------
            cursor.execute(
                """
                INSERT INTO doctors 
                (first_name, last_name, email, contact_no, password, qualification, dob) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    "Umair",
                    "Hassan",
                    "umair@example.com",
                    "923198307451",
                    "123456",
                    "MS",
                    "2004-01-01",
                ),
            )
    
            doctor_id = cursor.lastrowid
    
            # ---------------------------------
            # Sample Patients (Formatted Contact Numbers)
            # ---------------------------------
            patients = [
                ("Ali Ahmed", "923001111111", 32),
                ("Sara Khan", "923002222222", 27),
                ("Bilal Hussain", "923003333333", 48),
                ("Ayesha Malik", "923004444444", 35),
                ("Usman Tariq", "923005555555", 58),
                ("Fatima Noor", "923006666666", 63),
                ("Hamza Iqbal", "923007777777", 41),
                ("Hina Shah", "923008888888", 67),
                ("Zain Ali", "923009999999", 55),
                ("Maryam Aslam", "923110000000", 45),
            ]
    
            for index, patient in enumerate(patients):
                cursor.execute(
                    """
                    INSERT INTO patients (doc_id, name, contact_no, age) 
                    VALUES (?, ?, ?, ?)
                """,
                    (doctor_id, patient[0], patient[1], patient[2]),
                )
    
                patient_id = cursor.lastrowid
                gender_map = {
                    "Ali Ahmed": 1,        # Male
                    "Sara Khan": 0,        # Female
                    "Bilal Hussain": 1,    # Male
                    "Ayesha Malik": 0,     # Female
                    "Usman Tariq": 1,      # Male
                    "Fatima Noor": 0,      # Female
                    "Hamza Iqbal": 1,      # Male
                    "Hina Shah": 0,        # Female
                    "Zain Ali": 1,         # Male
                    "Maryam Aslam": 0      # Female
                }

                gender = gender_map[patient[0]]
                # Fix 1: Establish a static gender and age per patient context
                #gender = random.randint(0, 1)
                age = patient[2]
    
                # Every patient gets 1-3 visits
                num_records = random.randint(1, 3)
    
                # Generate distinct dates going backwards from today
                base_date = datetime.now()
    
                for r in range(num_records):
                    # Fix 2: Create a unique date for each visit (spaced out by 30-90 days)
                    visit_date = (
                        base_date - timedelta(days=r * random.randint(30, 90))
                    ).strftime("%Y-%m-%d %H:%M:%S")
    
                    # ===============================
                    # LOW RISK PATIENTS
                    # ===============================
                    if index in [0, 1, 3]:
                        chest_pain = random.choice([0, 1])
                        bp = random.randint(110, 125)
                        chol = random.randint(150, 195)
                        sugar = 0
                        ecg = random.randint(0, 1)
                        heart_rate = random.randint(155, 180)
                        angina = 0
                        st_dep = round(random.uniform(0.0, 0.8), 1)
                        st_slope = 2
                        vessels = 0
                        thal = random.choice([2, 3])
                        target = 0
                        probability = round(random.uniform(0.05, 0.25), 2)
    
                    # ===============================
                    # MEDIUM RISK PATIENTS
                    # ===============================
                    elif index in [2, 4, 6, 9]:
                        chest_pain = random.choice([1, 2])
                        bp = random.randint(126, 145)
                        chol = random.randint(200, 245)
                        sugar = random.choice([0, 1])
                        ecg = random.randint(0, 2)
                        heart_rate = random.randint(130, 155)
                        angina = random.choice([0, 1])
                        st_dep = round(random.uniform(0.9, 2.0), 1)
                        st_slope = random.choice([1, 2])
                        vessels = random.randint(0, 1)
                        thal = random.choice([2, 3])
                        target = random.choice([0, 1])
                        probability = round(random.uniform(0.40, 0.70), 2)
    
                    # ===============================
                    # HIGH RISK PATIENTS
                    # ===============================
                    else:
                        chest_pain = 3
                        bp = random.randint(145, 185)
                        chol = random.randint(245, 340)
                        sugar = 1
                        ecg = random.randint(1, 2)
                        heart_rate = random.randint(85, 130)
                        angina = 1
                        st_dep = round(random.uniform(2.0, 5.0), 1)
                        st_slope = random.choice([0, 1])
                        vessels = random.randint(2, 3)
                        thal = random.choice([1, 3])
                        target = 1
                        probability = round(random.uniform(0.75, 0.99), 2)
    
                    # Note: Assumes your records schema has a 'visit_date' (or similar) field.
                    cursor.execute(
                        """
                        INSERT INTO records 
                        (
                            patient_id, Age, Gender, ChestPainType, RestingBloodPressure, 
                            Cholesterol, FastingBloodSugar, RestECG, MaxHeartRate, 
                            ExerciseInducedAngina, ST_Depression, ST_Slope, MajorVessels, 
                            Thalassemia, Target, Probability, visit_date
                        ) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            patient_id,
                            age,
                            gender,
                            chest_pain,
                            bp,
                            chol,
                            sugar,
                            ecg,
                            heart_rate,
                            angina,
                            st_dep,
                            st_slope,
                            vessels,
                            thal,
                            target,
                            probability,
                            visit_date,
                        ),
                    )
    
            conn.commit()
            print("Sample data inserted successfully.")
