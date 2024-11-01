from flask import Flask, render_template, request, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, current_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import redirect

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret-key-goes-here'


# CREATE DATABASE


class Base(DeclarativeBase):
    pass


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)


# Create a user_loader callback
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, user_id)


# CREATE TABLE IN DB


class User(UserMixin, db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(1000))


with app.app_context():
    db.create_all()


@app.route('/')
def home():
    return render_template("index.html", logged_in=current_user.is_authenticated)


@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Gets the Data from the form
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")

        # Find the user
        user = db.session.execute(db.select(User).where(email == email)).scalar()

        if user:
            flash('This user already exists')
            return redirect(url_for('login'))
        else:
            # Generate a new hash
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)

            new_user = User(
                name=name,
                email=email,
                password=hashed_password
            )

            # Add new user
            db.session.add(new_user)
            # Save changes
            db.session.commit()

            return redirect(url_for("secrets", name=name))

    return render_template("register.html", logged_in=current_user.is_authenticated)


@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        # Find the user
        user = db.session.execute(db.select(User).where(email == email)).scalar()

        if user:

            hashed_password = user.password

            if check_password_hash(hashed_password, password):
                login_user(user)

                name = user.name

                return redirect(url_for("secrets", name=name))

            else:
                flash('Your password is incorrect')
                return redirect(url_for('login'))

        else:
            flash('Your email does not exist in the database')
            return redirect(url_for('login'))

    return render_template("login.html", logged_in=current_user.is_authenticated)


@app.route('/secrets')
def secrets():
    name = request.args.get('name')
    return render_template("secrets.html", name=name, logged_in=True)


@app.route('/logout')
def logout():
    pass


@app.route('/download')
def download():
    pass


if __name__ == "__main__":
    app.run(debug=True)
