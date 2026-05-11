import mysql.connector
import pandas as pd
from mysql.connector import Error

class DatabaseManager:
    DB_CONFIG = {
        'host': 'sql12.freesqldatabase.com',
        'database': 'sql12826318',
        'user': 'sql12826318',
        'password': 'yX4b1LddIG', # Replace with the password from your email
        'port': 3306
    }

    def __init__(self):
        pass # DB_CONFIG is a class attribute, no instance-specific setup needed here

    def _get_connection(self):
        """Returns a connection object to the MySQL cloud database."""
        return mysql.connector.connect(**self.DB_CONFIG)

    def init_db(self):
        """Initializes the cloud database with MySQL schema."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # 1. DOCTORS TABLE
                cursor.execute('''CREATE TABLE IF NOT EXISTS doctors
                                 (id INT PRIMARY KEY AUTO_INCREMENT,
                                  first_name VARCHAR(100), last_name VARCHAR(100), email VARCHAR(100) UNIQUE,
                                  contact_no VARCHAR(20), password VARCHAR(255), qualification VARCHAR(100), dob DATE,
                                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

                # 2. PATIENTS TABLE
                cursor.execute('''CREATE TABLE IF NOT EXISTS patients
                                 (id INT PRIMARY KEY AUTO_INCREMENT,
                                  doc_id INT, name VARCHAR(100), contact_no VARCHAR(20), age INT,
                                  FOREIGN KEY(doc_id) REFERENCES doctors(id))''')

                # 3. MEDICAL RECORDS TABLE
                cursor.execute('''CREATE TABLE IF NOT EXISTS records
                                 (id INT PRIMARY KEY AUTO_INCREMENT, patient_id INT,
                                  Age INT, Gender INT, ChestPainType INT,
                                  RestingBloodPressure INT, Cholesterol INT,
                                  FastingBloodSugar INT, RestECG INT, MaxHeartRate INT,
                                  ExerciseInducedAngina INT, ST_Depression FLOAT,
                                  ST_Slope INT, MajorVessels INT, Thalassemia INT,
                                  Target INT, Probability FLOAT, visit_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                  FOREIGN KEY(patient_id) REFERENCES patients(id))''')
                conn.commit()
        except Error as e:
            print(f"Error during initialization: {e}")

    # ==========================================
    # --- AUTHENTICATION ---
    # ==========================================

    def verify_login(self, email, password):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, first_name, last_name FROM doctors WHERE email=%s AND password=%s", (email, password))
            return cursor.fetchone()

    # ==========================================
    # --- DOCTOR CRUD ---
    # ==========================================

    def create_doctor(self, f_name, l_name, email, contact, pwd, qual, dob):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""INSERT INTO doctors (first_name, last_name, email, contact_no, password, qualification, dob)
                               VALUES (%s,%s,%s,%s,%s,%s,%s)""", (f_name, l_name, email, contact, pwd, qual, str(dob)))
                conn.commit()
                return True
        except Error as e:
            print(f"Error creating doctor: {e}") # Print error for debugging
            return False

    def get_doctors(self, doc_ids=None):
        with self._get_connection() as conn:
            if doc_ids is None:
                return pd.read_sql("SELECT * FROM doctors", conn)
            ids = [doc_ids] if isinstance(doc_ids, int) else doc_ids
            id_tuple = str(tuple(ids)).replace(',)', ')')
            return pd.read_sql(f"SELECT * FROM doctors WHERE id IN {id_tuple}", conn)

    def update_doctor(self, doc_id, f_name, l_name, contact, qual):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE doctors SET first_name=%s, last_name=%s, contact_no=%s, qualification=%s WHERE id=%s",
                         (f_name, l_name, contact, qual, doc_id))
            conn.commit()

    def delete_doctor(self, doc_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM doctors WHERE id=%s", (doc_id,))
            conn.commit()

    # ==========================================
    # --- PATIENT CRUD ---
    # ==========================================

    def create_patient(self, doc_id, name, contact, age):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO patients (doc_id, name, contact_no, age) VALUES (%s,%s,%s,%s)",
                         (doc_id, name, contact, age))
            conn.commit()
            return cursor.lastrowid

    def get_patients(self, doc_id, patient_ids=None):
        with self._get_connection() as conn:
            if patient_ids is None:
                query = f"SELECT * FROM patients WHERE doc_id={doc_id}"
            else:
                ids = [patient_ids] if isinstance(patient_ids, int) else patient_ids
                id_tuple = str(tuple(ids)).replace(',)', ')')
                query = f"SELECT * FROM patients WHERE doc_id={doc_id} AND id IN {id_tuple}"
            return pd.read_sql(query, conn)

    def update_patient(self, p_id, name, contact, age):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE patients SET name=%s, contact_no=%s, age=%s WHERE id=%s", (name, contact, age, p_id))
            conn.commit()

    def delete_patient(self, p_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Delete dependent records first to avoid foreign key errors
            cursor.execute("DELETE FROM records WHERE patient_id=%s", (p_id,))
            cursor.execute("DELETE FROM patients WHERE id=%s", (p_id,))
            conn.commit()

    # ==========================================
    # --- MEDICAL RECORD CRUD ---
    # ==========================================

    def create_medical_record(self, patient_id, data_dict, target, prob):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            vals = list(data_dict.values())
            query = """INSERT INTO records (patient_id, Age, Gender, ChestPainType, RestingBloodPressure,
                       Cholesterol, FastingBloodSugar, RestECG, MaxHeartRate, ExerciseInducedAngina,
                       ST_Depression, ST_Slope, MajorVessels, Thalassemia, Target, Probability)
                       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
            cursor.execute(query, [patient_id] + vals + [target, prob])
            conn.commit()

    def get_records(self, patient_id, record_ids=None):
        with self._get_connection() as conn:
            if record_ids is None:
                query = f"SELECT * FROM records WHERE patient_id={patient_id} ORDER BY visit_date DESC"
            else:
                ids = [record_ids] if isinstance(record_ids, int) else record_ids
                id_tuple = str(tuple(ids)).replace(',)', ')')
                query = f"SELECT * FROM records WHERE patient_id={patient_id} AND id IN {id_tuple} ORDER BY visit_date DESC"
            return pd.read_sql(query, conn)

    def update_medical_record(self, record_id, data_dict, target, prob):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            vals = list(data_dict.values())
            query = """UPDATE records SET
                       Age=%s, Gender=%s, ChestPainType=%s, RestingBloodPressure=%s,
                       Cholesterol=%s, FastingBloodSugar=%s, RestECG=%s, MaxHeartRate=%s,
                       ExerciseInducedAngina=%s, ST_Depression=%s, ST_Slope=%s,
                       MajorVessels=%s, Thalassemia=%s, Target=%s, Probability=%s,
                       visit_date=CURRENT_TIMESTAMP WHERE id=%s"""
            cursor.execute(query, vals + [target, prob, record_id])
            conn.commit()

    def delete_medical_record(self, record_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM records WHERE id=%s", (record_id,))
            conn.commit()
