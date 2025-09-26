# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask_login import UserMixin

from sqlalchemy.orm import relationship
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin

from apps import db, login_manager
from sqlalchemy import text
from apps.common.util import hash_pass, hash_pin, verify_pin
from pytz import timezone
from datetime import datetime

local_tz = timezone('Asia/Kolkata')  # replace with your local timezone
time_now = datetime.now(local_tz)
get_time_now = time_now.strftime('%Y-%m-%d %H:%M:%S %Z%z')
ACCESS = {

    'super_admin': 1,

    'b2b': 2,
    'merchant': 3,
    'employee': 4,



}

user_roles = db.Table('user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('Users.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True)
)

# Association Table for Roles and Permissions (Defined First)
role_permissions = db.Table('role_permissions',
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True),
    db.Column('permission_id', db.Integer, db.ForeignKey('permissions.id'), primary_key=True)
)


class Users(db.Model, UserMixin):

    __tablename__ = 'Users'

    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(64), unique=True)
    email         = db.Column(db.String(64), unique=True)
    password      = db.Column(db.LargeBinary)
    mobile = db.Column(db.String(10), nullable=False)
    access = db.Column(db.Integer, nullable=False)
    create_on = db.Column(db.DateTime(), nullable=False, default=datetime.now(local_tz))
    user_token = db.Column(db.String(250), index=True, unique=True)
    session_token = db.Column(db.String(250), index=True)
    lock_status = db.Column(db.Boolean, default=True)  # True = Locked, False = Unlocked
    ref = db.Column(db.String(250))
    oauth_github  = db.Column(db.String(100), nullable=True)
    pins = db.relationship('UserPin', backref='user', lazy=True)
    kyc_docs = db.relationship("UserKycDocs", backref="user", lazy=True)
    transactions = db.relationship("Transactions", backref="user", lazy=True)
    transactions_payout = db.relationship("Transactions_payout", backref="user", lazy=True)
    user_contact = db.relationship("UserContact", uselist=False, backref="user")
    #roles = db.relationship('Role', secondary=user_roles, backref=db.backref('users', lazy='dynamic'))
    #new_expanse = db.relationship("Expense", backref="user", lazy=True)
    expenses = db.relationship("Expense", backref="expense_user", lazy=True)
    Attendance = db.relationship("Attendance", backref="attendance_user", lazy=True)
    #roles = db.relationship('Role', secondary=user_roles, backref='users')  # Kept backref only here
    roles = db.relationship('Role', secondary=user_roles, lazy='dynamic', overlaps="users")

    new_phonebook = db.relationship("Phonebook", backref="user_phonebook", lazy=True)

    def is_super_admin(self):
            return self.access == ACCESS['super_admin']

    def is_b2b(self):
        return self.access == ACCESS['b2b']
    def is_merchant(self):
        return self.access == ACCESS['merchant']

    def is_employee(self):
        return self.access == ACCESS['employee']

    def allowed(self, access_level):
        return self.access >= access_level



    def unlock_app(self, pin):
        """Check if the PIN is correct to unlock the app."""
        active_pin = UserPin.query.filter_by(user_id=self.id, is_active=True).first()
        if active_pin and verify_pin(pin, active_pin.pin_hash):
            self.lock_status = False
            db.session.commit()
            return True
        return False

    def lock_app(self):
        """Lock the app and set the lock status to True."""
        self.lock_status = True
        db.session.commit()

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            if hasattr(value, '__iter__') and not isinstance(value, str):
                value = value[0]

            if property == 'password':
                value = hash_pass(value)  # Hash password
            elif property == 'pin':  # Assuming you have a field for the PIN
                value = hash_pin(value)  # Hash PIN

            setattr(self, property, value)

    def __repr__(self):
        return str(self.username)

    def get_associated_merchants(self):
        if self.is_b2b():
            current_user_token = self.user_token
            return Users.query.filter(Users.ref.contains(current_user_token)).limit(7).all()
        return []

    def get_associated_transactions_pay_in(self):
        if self.is_b2b():
            current_user_token = self.user_token
            associated_users = Users.query.filter(Users.ref.contains(current_user_token)).all()
            transactions = Transactions.query.filter(Transactions.user_id.in_([user.id for user in associated_users])).limit(7).all()
            return [{
                'id': transaction.id,
                'username': transaction.user.username,
                'business_name': transaction.user.user_contact.business_name if transaction.user.user_contact else None,
                'first_name': transaction.user.user_contact.firstName if transaction.user.user_contact else None,
                'transaction_amount': transaction.transaction_amount,
                'b_earned_amount': transaction.b_earned_amount,
                'c_earned_amount': transaction.c_earned_amount,
                'claim_status': transaction.claim_status,
                'transaction_date': transaction.transaction_date.strftime('%d %B %Y')
            } for transaction in transactions]


        return []

    def get_associated_transactions_pay_out(self):
        if self.is_b2b():
            current_user_token = self.user_token
            associated_users = Users.query.filter(Users.ref.contains(current_user_token)).all()
            transactions = Transactions_payout.query.filter(Transactions_payout.user_id.in_(
                [user.id for user in associated_users])).limit(7).all()
            return [{
                'id': transaction.id,
                'username': transaction.user.username,
                'business_name': transaction.user.user_contact.business_name if transaction.user.user_contact else None,
                'first_name': transaction.user.user_contact.firstName if transaction.user.user_contact else None,
                'transaction_amount': transaction.transaction_amount,
                'b_earned_amount': transaction.b_earned_amount,
                'c_earned_amount': transaction.c_earned_amount,
                'claim_status': transaction.claim_status,
                'transaction_date': transaction.transaction_date.strftime('%d %B %Y')
            } for transaction in transactions]
            # Corrected to Transactions_payout
        return []

    def get_b2b_associated_transactions_claim_pay_in(self):
        if self.is_b2b():
            current_user_token = self.user_token
            associated_users = Users.query.filter(Users.ref.contains(current_user_token)).all()
            return db.session.query(db.func.sum(Transactions.b_earned_amount)) \
                         .filter(Transactions.user_id.in_([user.id for user in associated_users]),Transactions.claim_status == True).scalar() or 0
        return []

    def get_b2b_associated_transactions_pending_pay_in(self):
        if self.is_b2b():
            current_user_token = self.user_token
            associated_users = Users.query.filter(Users.ref.contains(current_user_token)).all()
            return db.session.query(db.func.sum(Transactions.b_earned_amount)) \
                .filter(Transactions.user_id.in_([user.id for user in associated_users]),
                        Transactions.claim_status == False).scalar() or 0
        return []

    def get_b2b_associated_transactions_claim_pay_out(self):
        if self.is_b2b():
            current_user_token = self.user_token
            associated_users = Users.query.filter(Users.ref.contains(current_user_token)).all()
            return db.session.query(db.func.sum(Transactions_payout.b_earned_amount)) \
                         .filter(Transactions_payout.user_id.in_([user.id for user in associated_users]),Transactions_payout.claim_status == True).scalar() or 0
        return []

    def get_b2b_associated_transactions_pending_pay_out(self):
        if self.is_b2b():
            current_user_token = self.user_token
            associated_users = Users.query.filter(Users.ref.contains(current_user_token)).all()
            return db.session.query(db.func.sum(Transactions_payout.b_earned_amount)) \
                .filter(Transactions_payout.user_id.in_([user.id for user in associated_users]),
                        Transactions_payout.claim_status == False).scalar() or 0
        return []

    def get_merchants_count(self):
        if self.is_b2b():
            current_user_token = self.user_token
            return Users.query.filter(Users.ref.contains(current_user_token)).count()
        return []

    def get_transaction_pay_in_count(self):
        if self.is_b2b():
            current_user_token = self.user_token

            # Query to get associated users based on ref
            associated_users = Users.query.filter(Users.ref.contains(current_user_token)).all()

            # Extract user ids from associated users
            associated_user_ids = [user.id for user in associated_users]

            # Summing the transaction amounts for those users
            total_pay_in = db.session.query(db.func.sum(Transactions.transaction_amount)) \
                .filter(Transactions.user_id.in_(associated_user_ids)).scalar()

            # Return the total sum or 0 if no transactions
            return total_pay_in or 0

        return 0  # Return 0 if the user is not B2B

    def get_transaction_payout_count(self):
        if self.is_b2b():
            current_user_token = self.user_token
            associated_users = Users.query.filter(Users.ref.contains(current_user_token)).all()

            associated_user_ids = [user.id for user in associated_users]
            total_pay_in = db.session.query(db.func.sum(Transactions_payout.transaction_amount)) \
                .filter(Transactions_payout.user_id.in_(associated_user_ids)).scalar()

            # Return the total sum or 0 if no transactions
            return total_pay_in or 0

        return 0  # Return 0 if the user is not B2B

    def get_associated_merchants_all(self):
        if self.is_b2b():
            current_user_token = self.user_token
            return Users.query.filter(Users.ref.contains(current_user_token)).all()
        return []

    def get_associated_transactions_pay_in_all(self):
        if self.is_b2b():
            current_user_token = self.user_token
            associated_users = Users.query.filter(Users.ref.contains(current_user_token)).all()
            transactions = Transactions.query.filter(
                Transactions.user_id.in_([user.id for user in associated_users])).all()
            return [{
                'id': transaction.id,
                'username': transaction.user.username,
                'business_name': transaction.user.user_contact.business_name if transaction.user.user_contact else None,
                'first_name': transaction.user.user_contact.firstName if transaction.user.user_contact else None,
                'transaction_amount': transaction.transaction_amount,
                'b_earned_amount': transaction.b_earned_amount,
                'c_earned_amount': transaction.c_earned_amount,
                'claim_status': transaction.claim_status,
                'transaction_date': transaction.transaction_date.strftime('%d %B %Y')
            } for transaction in transactions]

        return []

    def get_associated_transactions_pay_out_all(self):
        if self.is_b2b():
            current_user_token = self.user_token
            associated_users = Users.query.filter(Users.ref.contains(current_user_token)).all()
            transactions = Transactions_payout.query.filter(Transactions_payout.user_id.in_(
                [user.id for user in associated_users])).all()
            return [{
                'id': transaction.id,
                'username': transaction.user.username,
                'business_name': transaction.user.user_contact.business_name if transaction.user.user_contact else None,
                'first_name': transaction.user.user_contact.firstName if transaction.user.user_contact else None,
                'transaction_amount': transaction.transaction_amount,
                'b_earned_amount': transaction.b_earned_amount,
                'c_earned_amount': transaction.c_earned_amount,
                'claim_status': transaction.claim_status,
                'transaction_date': transaction.transaction_date.strftime('%d %B %Y')
            } for transaction in transactions]
            # Corrected to Transactions_payout
        return []

    def has_permission(self, permission_name):
        """Check if the user has a specific permission"""
        for role in self.roles:
            for perm in role.permissions:
                if perm.name == permission_name:
                    return True
        return False


