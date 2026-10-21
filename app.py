from flask import Flask, render_template, request, redirect, url_for, flash, session
from database import db
from database import User, DoctorProfile, PatientProfile, Appointment, Treatment, DoctorAvailability, create_database
from werkzeug.security import generate_password_hash, check_password_hash

from functools import wraps

app = Flask(__name__)


app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///hospital.db"
app.config["SECRET_KEY"] = "+WdmukgUu)fhyXAw"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


create_database(app)


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



def login_required(view):
    @wraps(view)
    def wrapped_view(*args,**kwargs):
        if current_user() is None:
            flash("please login to continue", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped_view


@app.route("/dashboard")
@login_required
def dashboard():
    user = current_user()

    return redirect(url_for(f"{user.role}_dashboard"))





def current_user():
    user_id = session.get("user_id")
    if user_id is None:
        return None
    return User.query.get(user_id)







if __name__ == "__main__":
    app.run(debug=True)

