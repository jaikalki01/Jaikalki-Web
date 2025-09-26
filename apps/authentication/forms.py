# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""


from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Email, ValidationError, Regexp
from apps.common.models import *
  # Assuming you have a User model for your users
# login and registration


class LoginForm(FlaskForm):
    username = StringField('Username',
                         id='username_login',
                         validators=[DataRequired()])
    password = PasswordField('Password',
                             id='pwd_login',
                             validators=[DataRequired()])




class CreateAccountForm(FlaskForm):
    username = StringField('Username', id='username_create', validators=[DataRequired()])
    email = StringField('Email', id='email_create', validators=[DataRequired(), Email()])
    mobile = StringField('Mobile', validators=[DataRequired()])
    password = PasswordField('Password', id='pwd_create', validators=[
        DataRequired(),
        Regexp(r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{6,}$',
               message='Password must be at least 6 characters long and include at least one letter, one number, and one special character.')
    ])

    def validate_username(self, username):
        # Check if the username is unique in the database
        user = Users.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('This username is already taken. Please choose a different one.')

    def validate_email(self, email):
        # Check if the email is unique in the database
        user = Users.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('This email is already registered. Please choose a different one.')

    def validate_mobile(self, mobile):
        # Check if the mobile number is unique in the database
        user = Users.query.filter_by(mobile=mobile.data).first()
        if user:
            raise ValidationError('This mobile number is already registered. Please choose a different one.')


