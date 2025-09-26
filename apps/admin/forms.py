from wtforms.fields.form import FormField
from wtforms.fields.list import FieldList
from wtforms.fields.numeric import IntegerField
from wtforms.fields.simple import TextAreaField
from wtforms.validators import DataRequired, Length, ValidationError, NumberRange, InputRequired, Regexp

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField, DateField, FloatField
from wtforms.validators import DataRequired, Email, ValidationError
from apps.common.models import  UserPin, hash_pin, ACCESS, Users  # Your User model
import uuid
import re
from wtforms.validators import Optional
#from apps.authentication.util import *
from datetime import datetime

class PinForm(FlaskForm):
    pin = PasswordField('Enter your 6-digit PIN', validators=[
        DataRequired(),
        Length(min=6, max=6, message="PIN must be exactly 6 digits."),
        Regexp('^\d{6}$', message="PIN must be numeric and exactly 6 digits.")
    ])

    def validate_pin(self, field):
        # Check if the new pin matches any previous pin for the user
        existing_pin = UserPin.query.filter_by(pin_hash=hash_pin(field.data)).first()
        if existing_pin:
            raise ValidationError('This PIN has already been used, please choose a different one.')

    submit = SubmitField('Submit')

class UserContactForm(FlaskForm):
    firstName = StringField('First Name', validators=[DataRequired(), Length(max=50)])
    middleName = StringField('Middle Name', validators=[Length(max=50)])
    lastName = StringField('Last Name', validators=[DataRequired(), Length(max=50)])
    dob = DateField('Date of Birth', format='%Y-%m-%d', validators=[DataRequired()])
    address = StringField('Address', validators=[DataRequired(), Length(max=255)])
    city = StringField('City', validators=[DataRequired(), Length(max=50)])
    state = StringField('State', validators=[DataRequired(), Length(max=50)])
    pincode = StringField('Pincode', validators=[DataRequired(), Length(min=6, max=6)])
    business_name = StringField('Division Name', validators=[DataRequired(), Length(max=250)])
    #b_markup_percentage = FloatField('B2B Markup Percentage PayIn',
    #                                 validators=[InputRequired(), NumberRange(min=0.0, max=100.0)])
    #c_markup_percentage = FloatField('Business Markup Percentage PayIn',
    #                                 validators=[InputRequired(), NumberRange(min=0.0, max=100.0)])
    #b_markup_percentage_payout = FloatField('B2B Markup Percentage PayOut',
    #                                 validators=[InputRequired(), NumberRange(min=0.0, max=100.0)])
    #c_markup_percentage_payout = FloatField('Business Markup Percentage PayOut',
    #                                validators=[InputRequired(), NumberRange(min=0.0, max=100.0)])
    gender = SelectField('Gender', choices=[('Male', 'Male'), ('Female', 'Female'), ('Transgender', 'Transgender')],
                         validators=[DataRequired()])
    submit = SubmitField('Add Details')

    def validate_dob(form, field):
        today = datetime.today().date()
        age = today.year - field.data.year - ((today.month, today.day) < (field.data.month, field.data.day))
        if age < 18:
            raise ValidationError('You must be at least 18 years old.')

class TransactionForm(FlaskForm):
    transaction_amount = FloatField('Transaction Amount', validators=[DataRequired(), NumberRange(min=0.01)])
    transaction_date = DateField('Transaction Date', format='%Y-%m-%d', validators=[DataRequired()])  # Date input
    submit = SubmitField('Submit Transaction')




