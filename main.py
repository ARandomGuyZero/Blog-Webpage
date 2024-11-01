"""
Blog Webpage

Author: Alan
Date: October 16th 2024

This application uses Flask to show a webpage that uses Bootstrap for design and a json for the data.
"""
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from smtplib import SMTP

from flask import Flask, render_template, request, url_for
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from werkzeug.security import generate_password_hash
from werkzeug.utils import redirect

from forms import PostForm, RegisterForm

EMAIL = "email@gmail.com"  # Your email
PASSWORD = "password"  # Your password
HOST = "smtp.gmail.com"  # I use gmail's smtp, may change depending on your email provider
PORT = 587

# Sets a post list empty
post_list = []

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
ckeditor = CKEditor(app)
Bootstrap5(app)


# CREATE DATABASE
class Base(DeclarativeBase):
    pass


# Were we will save the data
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)


# CONFIGURE TABLE
class BlogPost(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str] = mapped_column(String(250), nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)


class User(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(250), nullable=False)
    name: Mapped[str] = mapped_column(String(250), nullable=False)


with app.app_context():
    db.create_all()


@app.route('/')
def index():
    """
    Renders index.html file
    :return:
    """
    blogposts = db.session.execute(db.select(BlogPost)).scalars().all()
    return render_template("index.html", posts=blogposts)


@app.route('/post/<int:index_number>')
def post(index_number):
    """
    Renders post.html file using an index number to post a certain post.
    :param index_number:
    :return:
    """

    blogpost = db.get_or_404(BlogPost, index_number)
    return render_template("post.html", post=blogpost)


@app.route("/new-post", methods=["GET", "POST"])
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
            author=request.form.get("author"),
            img_url=request.form.get("img_url"),
        )
        # Adds the new row to the database
        db.session.add(new_post)

        # Saves changes
        db.session.commit()

        return redirect(url_for("index"))

    return render_template("make-post.html", is_new_post=is_new_post, form=form)


@app.route("/edit-post/<int:index_number>", methods=["GET", "POST "])
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
        author=blogpost.author,
        body=blogpost.body
    )

    is_new_post = False

    # If the user clicks on submit
    if request.method == "POST":
        # Creates a new post using the form's data
        blogpost.title = request.form.get("title")
        blogpost.subtitle = request.form.get("subtitle")
        blogpost.body = request.form.get("body")
        blogpost.author = request.form.get("author")
        blogpost.img_url = request.form.get("img_url")

        # Saves changes
        db.session.commit()

        return redirect(url_for("index"))

    return render_template("make-post.html", is_new_post=is_new_post, form=form)


@app.route("/delete/<int:index_number>")
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
    # Creates a new form using the UserForm class
    form = RegisterForm()
    if request.method == "POST":
        # Generate a password using a hashed method
        hashed_password = generate_password_hash(request.form.get("password"), method="pbkdf2:sha256", salt_length=8)

        new_user = User(
            email=request.form.get("email"),
            password=hashed_password,
            name=request.form.get("name")
        )

        # Add a new user to the database
        db.session.add(new_user)

        # Save the data to the database
        db.session.commit()

        return redirect(url_for("index"))

    return render_template("register.html", form=form)


@app.route('/about')
def about():
    """
    Renders about.html file
    :return:
    """
    return render_template("about.html")


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

        return render_template("contact.html", message_sent=message_sent)

    return render_template("contact.html", message_sent=message_sent)


# Start the flask application
if __name__ == "__main__":
    app.run(debug=True)
