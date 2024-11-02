"""
Blog Webpage

Author: Alan
Date: October 16th 2024

This application uses Flask to show a webpage that uses Bootstrap for design and a json for the data.
"""
import hashlib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from functools import wraps
from smtplib import SMTP

from flask import Flask
from flask import abort
from flask import render_template, request, url_for, flash
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_login import LoginManager, UserMixin
from flask_login import login_user, current_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String, Text, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import redirect

from forms import PostForm, RegisterForm, LogInForm, CommentForm

EMAIL = "email@gmail.com"  # Your email
PASSWORD = "password"  # Your password
HOST = "smtp.gmail.com"  # I use gmail's smtp, may change depending on your email provider
PORT = 587

# Starts the app
app = Flask(__name__)

app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
ckeditor = CKEditor(app)
Bootstrap5(app)

# Starts the login manager
login_manager = LoginManager()
login_manager.init_app(app)


class Base(DeclarativeBase):
    pass


# Were we will save the data
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)


class User(UserMixin, db.Model):
    __tablename__ = "user_table"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Data
    email: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(250), nullable=False)
    name: Mapped[str] = mapped_column(String(250), nullable=False)

    # Relationship to BlogPost
    posts = relationship("BlogPost", back_populates="author")

    # Relationship to Comment
    comments = relationship("Comment", back_populates="author")


class BlogPost(db.Model):
    __tablename__ = "blogpost_table"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Data
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)

    # Relationship to Comment
    comments = relationship("Comment", back_populates="blogpost")

    # Foreign key to User and relationship
    author_id: Mapped[int] = mapped_column(ForeignKey("user_table.id"), nullable=False)
    author = relationship("User", back_populates="posts")


class Comment(db.Model):
    __tablename__ = "comment_table"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Data
    text: Mapped[str] = mapped_column(Text, nullable=False)

    # Foreign key to User and relationship
    author_id: Mapped[int] = mapped_column(ForeignKey("user_table.id"), nullable=False)
    author = relationship("User", back_populates="comments")

    # Foreign key to BlogPost and relationship
    blogpost_id: Mapped[int] = mapped_column(ForeignKey("blogpost_table.id"), nullable=False)
    blogpost = relationship("BlogPost", back_populates="comments")


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, user_id)


with app.app_context():
    db.create_all()


def gravatar_url(email, size=100, default="retro", rating="g"):
    """
    Uses gravatar to get the images from the site
    :param email: String with email
    :param size: Integer with size of image
    :param default: String of what image to choose if now found
    :param rating: String with the level of control of parenting of the image (General)
    :return:
    """
    hashed_email = hashlib.md5(email.strip().lower().encode("utf-8")).hexdigest()
    return f"https://www.gravatar.com/avatar/{hashed_email}?s={size}&d={default}&r={rating}"