class Role(db.Model):
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    permissions = db.relationship('Permission', secondary=role_permissions, backref=db.backref('roles', lazy='dynamic'))
    #users = db.relationship('Users', secondary=user_roles, backref=db.backref('roles', lazy='dynamic'))
    #users = db.relationship('Users', secondary=user_roles, lazy='dynamic')  # Removed duplicate backref
    #permissions = db.relationship('Permission', secondary=role_permissions, lazy='dynamic')
    users = db.relationship('Users', secondary=user_roles, lazy='dynamic', overlaps="roles")

    def __repr__(self):
        return f"<Role {self.name}>"


class Permission(db.Model):
    __tablename__ = 'permissions'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return f"<Permission {self.name}>"

class UserContact(db.Model):
    """Personal Details"""

    __tablename__ = "userContact"

    user_id = db.Column(db.Integer, db.ForeignKey('Users.id'), primary_key=True)  # one-to-one
    firstName = db.Column(db.String(50), nullable=False)
    middleName = db.Column(db.String(50))
    lastName = db.Column(db.String(50), nullable=False)
    dob = db.Column(db.Date, nullable=False)  # Date of Birth
    address = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    state = db.Column(db.String(50), nullable=False)
    pincode = db.Column(db.String(6), nullable=False)
    business_name = db.Column(db.String(250), nullable=False)
    profile = db.Column(db.String(250))
    cover_profile = db.Column(db.String(250))
    gender = db.Column(db.String(6), nullable=False)

    # Add c_markup and b_markup columns
    c_markup = db.Column(db.Float, nullable=False, default=0.5)  # Default markup for 'c'
    b_markup = db.Column(db.Float, nullable=False, default=0.5)  # Default markup for 'b'
    c_markup_payout = db.Column(db.Float, nullable=False, default=0.5)  # Default markup for 'c'
    b_markup_payout = db.Column(db.Float, nullable=False, default=0.5)  # Default markup for 'b'
