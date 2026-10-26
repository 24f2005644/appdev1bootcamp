
# def check_access(required_role=None):
#     user = current_user()

#     if user is None:
#         flash("Please login to continue.", "error")
#         return redirect(url_for("login"))

#     if required_role and user.role != required_role:
#         return "You are not authorized to access this page.", 403

#     return None


# @app.route("/dashboard")

# def dashboard():

#     access_error = check_access()

#     if access_error:
#         return access_error

#     user = current_user()

#     return redirect(url_for(f"{user.role}_dashboard"))




# @app.route("/admin/dashboard")

# def admin_dashboard():

#     access_error = check_access("admin")

#     if access_error:
#         return access_error

#     doctors = DoctorProfile.query.all()
#     patients = PatientProfile.query.all()

#     return render_template("admin_dashboard.html",
#                            doctors=doctors,
#                            patients=patients,
#                            doctor_count=len(doctors),
#                            patient_count=len(patients),
#                            appointment_count=Appointment.query.count()
#                            )




from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)

    # One user can have many posts
    posts = db.relationship(
        "Post",
        back_populates="user",
        cascade="all, delete-orphan"
    )


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)

    # Foreign key referencing User
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    # Each post belongs to one user
    user = db.relationship(
        "User",
        back_populates="posts"
    )


# Create tables
with app.app_context():
    db.create_all()


# Create a user with two posts
@app.route("/users", methods=["POST"])
def create_user():
    user = User(username="vinay")

    user.posts.append(Post(title="Flask Basics"))
    user.posts.append(Post(title="SQLAlchemy Relationships"))

    db.session.add(user)
    db.session.commit()

    return jsonify({
        "message": "User and posts created",
        "user_id": user.id,
        "post_ids": [post.id for post in user.posts]
    }), 201


# Delete a user and all their posts
@app.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    user = db.session.get(User, user_id)

    if user is None:
        return jsonify({"error": "User not found"}), 404

    db.session.delete(user)
    db.session.commit()

    return jsonify({
        "message": "User and related posts deleted"
    }), 200


# Delete a single post
@app.route("/posts/<int:post_id>", methods=["DELETE"])
def delete_post(post_id):
    post = db.session.get(Post, post_id)

    if post is None:
        return jsonify({"error": "Post not found"}), 404

    db.session.delete(post)
    db.session.commit()

    return jsonify({
        "message": "Post deleted"
    }), 200





if __name__ == "__main__":
    app.run(debug=True)