def admin_only(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if not current_user.id == 1:
            return abort(403)
        return func(*args, **kwargs)

    return decorated_function


@app.route('/')
def index():
    """
    Renders index.html file
    :return:
    """
    blogposts = db.session.execute(db.select(BlogPost)).scalars().all()

    return render_template("index.html", posts=blogposts, current_user=current_user)


@app.route('/post/<int:index_number>', methods=["GET", "POST"])
def post(index_number):
    """
    Renders post.html file using an index number to post a certain post.
    :param index_number:
    :return:
    """
    form = CommentForm()
    blogpost = db.get_or_404(BlogPost, index_number)
    blogpost_id = blogpost.id

    comments = db.session.execute(db.select(Comment).where(Comment.blogpost_id == blogpost_id)).scalars().all()

    if request.method == "POST":
        text = request.form.get("text")
        new_comment = Comment(
            text=text,
            author_id=current_user.id,
            blogpost_id=blogpost_id
        )

        # Adds the new comment
        db.session.add(new_comment)
        # Saves the data
        db.session.commit()

        return redirect(url_for("post", index_number=blogpost_id))

    return render_template("post.html", post=blogpost, comments=comments, form=form, current_user=current_user,
                           gravatar_url=gravatar_url)


@app.route("/new-post", methods=["GET", "POST"])
@admin_only
@login_required
def add_new_post():
    """
    Renders a form where the user can add a new blog
    :return:
    """
    form = PostForm()
    is_new_post = True

    # If the user clicks on submit
    if request.method == "POST":
        # Gets the server date in a formatted code
        date = datetime.now().strftime("%B %d, %Y")
        # Creates a new post using the form's data
        new_post = BlogPost(
            title=request.form.get("title"),
            subtitle=request.form.get("subtitle"),
            body=request.form.get("body"),
            date=date,
            author_id=current_user.id,
            img_url=request.form.get("img_url"),
        )
        # Adds the new row to the database
        db.session.add(new_post)

        # Saves changes
        db.session.commit()

        return redirect(url_for("index"))

    return render_template("make-post.html", is_new_post=is_new_post, form=form, current_user=current_user)


@app.route("/edit-post/<int:index_number>", methods=["GET", "POST"])
@admin_only
@login_required
def edit_post(index_number):
    """
    Renders a form where the user can edit an existing form
    :return:
    """
    blogpost = db.get_or_404(BlogPost, index_number)

    form = PostForm(
        title=blogpost.title,
        subtitle=blogpost.subtitle,
        img_url=blogpost.img_url,
        body=blogpost.body
    )

    is_new_post = False

    # If the user clicks on submit
    if request.method == "POST":
        # Creates a new post using the form's data
        blogpost.title = request.form.get("title")
        blogpost.subtitle = request.form.get("subtitle")
        blogpost.body = request.form.get("body")
        blogpost.img_url = request.form.get("img_url")

        # Saves changes
        db.session.commit()

        return redirect(url_for("index"))

    return render_template("make-post.html", is_new_post=is_new_post, form=form, current_user=current_user)


@app.route("/delete/<int:index_number>")
@admin_only
@login_required
def delete_post(index_number):
    """
    Gets the index number and deletes the blog from the database
    :param index_number:
    :return:
    """
    # Search the blogpost
    blogpost = db.get_or_404(BlogPost, index_number)
    # Deletes the blogpost
    db.session.delete(blogpost)
    # Saves the blogpost
    db.session.commit()

    return redirect(url_for("index"))


@app.route("/register", methods=["GET", "POST"])
def register():
    """
    Renders the register.html page
    Once the user completes the form, we will register
    :return:
    """
    # Creates a new form using the RegisterForm class
    form = RegisterForm()
    if request.method == "POST":
        # Get the data from the form
        email = request.form.get("email")
        password = request.form.get("password")
        name = request.form.get("name")

        # Get the data from the database
        user = db.session.execute(db.select(User).where(User.email == email)).scalar()

        # Checks if there is a user in the database, if we couldn't find them, then we create one
        if not user:

            # Generate a password using a hashed method
            hashed_password = generate_password_hash(password, method="pbkdf2:sha256", salt_length=8)

            new_user = User(
                email=email,
                password=hashed_password,
                name=name
            )

            # Add a new user to the database
            db.session.add(new_user)

            # Save the data to the database
            db.session.commit()

            login_user(new_user)

            return redirect(url_for("index"))

        # If we founded, we redirect them to the login page
        else:
            flash("Log in with that email instead!")
            return redirect(url_for("login"))

    return render_template("register.html", form=form, current_user=current_user)


@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Renders the login.html page
    Once the user completes the form, we will register
    :return:
    """
    # Creates a new form using the RegisterForm class
    form = LogInForm()

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        found_user = db.session.execute(db.select(User).where(User.email == email)).scalar()

        # If there is a user in the database, then we continue
        if found_user:

            hashed_password = found_user.password

            # Checks if the password is correct with the hashed one
            if check_password_hash(hashed_password, password):
                login_user(found_user)

                return redirect(url_for("index"))

            # If it's not correct, we let the user know
            else:

                flash("The password is not correct!")
                return redirect(url_for("login"))

        # If we couldn't find one, let's make the user know
        else:
            flash("There is no user registered with that email")
            return redirect(url_for("login"))

    return render_template("login.html", form=form, current_user=current_user)


@app.route("/logout")
@login_required
def logout():
    """
    Logs the user out from the website
    :return:
    """
    logout_user()
    return redirect(url_for("index"))


@app.route('/about')
def about():
    """
    Renders about.html file
    :return:
    """
    return render_template("about.html", current_user=current_user)


@app.route('/contact', methods=["GET", "POST"])
def contact():
    """
    Renders contact.html file
    :return:
    """

    message_sent = False

    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]
        message = request.form["message"]

        msg = MIMEMultipart()
        body = f"Name: {name}\nEmail: {email}\nPhone: {phone}\nMessage: {message}"
        msg.attach(MIMEText(body, 'plain'))

        with SMTP(host=HOST, port=PORT) as smtp:
            smtp.starttls()

            smtp.login(user=EMAIL, password=PASSWORD)

            smtp.sendmail(from_addr=EMAIL, to_addrs=EMAIL, msg=msg.as_string())

        message_sent = True

        return render_template("contact.html", message_sent=message_sent, current_user=current_user)

    return render_template("contact.html", message_sent=message_sent, current_user=current_user)


# Start the flask application
if __name__ == "__main__":
    app.run(debug=True)
