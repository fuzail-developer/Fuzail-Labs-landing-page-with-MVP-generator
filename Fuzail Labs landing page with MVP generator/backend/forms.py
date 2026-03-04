from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, Length

class OrderForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    project_idea = TextAreaField('Project Idea', validators=[DataRequired()])
    preferred_framework = SelectField('Preferred Framework', choices=[('Flask', 'Flask'), ('FastAPI', 'FastAPI'), ('Django', 'Django')])
    database_choice = SelectField('Database Choice', choices=[('SQLite', 'SQLite'), ('PostgreSQL', 'PostgreSQL'), ('MySQL', 'MySQL'), ('Supabase', 'Supabase')])
    preferred_plan = SelectField('Preferred Plan', choices=[('Basic', 'Basic'), ('Startup', 'Startup'), ('Full SaaS', 'Full SaaS')])
    submit = SubmitField('Submit')