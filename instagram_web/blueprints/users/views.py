from flask import Blueprint, render_template, request, redirect, url_for, flash
from models.user import User
from flask_login import login_required, login_user, current_user
from werkzeug import secure_filename
from instagram_web.util.helpers import upload_file_to_s3

users_blueprint = Blueprint('users',
                            __name__,
                            template_folder='templates')

@users_blueprint.route('/new', methods=['GET'])
def new():
    return render_template('users/new.html')


@users_blueprint.route('/', methods=['POST'])
def create():
    params = request.form

    new_user = User(username = params.get("username"), email=params.get("email"), password=params.get("password"))

    if new_user.save():
        flash("Sign Up Successful", 'success')
        login_user(new_user) #login new user after sign up
        return redirect(url_for('users.show', username=new_user.username)) # redirect user to profile page
    else:
        flash(new_user.errors)
        return redirect(url_for("users.new"))

@users_blueprint.route('/<username>', methods=["GET"])
@login_required
def show(username):
    user = User.get_or_none(User.username == username)
    if user:
        return render_template("users/show.html", user=user)
    else:
        flash("No user found")
        return redirect(url_for('home'))


@users_blueprint.route('/', methods=["GET"])
def index():
    return "USERS"


@users_blueprint.route('/<id>/edit', methods=['GET'])
@login_required
def edit(id):
    user = User.get_or_none(User.id == id)
    if user:
        if current_user.id == int(id):
            return render_template("users/edit.html", user=user)
        else:
            flash("Cannot edit someone else's profile")
            return redirect(url_for('users.show', username=user.username))
    else:
        flash("No user found")
        return redirect(url_for("home"))



@users_blueprint.route('/<id>', methods=['POST'])
@login_required
def update(id):
    user = User.get_or_none(User.id == id)
    if user:
        if current_user.id == int(id):
            params = request.form

            user.username = params.get("username")
            user.email = params.get("email")
           
            password = params.get("password")
            
            if len(password) > 0:
                user.password = password
            
            if user.save():
                
                flash("Successfully updated details.")
                return redirect(url_for("users.show", username=user.username))
            else:
                flash("Failed to edit the details. Try again")
                for err in user.errors:
                    flash(err)
                return redirect(url_for("users.edit", id=user.id))
        else:
            flash("You cannot edit details of another user")
            return redirect(url_for("home"))
    else:
        flash("No such user found")
        return redirect(url_for("home"))

@users_blueprint.route('/<id>/upload', methods=['POST'])
@login_required
def upload(id):
    user = User.get_or_none(User.id == id)
    if user:
        if current_user.id == int(id):
            # Upload image
            if "profile_image" not in request.files:
                flash("No file selected")
                return redirect(url_for("users.edit", id=id))

            file = request.files["profile_image"]

            file.filename = secure_filename(file.filename)

            image_path = upload_file_to_s3(file, user.username)

            user.image_path = image_path

            if user.save():
                return redirect(url_for("users.show", username = user.username))
            else:
                flash("Upload failed, try again!")
                return redirect(url_for("user.edit", id=id))
        else:
            flash("You cannot edit other profiles")
            return redirect(url_for("users.show", username = user.username))
    else:
        flash("No such user found")
        return redirect(url_for("home"))