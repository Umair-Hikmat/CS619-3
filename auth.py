import streamlit as st
import database_helper as db
import re

class AuthenticationService:
    def __init__(self, db_manager: db.DatabaseManager):
        self.db_manager = db_manager

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

    def _validate_email(self, email):
        if not email.strip():
            return False, "Email required."
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return False, "Invalid email format."
        return True, "Success"

    def login_page(self):
        st.markdown("<h1 style='text-align: center;'>🏥 Deep Heart Pro</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center;'>Doctor Login Portal</h3>", unsafe_allow_html=True)

        with st.container():
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Login", use_container_width=True):
                    user = self.db_manager.verify_login(email, password)
                    if user:
                        st.session_state.logged_in = True
                        st.session_state.user_id = user[0]
                        st.session_state.user_name = f"{user[1]} {user[2]}"
                        st.success(f"Welcome Dr. {user[1]}")
                        st.rerun()
                    else:
                        st.error("Invalid credentials.")

            with col2:
                if st.button("Sign Up", use_container_width=True):
                    st.session_state.auth_mode = "signup"
                    st.rerun()

            st.write("---")
            if st.button("Forgot Password?", use_container_width=True):
                st.session_state.auth_mode = "forgot"
                st.rerun()

    def signup_page(self):
        st.subheader("👨‍⚕️ Create Doctor Account")

        # Initialize session state for errors if not present
        if "signup_email_error" not in st.session_state:
            st.session_state.signup_email_error = ""
        if "signup_contact_error" not in st.session_state:
            st.session_state.signup_contact_error = ""
        if "signup_general_error" not in st.session_state:
            st.session_state.signup_general_error = ""

        with st.form("signup_form"):
            col_a, col_b = st.columns(2)
            with col_a:
                f_name = st.text_input("First Name")
                email = st.text_input("Email")
                if st.session_state.signup_email_error: # Display error if exists
                    st.error(st.session_state.signup_email_error)
                password = st.text_input("Password", type="password")
            with col_b:
                l_name = st.text_input("Last Name")
                contact = st.text_input("Contact No")
                if st.session_state.signup_contact_error: # Display error if exists
                    st.error(st.session_state.signup_contact_error)
                qual = st.text_input("Qualification (MBBS/MD)")

            dob = st.date_input("Date of Birth")

            submit = st.form_submit_button("Complete Registration")

            if submit:
                # Reset all errors at the start of a new submission attempt
                st.session_state.signup_email_error = ""
                st.session_state.signup_contact_error = ""
                st.session_state.signup_general_error = ""

                # Perform individual field validations
                email_valid, email_msg = self._validate_email(email)
                contact_valid, contact_msg = self._validate_contact_number(contact)

                if not email_valid:
                    st.session_state.signup_email_error = email_msg
                if not contact_valid:
                    st.session_state.signup_contact_error = contact_msg

                # Check for other mandatory fields (if individual validations pass or set their own errors)
                if not f_name.strip() or not l_name.strip() or not password.strip() or not qual.strip() or dob is None:
                    st.session_state.signup_general_error = "Please fill in all required fields."
                
                # If there are no errors, attempt to create the doctor
                if not st.session_state.signup_email_error and \
                   not st.session_state.signup_contact_error and \
                   not st.session_state.signup_general_error: # All checks passed so far
                    
                    success = self.db_manager.create_doctor(f_name, l_name, email, contact, password, qual, str(dob))
                    if success:
                        st.success("Account created! Please log in.")
                        st.session_state.auth_mode = "login"
                        st.rerun()
                    else:
                        st.session_state.signup_general_error = "Email already registered or another database error occurred."
                
            # Display general error after the submit button if it exists
            if st.session_state.signup_general_error:
                st.error(st.session_state.signup_general_error)

        if st.button("← Back to Login"):
            # Clear all signup related session state errors when navigating away
            st.session_state.signup_email_error = ""
            st.session_state.signup_contact_error = ""
            st.session_state.signup_general_error = ""
            st.session_state.auth_mode = "login"
            st.rerun()

    def forgot_password_page(self):
        st.subheader("🔑 Reset Password")
        st.info("Enter your registered email to reset your credentials.")
        email = st.text_input("Registered Email")
        if st.button("Send Reset Instructions"):
            st.success(f"If {email} is in our database, instructions have been sent.")

        if st.button("← Back to Login"):
            st.session_state.auth_mode = "login"
            st.rerun()
