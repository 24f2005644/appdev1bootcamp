from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # e.g., 'admin', 'doctor', 'patient'
    is_active = db.Column(db.Boolean, default=True)

    doctor_profile = db.relationship("DoctorProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    patient_profile = db.relationship("PatientProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")

class Department(db.Model):
    __tablename__ = "departments"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    doctors = db.relationship("DoctorProfile", back_populates="department", cascade="all, delete-orphan")


class DoctorProfile(db.Model):
    __tablename__ = "doctor_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete = "CASCADE"), nullable=False, unique=True)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=False)
    specialization = db.Column(db.String(100), nullable=False)



    user = db.relationship("User", back_populates="doctor_profile")
    department = db.relationship("Department", back_populates="doctors")
    availability = db.relationship("DoctorAvailability", back_populates="doctor", cascade="all, delete-orphan")
    appointments = db.relationship("Appointment", back_populates="doctor", cascade="all, delete-orphan")

class PatientProfile(db.Model):
    __tablename__ = "patient_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete = "CASCADE"), nullable=False, unique=True)
    date_of_birth = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    address = db.Column(db.String(200), nullable=False)


    user = db.relationship("User", back_populates="patient_profile")
    appointments = db.relationship("Appointment", back_populates="patient", cascade="all, delete-orphan")


class Appointment(db.Model):
    __tablename__ = "appointments"

    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctor_profiles.id"), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey("patient_profiles.id"), nullable=False)
    appointment_date = db.Column(db.DateTime, nullable=False)
    appointment_time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(50), nullable=False)  # e.g., 'scheduled', 'completed', 'canceled'
    reason = db.Column(db.Text, nullable=True)


    doctor = db.relationship("DoctorProfile", back_populates="appointments")
    patient = db.relationship("PatientProfile", back_populates="appointments")

    treatment = db.relationship("Treatment", back_populates="appointment", uselist=False, cascade="all, delete-orphan")

class Treatment(db.Model):
    __tablename__ = "treatments"

    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey("appointments.id", ondelete= "CASCADE" ), nullable=False)
    diagnosis = db.Column(db.Text, nullable=False)
    treatment_notes = db.Column(db.Text, nullable=False)
    prescription = db.Column(db.Text, nullable=True)



    appointment = db.relationship("Appointment", back_populates="treatment")



class DoctorAvailability(db.Model):
    __tablename__ = "doctor_availability"

    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctor_profiles.id", ondelete="CASCADE"), nullable=False)
    available_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)


    doctor = db.relationship("DoctorProfile", back_populates="availability")




def create_database(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()
        admin = User.query.filter_by(role="admin").first()
        if not admin:
            admin = User(
                name="Admin",
                email="admin@email.com",
                password_hash=generate_password_hash("admin123"),
                role = 'admin'
                )

        db.session.add(admin)
        db.session.commit()



