from flask_wtf import FlaskForm
from wtforms import RadioField
from wtforms.validators import DataRequired

class VoteForm(FlaskForm):
	vote = RadioField('Label', choices=[])