class Transactions(db.Model):
    """Transactions table with markup calculation and transaction date"""

    __tablename__ = 'Transactions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.id'), nullable=False)  # Foreign key to Users
    transaction_amount = db.Column(db.Float, nullable=False)  # Transaction amount
    b_earned_amount = db.Column(db.Float, nullable=False)  # Auto-calculated amount from markup
    c_earned_amount = db.Column(db.Float, nullable=False)  # Auto-calculated amount from markup
    transaction_date = db.Column(db.DateTime, nullable=False, default=datetime.now)  # Date of transaction
    claim_status = db.Column(db.Boolean, default=False)
    trans_token = db.Column(db.String(250), index=True, unique=True)

    def __init__(self, user_id, trans_token, transaction_amount, transaction_date):
        self.user_id = user_id
        self.transaction_amount = transaction_amount
        self.transaction_date = transaction_date  # Automatically set the transaction date to the current time
        self.trans_token = trans_token

        # Get UserContact instance for the user
        user_contact = UserContact.query.filter_by(user_id=user_id).first()
        if user_contact:
            self.b_markup_percentage = user_contact.b_markup
            self.c_markup_percentage = user_contact.c_markup
        else:
            self.b_markup_percentage = 0.5  # Default markup if no user_contact found
            self.c_markup_percentage = 0.5  # Default markup if no user_contact found

        self.b_earned_amount = self.calculate_earned_amount()
        self.c_earned_amount = self.c_calculate_earned_amount()

    def calculate_earned_amount(self):
        """Calculate the earned amount based on the transaction amount and b_markup percentage."""
        return (self.transaction_amount * self.b_markup_percentage) / 100

    def c_calculate_earned_amount(self):
        """Calculate the earned amount based on the transaction amount and c_markup percentage."""
        return (self.transaction_amount * self.c_markup_percentage) / 100

