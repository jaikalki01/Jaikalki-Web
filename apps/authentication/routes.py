# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask import render_template, redirect, request, url_for
from flask_login import (
    current_user,
    login_user,
    logout_user
)
import uuid
from flask_dance.contrib.github import github

from apps import db, login_manager
from apps.authentication import blueprint
from apps.authentication.forms import LoginForm, CreateAccountForm
from apps.common.models import Users, ACCESS
from sqlalchemy import or_
from apps.common.util import verify_pass


    #return redirect(url_for('authentication_blueprint.login'))

# Login & Registration

@blueprint.route("/github")
def login_github():
    """ Github login """
    if not github.authorized:
        return redirect(url_for("github.login"))

    res = github.get("/user")
    return redirect(url_for('home_blueprint.index'))

@blueprint.route('/login', methods=['GET', 'POST'])
def login():

    login_form = LoginForm(request.form)
    if 'login' in request.form:

        # read form data
        username = request.form['username']
        password = request.form['password']

        # Locate user
        user = Users.query.filter(
            Users.username == username,
            or_(Users.access == ACCESS['super_admin'], Users.access == ACCESS['employee'])
        ).first()
        # Check the password
        if user and verify_pass(password, user.password):

            login_user(user)
            return redirect(url_for('admin_blueprint.dashboard'))

        # Something (user or pass) is not ok
        return render_template('accounts/login.html',
                               msg='Wrong user or password',
                               form=login_form)

    if not current_user.is_authenticated:
        return render_template('accounts/login.html',
                               form=login_form)
    return redirect(url_for('admin_blueprint.dashboard'))


"""@blueprint.route('/register', methods=['GET', 'POST'])
def register():
    create_account_form = CreateAccountForm(request.form)

    if 'register' in request.form:
        username = request.form['username']
        email = request.form['email']
        #business_name = request.form['business_name']
        token = str(uuid.uuid4())
        # Check if username exists
        user = Users.query.filter_by(username=username).first()
        if user:
            return render_template('accounts/register.html',
                                   msg='Username already registered',
                                   success=False,
                                   form=create_account_form)

        # Check if email exists
        user = Users.query.filter_by(email=email).first()
        if user:
            return render_template('accounts/register.html',
                                   msg='Email already registered',
                                   success=False,
                                   form=create_account_form)
       
        # Create the new user
        user = Users(**request.form, access=1, user_token=token)
        db.session.add(user)
        db.session.commit()

        # Log out the user after successful registration
        logout_user()

        return render_template('accounts/register.html',
                               msg='Account created successfully.',
                               success=True,
                               form=create_account_form)

    else:
        return render_template('accounts/register.html', form=create_account_form)"""



@blueprint.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('authentication_blueprint.login'))


# Errors

@login_manager.unauthorized_handler
def unauthorized_handler():
    return render_template('admin/page-403.html'), 403


@blueprint.errorhandler(403)
def access_forbidden(error):
    return render_template('admin/page-403.html'), 403


@blueprint.errorhandler(404)
def not_found_error(error):
    return render_template('admin/page-404.html'), 404


@blueprint.errorhandler(500)
def internal_error(error):
    return render_template('admin/page-500.html'), 500
