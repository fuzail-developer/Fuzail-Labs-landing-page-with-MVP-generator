from app import db

class ProjectRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    project_idea = db.Column(db.Text, nullable=False)
    preferred_framework = db.Column(db.String(50), nullable=False)
    database_choice = db.Column(db.String(50), nullable=False)
    preferred_plan = db.Column(db.String(50), nullable=False)