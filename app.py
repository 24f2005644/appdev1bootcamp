from flask import Flask, render_template
from database import db
from database import User, DoctorProfile, PatientProfile, Appointment, Treatment, DoctorAvailability, create_database


app = Flask(__name__)


app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///hospital.db"


create_database(app)


@app.route("/")
def home():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)

