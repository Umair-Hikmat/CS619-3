import sqlite3
import pandas as pd


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