class Transactions_payout(db.Model):
    """Transactions table with markup calculation and transaction date"""

    __tablename__ = 'Transactions_payout'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.id'), nullable=False)  # Foreign key to Users
    transaction_amount = db.Column(db.Float, nullable=False)  # Transaction amount
    b_earned_amount = db.Column(db.Float, nullable=False)  # Auto-calculated amount from markup
    c_earned_amount = db.Column(db.Float, nullable=False)  # Auto-calculated amount from markup
    transaction_date = db.Column(db.DateTime, nullable=False, default=datetime.now)  # Date of transaction
    claim_status = db.Column(db.Boolean, default=False)
    trans_token = db.Column(db.String(250), index=True, unique=True)

    def __init__(self, user_id, trans_token, transaction_amount, transaction_date):
        self.user_id = user_id
        self.transaction_amount = transaction_amount
        self.transaction_date = transaction_date  # Automatically set the transaction date to the current time
        self.trans_token = trans_token

        # Get UserContact instance for the user
        user_contact = UserContact.query.filter_by(user_id=user_id).first()
        if user_contact:
            self.b_markup_percentage_payout = user_contact.b_markup_payout
            self.c_markup_percentage_payout = user_contact.c_markup_payout
        else:
            self.b_markup_percentage_payout = 0.5  # Default markup if no user_contact found
            self.c_markup_percentage_payout = 0.5  # Default markup if no user_contact found

        self.b_earned_amount = self.calculate_earned_amount_payout()
        self.c_earned_amount = self.c_calculate_earned_amount_payout()

    def calculate_earned_amount_payout(self):
        """Calculate the earned amount based on the transaction amount and b_markup percentage."""
        return (self.transaction_amount * self.b_markup_percentage_payout) / 100

    def c_calculate_earned_amount_payout(self):
        """Calculate the earned amount based on the transaction amount and c_markup percentage."""
        return (self.transaction_amount * self.c_markup_percentage_payout) / 100




class CallbackRequest(db.Model):
    __tablename__ = 'CallbackRequest'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    mobile = db.Column(db.String(15), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())


class UserKycDocs(db.Model):
    """KYC Documents associated with a user"""
    __tablename__ = "userKycDocs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.id'), nullable=False)  # One-to-many relationship with Users
    kyc_name = db.Column(db.String(100), nullable=False)  # Name of the KYC document (e.g., PAN, Aadhar, etc.)
    kyc_value = db.Column(db.String(250),
                          nullable=False)  # Value of the KYC document (e.g., PAN number, Aadhar number, etc.)
    kyc_approval = db.Column(db.Boolean, default=False)  # True = Locked, False = Unlocked

    def __init__(self, user_id, kyc_name, kyc_value):
        self.user_id = user_id
        self.kyc_name = kyc_name
        self.kyc_value = kyc_value

    def __repr__(self):
        return f"<KYC {self.kyc_name}: {self.kyc_value}>"
class UserPin(db.Model):
    """Pin model to store hashed user pins and their status."""
    __tablename__ = 'user_pin'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.id'), nullable=False)  # Foreign key to Users
    pin_hash = db.Column(db.LargeBinary)
    is_active = db.Column(db.Boolean, default=False)  # Only one active pin at a time
    created_on = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def __init__(self, user_id, pin, is_active=False):
        self.user_id = user_id
        self.pin_hash = hash_pin(pin)  # Hash the pin
        self.is_active = is_active  # Can now be set explicitly

    def __repr__(self):
        return f"<UserPin {self.id} for User {self.user_id}>"