class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    mobile = StringField('Mobile', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])

    access = SelectField('Access Level', choices=[(1, 'Super Admin'),  (4, 'Employee')],
                         coerce=int, validators=[DataRequired()])
    b2b_user = SelectField('Keep Blank', choices=[], coerce=str, validators=[Optional()])

    submit = SubmitField('Register')

    def __init__(self, user=None, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)

        # Fetch all B2B users and populate the choices dynamically
        b2b_users = Users.query.filter_by(access=ACCESS['b2b']).all()

        # Add "None" as the default option
        self.b2b_user.choices = [('', '')] + [(user.user_token, user.username) for user in b2b_users]

        if user:
            self.username.data = user.username
            self.email.data = user.email
            self.mobile.data = user.mobile
            self.access.data = user.access
            self.b2b_user.data = user.ref if user.ref else ''
    """def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)

        # Fetch all B2B users and populate the choices dynamically
        #with app.app_context():
        b2b_users = Users.query.filter_by(access=ACCESS['b2b']).all()

        # Add "None" as the default option
        self.b2b_user.choices = [('', '')] + [(user.user_token, user.username) for user in b2b_users]"""
    # Custom validation methods for uniqueness
    def validate_username(self, username):
        if Users.query.filter_by(username=username.data).first():
            raise ValidationError('This username is already in use.')

    def validate_email(self, email):
        if Users.query.filter_by(email=email.data).first():
            raise ValidationError('This email is already in use.')

    def validate_mobile(self, mobile):
        mobile_data = mobile.data
        # Check for uniqueness
        if Users.query.filter_by(mobile=mobile_data).first():
            raise ValidationError('This mobile number is already registered.')
        # Check for exactly 10 digits
        if len(mobile_data) != 10 or not mobile_data.isdigit():
            raise ValidationError('Mobile number must be exactly 10 digits.')


    def validate_password(self, password):
        password_data = password.data
        if len(password_data) < 6:
            raise ValidationError('Password must be at least 6 characters long.')
        if not re.search(r"[A-Za-z]", password_data):
            raise ValidationError('Password must contain at least one letter.')
        if not re.search(r"[0-9]", password_data):
            raise ValidationError('Password must contain at least one number.')
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password_data):
            raise ValidationError('Password must contain at least one special character.')

class EditForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    mobile = StringField('Mobile', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])

    access = SelectField('Access Level', choices=[(1, 'Super Admin'), (4, 'Employee')],
                         coerce=int, validators=[DataRequired()])
    b2b_user = SelectField('B2B User', choices=[], coerce=str, validators=[Optional()])

    submit = SubmitField('Register')

    def __init__(self, user=None, *args, **kwargs):
        super(EditForm, self).__init__(*args, **kwargs)

        # Fetch all B2B users and populate the choices dynamically
        b2b_users = Users.query.filter_by(access=ACCESS['b2b']).all()

        # Add "None" as the default option
        self.b2b_user.choices = [('', '')] + [(user.user_token, user.username) for user in b2b_users]

        if user:
            self.username.data = user.username
            self.email.data = user.email
            self.mobile.data = user.mobile
            self.access.data = user.access
            self.b2b_user.data = user.ref if user.ref else ''
    """def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)

        # Fetch all B2B users and populate the choices dynamically
        #with app.app_context():
        b2b_users = Users.query.filter_by(access=ACCESS['b2b']).all()

        # Add "None" as the default option
        self.b2b_user.choices = [('', '')] + [(user.user_token, user.username) for user in b2b_users]"""
    # Custom validation methods for uniqueness


    def validate_mobile(self, mobile):
        mobile_data = mobile.data
        # Check for uniqueness

        # Check for exactly 10 digits
        if len(mobile_data) != 10 or not mobile_data.isdigit():
            raise ValidationError('Mobile number must be exactly 10 digits.')


    def validate_password(self, password):
        password_data = password.data
        if len(password_data) < 6:
            raise ValidationError('Password must be at least 6 characters long.')
        if not re.search(r"[A-Za-z]", password_data):
            raise ValidationError('Password must contain at least one letter.')
        if not re.search(r"[0-9]", password_data):
            raise ValidationError('Password must contain at least one number.')
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password_data):
            raise ValidationError('Password must contain at least one special character.')


class PasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[Optional()])
    submit = SubmitField('Update Password')

    def validate_password(self, password):
        password_data = password.data
        if len(password_data) < 6:
            raise ValidationError('Password must be at least 6 characters long.')
        if not re.search(r"[A-Za-z]", password_data):
            raise ValidationError('Password must contain at least one letter.')
        if not re.search(r"[0-9]", password_data):
            raise ValidationError('Password must contain at least one number.')
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password_data):
            raise ValidationError('Password must contain at least one special character.')


class B2BUserForm(FlaskForm):
    b2b_user = SelectField('B2B User', choices=[], coerce=str, validators=[Optional()])
    submit = SubmitField('Update B2B User')
    remove = SubmitField('Remove B2B User')

    def __init__(self, user=None, *args, **kwargs):
        super(B2BUserForm, self).__init__(*args, **kwargs)

        # Fetch all B2B users
        b2b_users = Users.query.filter_by(access=2).all()

        # Create a list of choices for the SelectField
        self.b2b_user.choices = [(user.user_token, user.username) for user in b2b_users]

        # Pre-select the current B2B user if available
        if user and user.ref:  # Check if user has a reference
            assigned_b2b_user = Users.query.filter_by(user_token=user.ref).first()
            if assigned_b2b_user:
                # Set the default to the current B2B user's token and ensure it appears in the choices
                self.b2b_user.default = assigned_b2b_user.user_token

        # Add "None" as the default option
        self.b2b_user.choices.insert(0, ('', 'Select a B2B User'))  # Optional "Select" option






class UserDetailsForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    mobile = StringField('Mobile', validators=[DataRequired()])
    access = SelectField('Access Level', choices=[(1, 'Super Admin'), (4, 'Employee')],
                         coerce=int, validators=[DataRequired()])
    submit = SubmitField('Update Details')
class ExpenseForm(FlaskForm):
    trans_type = SelectField(
        'Transaction Type',
        choices=[('Credit', 'Credit'), ('Debit', 'Debit')],
        validators=[DataRequired()]
    )
    amount = FloatField('Amount', validators=[DataRequired(), NumberRange(min=0.01, message="Amount must be greater than 0")])
    remark = TextAreaField('Remark', validators=[DataRequired()])
    date_of_transaction = DateField('Date of Transaction', format='%Y-%m-%d', default=datetime.today, validators=[DataRequired()])
    submit = SubmitField('Submit Transaction')

class PhonebookForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=100)])
    number = StringField('Number', validators=[DataRequired(), Regexp(r'^\d{10,15}$', message="Enter a valid number")])
    company_name = StringField('Company Name', validators=[Length(max=100)])
    address = TextAreaField('Address', validators=[Length(max=200)])
    submit = SubmitField('Save')

class CreateUserForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(),
        Length(max=10, message="Username must be less than 10 characters"),
        Regexp('^[a-z]+$', message="Username can only contain lowercase letters (a-z) with no numbers or special characters.")
    ])
    password = PasswordField('Password', validators=[DataRequired()])

class AssignPermissionForm(FlaskForm):
    role_id = SelectField('Role', coerce=int, validators=[DataRequired()])
    permission_id = SelectField('Permission', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Assign Permission')

class RoleForm(FlaskForm):
    name = StringField('Role Name', validators=[DataRequired()])
    submit = SubmitField('Create Role')

# Form to create a new permission
class PermissionForm(FlaskForm):
    names= StringField('Permission Name', validators=[DataRequired()])
    submit = SubmitField('Create Permission')

# Form to assign a role to a user
class AssignRoleForm(FlaskForm):
    user_id = SelectField('User', coerce=int, validators=[DataRequired()])
    role_id = SelectField('Role', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Assign Role')


# Admin forms start from here
class InvoiceItemForm(FlaskForm):
    description = StringField('Description', validators=[DataRequired()])
    hsn_sac_code = StringField('HSN/SAC Code', validators=[DataRequired()])
    quantity = IntegerField('Quantity', validators=[DataRequired()])
    rate = FloatField('Rate', validators=[DataRequired()])
    amount = FloatField('Amount', validators=[DataRequired()])

class InvoiceForm(FlaskForm):
    invoice_type = SelectField('Invoice Type', choices=[('proforma', 'Proforma Invoice'), ('tax', 'Tax Invoice')], validators=[DataRequired()])
    invoice_no = StringField('Invoice No', validators=[DataRequired(), Length(max=50)])
    invoice_date = DateField('Invoice Date', validators=[DataRequired()])
    #payment_status = SelectField('Payment Status', choices=[('Pending', 'Pending'), ('Paid', 'Paid')],validators=[DataRequired()])


    company_name = StringField('Company Name', validators=[DataRequired()])
    address = StringField('Address', validators=[DataRequired()])
    state = StringField('State', validators=[DataRequired()])
    pincode = StringField('Pincode', validators=[DataRequired()])
    mobile_number = StringField('Mobile Number', validators=[DataRequired()])
    bill_to_date = DateField('Bill to Date', validators=[DataRequired()])
    due_date = DateField('Due Date', validators=[DataRequired()])
    gstin = StringField('GSTIN', validators=[DataRequired()])

    subtotal = FloatField('Subtotal', validators=[DataRequired()])
    sgst_rate = FloatField('SGST (%)', validators=[InputRequired()])  # Fixed
    cgst_rate = FloatField('CGST (%)', validators=[InputRequired()])  # Fixed
    igst_rate = FloatField('IGST (%)', validators=[InputRequired()])  # Fixed
    total_tax = FloatField('Total Tax', validators=[DataRequired()])
    total_amount = FloatField('Total Amount After Tax', validators=[DataRequired()])

    items = FieldList(FormField(InvoiceItemForm), min_entries=1)
    submit = SubmitField('Submit Invoice')