from flask import Flask, render_template, request, redirect, url_for, flash, session
from database import db
from database import User, DoctorProfile, PatientProfile, Appointment, Treatment, DoctorAvailability, Department, create_database
from werkzeug.security import generate_password_hash, check_password_hash

from functools import wraps

from datetime import datetime, date, time, timedelta



from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)


app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("SQLALCHEMY_DATABASE_URI", 'sqlite:///hospital.db')
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "default_secret_key")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


create_database(app)


def login_required(view):
    @wraps(view)
    def wrapped_view(*args,**kwargs):
        if current_user() is None:
            flash("please login to continue", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped_view

def role_required(role):
    def decorator(view):
        @wraps(view)
        @login_required
        def wraped_view(*args, **kwargs):
            if current_user().role != role:
                return "You are not authrized to access this page."
            return view(*args, **kwargs)
        return wraped_view
    return decorator


@app.route("/")

def home():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        print(f"Received registration data: name={name}, email={email}, password={'*' * len(password)}")  # Debugging line

        if not name or not email or not password:
            flash("Name, email and password are required", "error")
            return render_template("register.html")

        # if len(password) <6 :
            # flash("password lenght should be greater than 6.", "error")
        #     return render_template("register.html")

        if User.query.filter_by(email= email).first():
            flash("An account with this email already exixts.", "error")
            return render_template("register.html")

        user = User(
            name = name,
            email = email,
            password_hash = generate_password_hash(password),
            role = "patient",
        )

        db.session.add(user)
        db.session.flush()
        db.session.add(PatientProfile(user_id = user.id))
        db.session.commit()
        flash("Registration successfful. Please Log in.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))




@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email_form = request.form.get("email", "").strip().lower()
        password_form = request.form.get("password", "")

        user = User.query.filter_by(email=email_form).first() # if you dontt't put .first() you'll get [user] if you put you'll get user object

        if user is None or not check_password_hash(user.password_hash, password_form):
            flash("Invalid email or password", "error")
            return render_template("login.html", error="Invalid email or password")

        if not user.is_active:
            flash("This account is inactive.", "error")
            return render_template("login.html", error="Your account is inactive. Please contact the administrator.")

        session.clear()
        session["user_id"] = user.id
        return redirect(url_for("dashboard"))  # Redirect to the dashboard after successful login

    return render_template("login.html")





@app.route("/dashboard")
@login_required
def dashboard():

    user = current_user()

    return redirect(url_for(f"{user.role}_dashboard"))


# ===================================Admin routes========================================

@app.route("/admin/dashboard")
@role_required("admin")
def admin_dashboard():
    doctors = DoctorProfile.query.all()
    patients = PatientProfile.query.all()

    return render_template("admin_dashboard.html",
                           doctors=doctors,
                           patients=patients,
                           doctor_count=len(doctors),
                           patient_count=len(patients),
                           appointment_count=Appointment.query.count()
                           )


@app.route("/admin/appointments")
@role_required("admin")
def admin_appointments():
    appointments = Appointment.query.all()
    return render_template("admin_appointments.html", appointments=appointments)


@app.route("/admin/doctors/new", methods=["GET", "POST"])
@role_required("admin")
def add_doctor():
    departments = Department.query.all()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        specialization = request.form.get("specialization", "").strip()
        department_id = request.form.get("department_id", type=int)



        if not all([name, email, password, specialization, department_id]):
            flash("All fields are required.", "error")
            return render_template("doctor_form.html", departments=departments)

        if User.query.filter_by(email=email).first():
            flash("An account with this email already exists.", "error")
            return render_template("doctor_form.html", departments=departments)


        if Department.query.get(department_id) is None:
            flash("Selected department does not exist.", "error")
            return render_template("doctor_form.html", departments=departments)

        user = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
            role="doctor",
        )

        db.session.add(user)
        db.session.flush()  # Flush to get the user ID
        doctor_profile = DoctorProfile(user_id=user.id, specialization=specialization, department_id=department_id)
        db.session.add(doctor_profile)
        db.session.commit()

        flash("Doctor added successfully.", "success")
        return redirect(url_for("admin_dashboard"))

    return render_template("doctor_form.html", departments=departments)



@app.route("/admin/doctors/<int:doctor_id>/edit", methods=["GET", "POST"])
@role_required("admin")
def edit_doctor(doctor_id):
    doctor = DoctorProfile.query.get(doctor_id)
    if not doctor:
        flash("Doctor not found.", "error")
        return redirect(url_for("admin_dashboard"))
    departments = Department.query.all()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        specialization = request.form.get("specialization", "").strip()
        department_id = request.form.get("department_id", type=int)
        password = request.form.get("password", "").strip()



        other_user = User.query.filter_by(email = email).first()

        if not all([name, email, specialization, department_id, password]):
            flash("All fields are required.", "error")
            return render_template("doctor_form.html", doctor=doctor, departments=departments)

        if other_user and other_user.id != doctor.user_id:
            flash("An account with this email already exists.", "error")
            return render_template("doctor_form.html", doctor=doctor, departments=departments)


        doctor.user.name = name
        doctor.user.email = email
        doctor.specialization = specialization
        doctor.department_id = department_id
        doctor.user.password_hash = generate_password_hash(password)
        db.session.commit()
        flash("Doctor profile updated successfully.", "success")
        return redirect(url_for("admin_dashboard"))
    return render_template("doctor_form.html", doctor=doctor, departments=departments)


@app.route("/admin/users/<int:user_id>/toggle-active", methods=["POST", "GET"])
@role_required("admin")
def toggle_user_active(user_id):
    user = User.query.get(user_id)
    if not user or user.role == "admin":  # Prevent deactivating admin users
        flash("User not found.", "error")
        return redirect(url_for("admin_dashboard"))

    user.is_active = not user.is_active
    db.session.commit()
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/patients")
@role_required("admin")
def search_patients():
    search_query = request.args.get("q", "").strip()
    if search_query:
        patients = PatientProfile.query.join(User).filter(
            (User.name.ilike(f"%{search_query}%")) | (User.email.ilike(f"%{search_query}%"))
        ).all()
    else:
        patients = PatientProfile.query.all()

    return render_template("admin_patients.html", patients=patients, search_query=search_query)

@app.route("/admin/department/new", methods=["GET", "POST"])
@role_required("admin")
def add_department():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()

        if not name:
            flash("Department name is required.", "error")
            return render_template("department_form.html")

        if Department.query.filter_by(name=name).first():
            flash("A department with this name already exists.", "error")
            return render_template("department_form.html")

        department = Department(name=name, description=description)
        db.session.add(department)
        db.session.commit()

        flash("Department added successfully.", "success")
        return redirect(url_for("admin_dashboard"))

    return render_template("department_form.html")



# ==================================Doctor routes========================================


@app.route("/doctor/dashboard")
@role_required("doctor")
def doctor_dashboard():
    doctor = doctor_profile()

    appointments = Appointment.query.filter_by(doctor_id=doctor.id).all()

    return render_template("doctor_dashboard.html", doctor=doctor, appointments=appointments, availability = doctor.availability)

@app.route("/doctor/appointments/<int:appointment_id>/status", methods=["GET", "POST"])
@role_required("doctor")
def update_appointment_status(appointment_id):
    doctor = doctor_profile()
    appointment = Appointment.query.get(appointment_id)

    if not appointment or appointment.doctor_id != doctor.id:
        return "Appointment Not Found"

    status = request.form.get("status", "")

    if status not in {"Completed", "Cancelled"}:
        flash("Invalid appointment status.", "error")
        return redirect(url_for("doctor_dashboard"))

    if appointment.status != "Booked":
        flash("Only booked appointments can be updated.", "error")
        return redirect(url_for("doctor_dashboard"))

    appointment.status = status
    db.session.commit()
    flash("Appointment status updated successfully.", "success")
    return redirect(url_for("doctor_dashboard"))

@app.route("/doctor/appointments/<int:appointment_id>/treatment", methods=["GET", "POST"])
@role_required("doctor")
def add_treatment(appointment_id):
    doctor = doctor_profile()
    appointment = Appointment.query.get(appointment_id)

    if not appointment or appointment.doctor_id != doctor.id:
        return "Appointment Not Found"

    if request.method == "POST":
        diagnosis = request.form.get("diagnosis", "").strip()
        treatment_notes = request.form.get("treatment_notes", "").strip()
        prescription = request.form.get("prescription", "").strip()

        if not diagnosis or not treatment_notes:
            flash("Diagnosis and treatment notes are required.", "error")
            return render_template("treatment_form.html", appointment=appointment)

        if appointment.status in {"Cancelled", "Completed"}:
            flash("Cannot add treatment to a cancelled or completed appointment.", "error")
            return redirect(url_for("doctor_dashboard"))

        existing_treatment = Treatment.query.filter_by(appointment_id=appointment.id).first()
        if existing_treatment:
            existing_treatment.diagnosis = diagnosis
            existing_treatment.treatment_notes = treatment_notes
            existing_treatment.prescription = prescription
            db.session.commit()



        treatment = Treatment(
                    appointment_id=appointment.id,
                    diagnosis=diagnosis,
                    treatment_notes=treatment_notes,
                    prescription=prescription
                )
        db.session.add(treatment)
        db.session.commit()
        flash("Treatment details added successfully.", "success")



        return redirect(url_for("doctor_dashboard"))

    return render_template("treatment_form.html", appointment=appointment)


@app.route("/doctor/patients/<int:patient_id>/history", methods=["GET", "POST"])
@role_required("doctor")
def patient_history(patient_id):
    doctor = doctor_profile()
    patient = PatientProfile.query.get(patient_id)

    if not patient:
        return "Patient Not Found"

    appointments = Appointment.query.filter_by(doctor_id=doctor.id, patient_id=patient.id).all()

    return render_template("patient_history.html", patient=patient, appointments=appointments)


@app.route("/doctor/availability", methods=["GET", "POST"])
@role_required("doctor")
def manage_availability():
    doctor = doctor_profile()

    if request.method == "POST":
        available_date = request.form.get("available_date")
        start_time = request.form.get("start_time")
        end_time = request.form.get("end_time")

        if not all([available_date, start_time, end_time]):
            flash("All fields are required.", "error")
            return redirect(url_for("manage_availability"))

        try:
            selected_date = date.fromisoformat(available_date)
            start_time = time.fromisoformat(start_time)
            end_time = time.fromisoformat(end_time)
        except ValueError:
            selected_date = None
        today = date.today()

        if (
            selected_date is None
            or selected_date < today
            or selected_date > today + timedelta(days=6)
            or start_time >= end_time
        ):
            flash("Invalid date or time. Please ensure the date is within the next 7 days and the start time is before the end time.", "error")
            return redirect(url_for("manage_availability"))

        duplicate_availability = DoctorAvailability.query.filter_by(
            doctor_id=doctor.id,
            available_date=selected_date,
            start_time=start_time,
            end_time=end_time
        ).first()

        if duplicate_availability:
            flash("This availability slot already exists.", "error")
            return redirect(url_for("manage_availability"))

        doctor_availability = DoctorAvailability(
            doctor_id=doctor.id,
            available_date=selected_date,
            start_time=start_time,
            end_time=end_time
        )
        db.session.add(doctor_availability)
        db.session.commit()
        flash("Availability added successfully.", "success")
        return redirect(url_for("manage_availability"))
    return render_template("availability.html", availabilities=doctor.availability)


# =================================Patient routes========================================

@app.route("/patient/dashboard")
@role_required("patient")
def patient_dashboard():
    patient = patient_profile()
    today = date.today()

    upcoming = Appointment.query.filter_by(patient_id=patient.id, status="Booked").filter(Appointment.appointment_date >= today).all()

    history = Appointment.query.filter_by(patient_id=patient.id).filter(db.or_(Appointment.appointment_date < today, Appointment.status.in_(["Completed", "Cancelled"]) )).all()


    return render_template("patient_dashboard.html", patient=patient, upcoming=upcoming, history=history)



@app.route("/patient/profile", methods=["GET", "POST"])
@role_required("patient")
def patient_profile_view():
    patient = patient_profile()
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()
        date_of_birth = request.form.get("date_of_birth", "").strip()
        gender = request.form.get("gender", "").strip()
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()


        try:

            date_of_birth = date.fromisoformat(date_of_birth)
        except ValueError:
            date_of_birth = None

        if not all([name, email, password]):
            flash("All fields are required.", "error")
            return render_template("patient_profile.html", patient=patient)

        other_user = User.query.filter_by(email=email).first()

        if other_user and other_user.id != patient.user_id:
            flash("An account with this email already exists.", "error")
            return render_template("patient_profile.html", patient=patient)



        patient.user.name = name
        patient.user.email = email
        patient.user.password_hash = generate_password_hash(password)

        patient.date_of_birth = date_of_birth

        patient.gender = gender
        patient.phone = phone
        patient.address = address

        db.session.commit()
        flash("Profile updated successfully.", "success")
        return redirect(url_for("patient_dashboard"))

    return render_template("patient_profile.html", patient=patient)

@app.route("/patient/doctors")
@role_required("patient")
def search_doctors():
    doctors = DoctorProfile.query.all()
    query = request.args.get("q", "").strip()
      # Debugging line to print the search query

    combined = (
        DoctorProfile.query
        .join(DoctorProfile.user)
        .join(DoctorProfile.department)
        .filter(User.is_active.is_(True))
    )

    if query:
        pattern = f"%{query}%"
        combined = combined.filter(
            db.or_(
                User.name.ilike(pattern),
                DoctorProfile.specialization.ilike(pattern),
                Department.name.ilike(pattern)
            )
        )
        doctors = combined.all()






    return render_template("view_doctors.html", doctors=doctors , query=query)

@app.route("/patient/doctors/<int:doctor_id>/availability", methods=["GET", "POST"])
@role_required("patient")
def doctor_availability(doctor_id):
    doctor = DoctorProfile.query.get(doctor_id)

    if not doctor or not doctor.user.is_active:
        return "Doctor Not Found"

    today = date.today()

    availability = DoctorAvailability.query.filter_by(doctor_id=doctor.id).filter(DoctorAvailability.available_date >= today).all()


    return render_template("doctor_availability.html", doctor=doctor, availability=availability)


@app.route("/patient/appointments/book", methods=["GET", "POST"])
@role_required("patient")
def book_appointment():
    patient = patient_profile()

    if request.method == "POST":
        doctor_id = request.form.get("doctor_id", type=int)
        available_date = request.form.get("appointment_date", "")
        appointment_time = request.form.get("appointment_time", "")
        reason = request.form.get("reason", "").strip()
        doctor = DoctorProfile.query.get(doctor_id)

        print(f"Booking appointment for doctor_id: {doctor_id}, available_date: {available_date}, appointment_time: {appointment_time}, reason: {reason}")
        try:
            selected_date = date.fromisoformat(available_date)
            selected_time = time.fromisoformat(appointment_time)

        except ValueError:
            selected_date = None
            selected_time = None


        slot = DoctorAvailability.query.filter_by(
            doctor_id=doctor_id,
            available_date=selected_date,
            start_time=selected_time
        ).first()



        if (
            not doctor
            or not slot
            or selected_date is None
            or selected_time is None
        ):
            flash("Invalid appointment details.", "error")
            return redirect(url_for("search_doctors"))

        existing_appointment = Appointment.query.filter_by(
            patient_id=patient.id,
            appointment_date=selected_date,
            appointment_time=selected_time,
            status="Booked"
        ).first()

        if existing_appointment:
            flash("You already have an appointment at this time.", "error")
            return redirect(url_for("patient_dashboard"))

        appointment = Appointment(
            doctor_id=doctor.id,
            patient_id=patient.id,
            appointment_date=selected_date,
            appointment_time=selected_time,
            status="Booked",
            reason=reason
        )

        db.session.add(appointment)

        db.session.commit()

        flash("Appointment booked successfully.", "success")
    return redirect(url_for("patient_dashboard"))


@app.route("/patient/appointments/<int:appointment_id>/reschedule", methods=["GET","POST"])
@role_required("patient")
def reschedule_appointment(appointment_id):
    patient = patient_profile()
    appointment = Appointment.query.get(appointment_id)

    if not appointment or appointment.patient_id != patient.id:
        return "Appointment Not Found"

    if appointment.status != "Booked":
        flash("Only booked appointments can be rescheduled.", "error")
        return redirect(url_for("patient_dashboard"))

    if request.method == "POST":
        new_date = request.form.get("appointment_date", "")
        new_time = request.form.get("appointment_time", "")

        print(f"new_date: {new_date}, new_time: {new_time}")

        try:
            selected_date = date.fromisoformat(new_date)
            selected_time = time.fromisoformat(new_time)
        except ValueError:
            flash("Invalid date or time format.", "error")
            return redirect(url_for("reschedule_appointment", appointment_id=appointment.id))

        slot = DoctorAvailability.query.filter(
            DoctorAvailability.doctor_id == appointment.doctor_id,
            DoctorAvailability.available_date == selected_date,
            DoctorAvailability.start_time <= selected_time,
            DoctorAvailability.end_time > selected_time
        )

        if not slot:
            flash("Selected time slot is not available.", "error")
            return redirect(url_for("reschedule_appointment", appointment_id=appointment.id))

        existing_appointment = Appointment.query.filter_by(
            patient_id=patient.id,
            appointment_date=selected_date,
            appointment_time=selected_time,
            status="Booked"
        ).first()

        if existing_appointment:
            flash("You already have an appointment at this time.", "error")
            return redirect(url_for("reschedule_appointment", appointment_id=appointment.id))

        appointment.appointment_date = selected_date
        appointment.appointment_time = selected_time
        db.session.commit()

        flash("Appointment rescheduled successfully.", "success")
        return redirect(url_for("patient_dashboard"))
    return render_template("reschedule.html", appointment=appointment)



@app.route("/patient/appointments/<int:appointment_id>/cancel", methods=["GET","POST"])
@role_required("patient")
def cancel_appointment(appointment_id):
    patient = patient_profile()
    appointment = Appointment.query.get(appointment_id)

    if not appointment or appointment.patient_id != patient.id:
        return "Appointment Not Found"

    if appointment.status != "Booked":
        flash("Only booked appointments can be canceled.", "error")
        return redirect(url_for("patient_dashboard"))

    appointment.status = "Cancelled"
    db.session.commit()

    flash("Appointment canceled successfully.", "success")
    return redirect(url_for("patient_dashboard"))

























# =================================Helper Functions========================================
def current_user():
    user_id = session.get("user_id")
    if user_id is None:
        return None
    return User.query.get(user_id)

def doctor_profile():
    user = current_user()
    if user and user.role == "doctor":
        return DoctorProfile.query.filter_by(user_id=user.id).first()
    return None

def patient_profile():
    user = current_user()
    if user and user.role == "patient":
        return PatientProfile.query.filter_by(user_id=user.id).first()
    return None







if __name__ == "__main__":
    app.run(debug=True)

