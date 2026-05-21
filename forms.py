from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired


class PhotoForm(FlaskForm):
    photo = FileField(validators=[FileRequired()])


class ManualForm(FlaskForm):
    manual = FileField(validators=[FileRequired()])
