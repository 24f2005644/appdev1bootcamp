
def check_access(required_role=None):
    user = current_user()

    if user is None:
        flash("Please login to continue.", "error")
        return redirect(url_for("login"))

    if required_role and user.role != required_role:
        return "You are not authorized to access this page.", 403

    return None


@app.route("/dashboard")

def dashboard():

    access_error = check_access()

    if access_error:
        return access_error

    user = current_user()

    return redirect(url_for(f"{user.role}_dashboard"))




@app.route("/admin/dashboard")

def admin_dashboard():

    access_error = check_access("admin")

    if access_error:
        return access_error

    doctors = DoctorProfile.query.all()
    patients = PatientProfile.query.all()

    return render_template("admin_dashboard.html",
                           doctors=doctors,
                           patients=patients,
                           doctor_count=len(doctors),
                           patient_count=len(patients),
                           appointment_count=Appointment.query.count()
                           )



