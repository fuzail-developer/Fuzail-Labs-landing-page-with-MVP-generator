from flask import Blueprint, render_template, redirect, url_for, flash
from .forms import OrderForm
from .models import ProjectRequest
from . import db

bp = Blueprint('main', __name__)

@bp.route('/')
def home():
    return render_template('index.html')

@bp.route('/order', methods=['GET', 'POST'])
def order():
    form = OrderForm()
    if form.validate_on_submit():
        project_request = ProjectRequest(
            name=form.name.data,
            email=form.email.data,
            project_idea=form.project_idea.data,
            preferred_framework=form.preferred_framework.data,
            database_choice=form.database_choice.data,
            preferred_plan=form.preferred_plan.data
        )
        db.session.add(project_request)
        db.session.commit()
        flash('Your project idea has been submitted!', 'success')
        return redirect(url_for('main.home'))
    return render_template('order.html', form=form)