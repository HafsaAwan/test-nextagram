from flask import Blueprint, render_template, request, redirect, url_for, flash
from models.user import User
from models.image import Image
from flask_login import login_required, login_user, current_user
from instagram_web.util.helpers import upload_file_to_s3
from werkzeug import secure_filename

users_blueprint = Blueprint('users',
                            __name__,
                            template_folder='templates')


@users_blueprint.route('/new', methods=['GET'])
def new():
    return render_template('users/new.html')


@users_blueprint.route('/', methods=['POST'])
def create():
    params = request.form
    new_user = User(username=params.get("username"), email=params.get("email"), password=params.get("password"))
    if new_user.save():
        flash("Successfuly Sign Up!", "success")
        login_user(new_user)  # login the new user after success sign up
        return redirect(url_for("users.show", username=new_user.username))  # then redirect to profile page
    else:
        for err in new_user.errors:
            flash(err, "danger")
        return redirect(url_for("users.new"))


@users_blueprint.route('/<username>', methods=["GET"])  # user profile page
@login_required   # only can access this route after signed in
def show(username):
    user = User.get_or_none(User.username == username) # check whether user exist in database
    if user:
        return render_template("users/show.html",user=user)
    else:
        flash(f"No {username} user found.", "danger" )
        return redirect(url_for('home'))


@users_blueprint.route('/', methods=["GET"])
def index():
    return "USERS"


@users_blueprint.route('/<id>/edit', methods=['GET'])
@login_required
def edit(id):
    user = User.get_or_none(User.id== id)
    if user:
        if current_user.id == int(id):
            return render_template("users/edit.html", user=user)
        else:
            flash("Cannot edit users other than yourself!")
            return redirect(url_for("users.show", username=user.username))
    else:
        flash("No such user!")
        return redirect(url_for("home"))

@users_blueprint.route('/<id>', methods=['POST'])
@login_required
def update(id):
    user = User.get_or_none(User.id == id)
    if user:
        if current_user.id == int(id):
            params = request.form

            user.is_private = True if params.get("private") == "on" else False

            user.username = params.get("username")
            user.email = params.get("email")

            password = params.get("password")

            if len(password) > 0:
                user.password = password
            
            if user.save():
                flash("Successfully updated user!")
                return redirect(url_for("users.show", username=user.username))
            else:
                flash("Unable to edit!")
                for err in user.errors:
                    flash(err)
                return redirect(url_for("users.edit", id=user.id))
        else:
            flash("Cannot edit users other than yourself!")
            return redirect(url_for("users.show", username=user.username))
    else:
        flash("No such user!")
        redirect(url_for("home"))


@users_blueprint.route('/<id>/upload', methods=['POST'])
@login_required
def upload(id):
    user = User.get_or_none(User.id == id)
    if user:
        if current_user.id == int(id):
            # Upload image
            if "profile_image" not in request.files:
                flash("No file provided!")
                return redirect(url_for("users.edit", id=id))

            file = request.files["profile_image"]

            file.filename = secure_filename(file.filename)
            # Get path to image on s3 bucket
            image_path = upload_file_to_s3(file,user.username )
            # Update user with image path
            user.image_path = image_path

            print(user.image_path)
            if user.save():
                return redirect(url_for("users.show", username=user.username))
            else:
                flash("Could not upload image. Please try again")
                return redirect(url_for("users.edit", id=id))       
        else:
            flash("Cannot edit users other than yourself!")
            return redirect(url_for("users.show", username=user.username))
    else:
        flash("No such user!")
        redirect(url_for("home"))


@users_blueprint.route('/<idol_id>/follow', methods=['POST'])
@login_required
def follow(idol_id):
    idol = User.get_by_id(idol_id)
    
    if current_user.follow(idol):
        if current_user.follow_status(idol).is_approved:
            flash(f"You follow {idol.username}", "primary")
        else:
            flash(f"You send request to follow {idol.username}", "primary")
        return redirect(url_for('users.show', username=idol.username))
    else:
        flash(f"Unable to follow this user, try again", "danger")
        return redirect(url_for('users.show', username=idol.username))

@users_blueprint.route('/<idol_id>/unfollow', methods=['POST'])
@login_required
def unfollow(idol_id):
    idol = User.get_by_id(idol_id)
    
    if current_user.unfollow(idol):
        flash(f"You unfollow {idol.username}", "primary")
        return redirect(url_for('users.show', username=idol.username))
    else:
        flash(f"Unable to unfollow this user, try again", "danger")
        return redirect(url_for('users.show', username=idol.username))

@users_blueprint.route('/request', methods=['GET'])
@login_required
def show_request():
    return render_template("users/request.html")

@users_blueprint.route('/<fan_id>/approve', methods=['POST'])
@login_required
def approve(fan_id):
    fan = User.get_by_id(fan_id)
    
    if current_user.approve_request(fan):
        flash(f"You approve {fan.username}'s request", "primary")
        return redirect(url_for('users.show', username=current_user.username))
    else:
        flash(f"Unable to approve this user, try again", "danger")
        return redirect(url_for('users.show', username=current_user.username))


@users_blueprint.route('/<fan_id>/delete_request', methods=['POST'])
@login_required
def delete_request(fan_id):
    fan = User.get_by_id(fan_id)
    
    if fan.unfollow(User.get_by_id(current_user.id)):
        flash(f"You delete {fan.username}'s request", "primary")
        return redirect(url_for('users.show', username=current_user.username))
    else:
        flash(f"Unable to delete this user's request, try again", "danger")
        return redirect(url_for('users.show', username=current_user.username))
