from flask_ckeditor import CKEditorField
from flask_wtf import FlaskForm
from wtforms.fields.simple import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired, URL, Email


class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    name = StringField("Name")
    submit = SubmitField()


class LogInForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField()


class PostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Blog Post Subtitle", validators=[DataRequired()])
    img_url = StringField("The Image URL for your Blog", validators=[DataRequired(), URL()])
    body = CKEditorField("Body", validators=[DataRequired()])
    submit = SubmitField()


class CommentForm(FlaskForm):
    comment = CKEditorField("Leave a comment", validators=[DataRequired()])
    submit = SubmitField()
