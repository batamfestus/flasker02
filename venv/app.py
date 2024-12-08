from flask import Flask, render_template, flash, request, url_for, redirect, session, sessions
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, BooleanField, ValidationError, TextAreaField, FileField
from wtforms.widgets import TextArea
from wtforms.validators import DataRequired, EqualTo, Length
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pymysql
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_ckeditor import CKEditor
from flask_ckeditor import CKEditorField
from flask_wtf.file import FileField
from werkzeug.utils import secure_filename
import uuid as uuid
import os
from dotenv import load_dotenv

from flask_migrate import Migrate

# Ensure SQLAlchemy uses PyMySQL
pymysql.install_as_MySQLdb()



# To create a flask instance
app = Flask(__name__)
ckeditor = CKEditor(app)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

UPLOAD_FOLDER = "static/images/"
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER')

### creating our database
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
db = SQLAlchemy(app)
migrate = Migrate(app, db)


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

################ DATABASE MODEL ###############
class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(225), nullable=False, unique=True)
    name = db.Column(db.String(250), nullable=False)
    email = db.Column(db.String(250), nullable=False, unique=True)
    favorite_color = db.Column(db.String(120))
    about_author = db.Column(db.Text, nullable=True) 
    date_added = db.Column(db.DateTime, default=datetime.utcnow)
    profile_pic = db.Column(db.String(250), nullable=True) 
    user_password = db.Column(db.String(128))


    posts = db.relationship("Posts", backref="poster")
    

    @property
    def password(self):
        raise AttributeError("Password is not a readable attribute")
    
    @password.setter
    def password(self, password):
        self.user_password = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.user_password, password)

    def __repr__(self) -> str:
        return "<Name %r>" % self.name

class Posts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250))
    content = db.Column(db.Text)
    # author = db.Column(db.String(255))
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    slug = db.Column(db.String(255))

    poster_id = db.Column(db.Integer, db.ForeignKey("users.id"))


class UserForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    username= StringField("Username", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired()])
    favorite_color = StringField("Favorite Color")
    about_author = TextAreaField("Author")
    user_password = PasswordField("Password", validators=[DataRequired(), EqualTo("confirm_password", message="Passwords must match")])
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired()])
    profile_pic = FileField("Profile Picture")
    submit = SubmitField("Submit")

############### CREATE A FORM CLASS ####################
class NameForm(FlaskForm):
    name = StringField("What is your name", validators=[DataRequired()])
    submit = SubmitField("Submit")

class PostForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    # content = StringField("Content", validators=[DataRequired()], widget=TextArea())
    content = CKEditorField('Content', validators=[DataRequired()])
    author = StringField("Author")
    slug = StringField("Slug", validators=[DataRequired()])
    submit = SubmitField("Submit Post")

class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    user_password = PasswordField("Password", validators=[DataRequired()])
    # confirm_password = PasswordField("Confirm Password", validators=[DataRequired()])
    submit = SubmitField("Submit")

class SearchForm(FlaskForm):
    searched = StringField("Searched", validators=[DataRequired()])
    submit = SubmitField("Submit")



# create a route decorator
@app.route("/")
def index():
    first_name = "John"
    best_movies = ['Avatar', 'Game of throne', 'Originals', 'Bob hearts Abisola']
    return render_template("index.html", first_name=first_name, best_movies=best_movies)

@app.route("/admin")
@login_required
def admin():
    id = current_user.id
    name = current_user.username 
    if id == 1 or id == 2:
        return render_template("admin.html")
    else:
        flash("You are not authorized to access this page. ADMINS ONLY.....")
        return redirect(url_for("dashboard", name=name))

@app.context_processor
def base():
    form = SearchForm()
    return dict(form=form)

@app.route("/search", methods=['GET', 'POST'])
def search():
    form = SearchForm()
    posts = Posts.query
    if form.validate_on_submit():
        post.searched = form.searched.data  
        posts = posts.filter(Posts.content.like('%' + post.searched + '%'))
        posts = posts.order_by(Posts.title).all()
        return render_template("search.html", form=form, searched=post.searched, posts=posts)

@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = Users.query.filter_by(username=form.username.data).first()
        if user:
            if check_password_hash(user.user_password, form.user_password.data):
                login_user(user)
                flash("Login Successfully")
                return redirect(url_for("dashboard"))
            else:
                flash("Wrong Password...")
        else:
            flash("User does not Exist")
    return render_template('login.html', form=form)

