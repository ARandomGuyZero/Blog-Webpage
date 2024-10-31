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
from flask_ckeditor import CKEditor, CKEditorField
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from werkzeug.utils import redirect
from wtforms.fields.simple import StringField, SubmitField
from wtforms.validators import DataRequired, URL

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


class PostForm(FlaskForm):
    title = StringField("Blog Post Title:", validators=[DataRequired()])
    subtitle = StringField("Blog Post Subtitle:", validators=[DataRequired()])
    author = StringField("Your Name:", validators=[DataRequired()])
    img_url = StringField("The Image URL for your Blog:", validators=[DataRequired(), URL()])
    body = CKEditorField("Body:", validators=[DataRequired()])
    submit = SubmitField()


# CONFIGURE TABLE
class BlogPost(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str] = mapped_column(String(250), nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)


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
    form = PostForm()

    # If the user clicks on submit
    if request.method == "POST":
        # Gets the server date in a formatted code
        date = datetime.now().strftime("%m %d, %Y")
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

    return render_template("make-post.html", form=form)


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
