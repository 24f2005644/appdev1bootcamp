from flask import Flask, render_template, request, redirect, url_for, flash, session
from database import db
from database import User, DoctorProfile, PatientProfile, Appointment, Treatment, DoctorAvailability, Department, create_database
from werkzeug.security import generate_password_hash, check_password_hash

from functools import wraps

app = Flask(__name__)


app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///hospital.db"
app.config["SECRET_KEY"] = "+WdmukgUu)fhyXAw"
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
        department_id = request.form.get("department", type=int)
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