@app.route("/logout", methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    flash("You have been logged out. Have a wonderful day")
    return redirect(url_for("login"))

@app.route("/dashboard", methods=['GET', 'POST'])
@login_required
def dashboard():
    form = UserForm()
    id = current_user.id
    name_to_update = Users.query.get_or_404(id) 
    if request.method == "POST":
        name_to_update.name = request.form['name']
        name_to_update.email = request.form['email']
        name_to_update.favorite_color = request.form['favorite_color']
        name_to_update.username = request.form['username']
        name_to_update.about_author = request.form['about_author']

        if request.files['profile_pic']:
            name_to_update.profile_pic = request.files['profile_pic']
            pic_filename = secure_filename(name_to_update.profile_pic.filename)
            pic_name = str(uuid.uuid1()) + "_" + pic_filename
            saver = request.files['profile_pic']
            name_to_update.profile_pic = pic_name
            
            try:
                db.session.commit()
                saver.save(os.path.join(app.config['UPLOAD_FOLDER'], pic_name))
                flash("User updated successfully")
                return render_template("dashboard.html", form=form, name_to_update=name_to_update)
            except:
                flash("Error ocured while updating. Try again")
                return render_template("dashboard.html", form=form, name_to_update=name_to_update)
        else:
            db.session.commit()
            flash("User updated successfully")
            return render_template("dashboard.html", form=form, name_to_update=name_to_update)
    else:
        return render_template("dashboard.html", form=form, name_to_update=name_to_update)

@app.route('/add-post', methods=['GET', 'POST'])
# @login_required
def add_post():
    form = PostForm()

    if form.validate_on_submit():
        poster = current_user.id
        post = Posts(title=form.title.data, content=form.content.data, poster_id=poster, slug=form.slug.data)
        form.title.data = " "
        form.content.data = " "
        form.author.data = " "
        form.slug.data = " "

        db.session.add(post)
        db.session.commit()

        flash("Blog post submitted successfully")

    return render_template("add_post.html", form=form)

@app.route("/posts")
def posts():
    posts = Posts.query.order_by(Posts.date_posted)
    return render_template("posts.html", posts=posts)

@app.route("/post/<int:id>")
def post(id):
    post = Posts.query.get_or_404(id) 
    return render_template("post.html", post=post)


@app.route("/posts/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_post(id):
    post = Posts.query.get_or_404(id)  
    form = PostForm()

    if form.validate_on_submit():
        post.title = form.title.data 
        # post.author = form.author.data 
        post.content = form.content.data 
        post.slug = form.slug.data 

        db.session.commit()

        flash("Post edited successfully!")
        return redirect(url_for('post', id=post.id))
    
    if current_user.id == post.poster.id or current_user.id == 1 or current_user.id == 2:
    # Pre-fill form fields with current post data
        form.title.data = post.title
        # form.author.data = post.author  # Ensure PostForm includes an 'author' field
        form.slug.data = post.slug
        form.content.data = post.content
    else:
        flash("You are not directed to edit this post")
        post = Posts.query.order_by(Posts.date_posted)
        return render_template("posts.html", posts=posts)
    
    return render_template("edit_post.html", form=form)


@app.route('/posts/delete/<int:id>')
@login_required
def delete_post(id):
    post_to_delete = Posts.query.get_or_404(id) 
    id = current_user.id  
    if id == post_to_delete.poster.id or id == 1 or id == 2: 
        try:
            db.session.delete(post_to_delete)
            db.session.commit()
            flash("Blog post deleted...")
            posts = Posts.query.order_by(Posts.date_posted)
            return render_template("posts.html", posts=posts)
        except:
            flash("OOPPSSS a problem occured while deleting post...")
            posts = Posts.query.order_by(Posts.date_posted)
            return render_template("posts.html", posts=posts)
    else:
        flash("You are not authorize to delete the post")
        posts = Posts.query.order_by(Posts.date_posted)
        return render_template("posts.html", posts=posts)

@app.route("/user/<name>")
def user(name):
    return render_template("user.html", user_name=name)

@app.route("/user/add", methods=['GET', 'POST'])
def add_user():
    name = None
    form = UserForm()

    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()
        if user is None:
            user_password = generate_password_hash(form.user_password.data, method="pbkdf2:sha256")
            user = Users(
                name=form.name.data, 
                username =form.username.data,
                email=form.email.data, 
                favorite_color=form.favorite_color.data, 
                user_password=user_password
            )
            db.session.add(user)
            db.session.commit()
        name = form.name.data  
        form.name.data = ""
        form.username.data = ""
        form.email.data = ""
        form.favorite_color.data = ""
        form.user_password.data = ""
        flash("User added Successfully")
    
    our_users = Users.query.order_by(Users.date_added)
    return render_template('add_user.html', form=form, our_users=our_users)


@app.route("/update/<int:id>", methods=['GET', 'POST'])
@login_required
def update(id):
    form = UserForm()
    name_to_update = Users.query.get_or_404(id) 
    if request.method == "POST":
        name_to_update.name = request.form['name']
        name_to_update.email = request.form['email']
        name_to_update.favorite_color = request.form['favorite_color']
        name_to_update.username = request.form['username']
        try:
            db.session.commit()
            flash("User updated successfully")
            return render_template("update.html", form=form, name_to_update=name_to_update)
        except:
            flash("Error ocured while updating. Try again")
            return render_template("update.html", form=form, name_to_update=name_to_update, id=id)
    else:
        return render_template("update.html", form=form, name_to_update=name_to_update, id=id)
    

@app.route("/delete/<int:id>")
@login_required
def delete(id):
    if id == current_user.id:
        form = UserForm()  # Instantiate the form
        user_to_delete = Users.query.get_or_404(id)

        try:
            # Save the user's name before deletion for feedback
            user_name = user_to_delete.name
            db.session.delete(user_to_delete)
            db.session.commit()
            flash(f"User '{user_name}' deleted successfully.")
        except Exception as e:
            # Log the error for debugging
            flash("There was an error deleting the user.")
            print(f"Error deleting user {id}: {e}")

        # Retrieve updated users list and render the page
        our_users = Users.query.order_by(Users.date_added).all()
        return render_template("add_user.html", form=form, our_users=our_users)
    else:
        flash("OOPPss!!! Sorry you can't delete the user...")
        return redirect(url_for("dashboard"))



@app.route("/name", methods=['GET', 'POST'])
def name():
    name = None
    form = NameForm()

    #### validate form
    if form.validate_on_submit():
        name = form.name.data  
        form.name.data = ""

        flash("Form Submitted Successfully")
    return render_template("name.html", name=name, form=form)

# custom error pages
# invalid url
@app.errorhandler(404)
def page_not_found(e):
    return render_template ("404.html"), 404
# internal server error
@app.errorhandler(500)
def server_error(e):
    return render_template ("500.html"), 500

with app.app_context():
    db.create_all()

if __name__ == "__main__":  # This creates tables based on models if they don't already exist
    app.run(debug=True)