class Expense(db.Model):
    __tablename__ = 'expenses'

    id = db.Column(db.Integer, primary_key=True)
    trans_type = db.Column(db.String(6), nullable=False)  # Debit or Credit
    amount = db.Column(db.Float, nullable=False)
    remark = db.Column(db.String(255), nullable=True)
    date_of_transaction = db.Column(db.DateTime, default=datetime.now(local_tz))
    user_id = db.Column(db.Integer, db.ForeignKey('Users.id'), nullable=False)  # Foreign key to Users
    # Relationship to Users (Each Expense Belongs to One User)
    user = db.relationship("Users", backref="user_expenses")  # Change backref name to avoid conflict


    def __repr__(self):
        return f"<Expense {self.trans_type} - {self.amount}>"


class Phonebook(db.Model):
    __tablename__ = 'Phonebook'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    number = db.Column(db.String(15), nullable=False)
    company_name = db.Column(db.String(100), nullable=True)
    address = db.Column(db.String(200), nullable=True)
    create_date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.id'), nullable=False)  # Foreign key to Users
    user = db.relationship('Users', backref='user_phonebook')

"""
class B2BMerchantMapping(db.Model):
    __tablename__ = 'b2b_merchant_mapping'

    id = db.Column(db.Integer, primary_key=True)
    b2b_user_id = db.Column(db.Integer, db.ForeignKey('Users.id'), nullable=False)
    merchant_user_id = db.Column(db.Integer, db.ForeignKey('Users.id'), nullable=False)

    b2b_user = db.relationship("Users", foreign_keys=[b2b_user_id], backref="mapped_merchants")
    merchant_user = db.relationship("Users", foreign_keys=[merchant_user_id], backref="b2b_mapped_to")

    def __repr__(self):
        return f"B2B User {self.b2b_user.username} -> Merchant {self.merchant_user.username}"""


@login_manager.user_loader
def user_loader(id):
    return Users.query.filter_by(id=id).first()


@login_manager.request_loader
def request_loader(request):
    username = request.form.get('username')
    user = Users.query.filter_by(username=username).first()
    return user if user else None

class OAuth(OAuthConsumerMixin, db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey("Users.id", ondelete="cascade"), nullable=False)
    user = db.relationship(Users)


class OTP(db.Model):
    __tablename__ = 'otp'
    id = db.Column(db.Integer, primary_key=True)
    otp_code = db.Column(db.String(6), nullable=False, unique=True)
    generated_at = db.Column(db.DateTime, default=datetime.now(local_tz))
    is_active = db.Column(db.Boolean, default=True)

class Attendance(db.Model):
    __tablename__ = 'attendance'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.id'), nullable=False)  # Foreign key to Users

    #user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, default=datetime.now(local_tz), unique=False)
    punch_in = db.Column(db.DateTime, nullable=True)
    punch_out = db.Column(db.DateTime, nullable=True)
    total_hours = db.Column(db.Interval, nullable=True)
    remark = db.Column(db.String(50), default="Absent")
    otp_used = db.Column(db.String(6), nullable=True)

    user = db.relationship('Users', backref=db.backref('attendances', lazy=True))

# Admin data tables start form here
class Invoice(db.Model):
    __tablename__ = 'invoice'

    id = db.Column(db.Integer, primary_key=True)
    invoice_type = db.Column(db.String(20), nullable=False)
    invoice_no = db.Column(db.String(50), unique=True, nullable=False)
    invoice_date = db.Column(db.Date, nullable=False)
    payment_status = db.Column(db.String(10), nullable=False, default='Pending')  # New Column


    company_name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text, nullable=False)
    state = db.Column(db.String(100), nullable=False)
    pincode = db.Column(db.String(10), nullable=False)
    mobile_number = db.Column(db.String(15), nullable=False)
    bill_to_date = db.Column(db.Date, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    gstin = db.Column(db.String(20), nullable=False)

    subtotal = db.Column(db.Float, nullable=False)
    sgst_rate = db.Column(db.Float, nullable=False, default=0)
    cgst_rate = db.Column(db.Float, nullable=False, default=0)
    igst_rate = db.Column(db.Float, nullable=False, default=0)
    total_tax = db.Column(db.Float, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)

    items = db.relationship('InvoiceItem', backref='invoice', cascade="all, delete", lazy=True)


class InvoiceItem(db.Model):
    __tablename__ = 'invoice_item'

    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=False)
    description = db.Column(db.Text, nullable=False)
    hsn_sac_code = db.Column(db.String(20), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    rate = db.Column(db.Float, nullable=False)
    amount = db.Column(db.Float, nullable=False)