'''
This Python file contains the routing logic for the Flask web application.

File is split into the main routing and routing to do with authetication lower down.

Note: This files imports from db.py to write to the database

Author: Joshua Hitchon
Date: April 9, 2023
'''

# flask imports
from flask import Blueprint, render_template, request, Response, redirect, url_for, jsonify
from flask_login import login_user, login_required, logout_user, current_user
from flask_socketio import emit
from werkzeug.utils import secure_filename
# from app import socketio

# custom imports
from .models import Img, Marker, User, LoginForm, RegisterForm
from .db import db
from .bcrypt import bcrypt
from .login_manager import login_manager
from app import socketio

# Register blueprints - note they are split for future modularity
main = Blueprint('main', __name__)
auth = Blueprint('auth', __name__)

# Main website routes


@socketio.on('my_event')
def handler(data):
    print("recieved event:", data)


@main.route('/')
def index():
    return render_template('landing.html')


@main.route('/dashboard')
@login_required
def dashboard():
    return render_template('main.html')


@main.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))


@main.route('/db')
def db_page():
    return render_template('db.html')


@main.route('/upload', methods=['POST'])
def upload():
    if request.method == "POST":
        pic = request.files['pic']
        lat = 51.380741
        long = -2.360147

        title = request.form.get('input-title')
        desc = request.form.get('input-desc')

        if pic:
            filename = secure_filename(pic.filename)
            mimetype = pic.mimetype
            if not filename or not mimetype:
                return 'Bad upload!', 400

            img = Img(img=pic.read(), name=filename, mimetype=mimetype)
            db.session.add(img)
            db.session.commit()

        marker = Marker(ownerID=1, lat=lat, long=long, imgID=(img.id if pic else None),
                        title=title, description=desc)
        db.session.add(marker)
        db.session.commit()

    return render_template("main.html")


def createNewMarker():
    # add image to db
    img = Img(img=pic.read(), name=filename, mimetype=mimetype)
    db.session.add(img)
    db.session.commit()

    # add marker with image to db
    marker = Marker(lat=lat, long=long, imgID=img.id,
                    title=title, description=desc)
    db.session.add(marker)
    db.session.commit()

    return marker


@socketio.on('connect')
def getMarkers(ownerID=1):
    results = Marker.query.filter_by(ownerID=1).all()
    print(results[0].serialize())
    print("Joined")

    emit('receiveMarkers', {str(r.id): r.serialize() for r in results})


def getMarkersWithTags(tags=["all"]):
    if "all" in tags:
        pass  # get all tags
    else:
        pass  # loop through all tags


# authentication routes


@ login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@ main.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('main.dashboard'))
    return render_template('login.html', form=form)


@ main.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('main.login'))

    return render_template('register.html', form=form)
