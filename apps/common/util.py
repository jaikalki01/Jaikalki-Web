# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import os
import hashlib
import binascii
import random
from functools import wraps

from flask import flash, redirect, url_for
from flask_login import current_user

#from apps.admin.forms import *
from apps.common.models import *
from apps import db

# Inspiration -> https://www.vitoshacademy.com/hashing-passwords-in-python/

def permission_required(permission):
    """Decorator to check if user has a specific permission"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.has_permission(permission):
                flash("You do not have permission to access this page.", "danger")
                return redirect(url_for('admin_blueprint.dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def hash_pass(password):
    """Hash a password for storing."""

    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
    pwdhash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'),
                                  salt, 100000)
    pwdhash = binascii.hexlify(pwdhash)
    return (salt + pwdhash)  # return bytes

def hash_pin(pin):
    """Hash a password for storing."""

    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
    pwdhash = hashlib.pbkdf2_hmac('sha512', pin.encode('utf-8'),
                                  salt, 100000)
    pwdhash = binascii.hexlify(pwdhash)
    return (salt + pwdhash)  # return bytes


def verify_pass(provided_password, stored_password):
    """Verify a stored password against one provided by user"""

    stored_password = stored_password.decode('ascii')
    salt = stored_password[:64]
    stored_password = stored_password[64:]
    pwdhash = hashlib.pbkdf2_hmac('sha512',
                                  provided_password.encode('utf-8'),
                                  salt.encode('ascii'),
                                  100000)
    pwdhash = binascii.hexlify(pwdhash).decode('ascii')
    return pwdhash == stored_password


def verify_pin(provided_pin, stored_pin):
    """Verify a stored password against one provided by user"""

    stored_password = stored_pin.decode('ascii')
    salt = stored_password[:64]
    stored_password = stored_password[64:]
    pwdhash = hashlib.pbkdf2_hmac('sha512',
                                  provided_pin.encode('utf-8'),
                                  salt.encode('ascii'),
                                  100000)
    pwdhash = binascii.hexlify(pwdhash).decode('ascii')
    return pwdhash == stored_password


def get_total_users_by_access(access_level):
    """Fetch total users based on access level."""
    return Users.query.filter_by(access=access_level).count()

def get_earned_amounts_by_claim_status(claim_status):
    """Fetch total earned amounts (b and c) based on claim status."""
    total_b_earned = db.session.query(db.func.sum(Transactions.b_earned_amount)) \
                               .filter(Transactions.claim_status == claim_status).scalar() or 0
    total_c_earned = db.session.query(db.func.sum(Transactions.c_earned_amount)) \
                               .filter(Transactions.claim_status == claim_status).scalar() or 0
    return {'total_b_earned': total_b_earned, 'total_c_earned': total_c_earned}

def get_transaction_list(limit=7):
    """Fetch a list of recent transactions."""
    transactions = Transactions.query.order_by(Transactions.id.desc()).limit(limit).all()
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

def get_total_transactions():
    """Fetch the total transaction amount."""
    return db.session.query(db.func.sum(Transactions.transaction_amount)).scalar() or 0

def get_total_transactions_payout():
    """Fetch total payout transaction amounts."""
    return db.session.query(db.func.sum(Transactions_payout.transaction_amount)).scalar() or 0

def get_total_earned_payout_by_claim_status(claim_status):
    """Fetch total earned payout amounts (b and c) based on claim status."""
    total_b_earned = db.session.query(db.func.sum(Transactions_payout.b_earned_amount)) \
                               .filter(Transactions_payout.claim_status == claim_status).scalar() or 0
    total_c_earned = db.session.query(db.func.sum(Transactions_payout.c_earned_amount)) \
                               .filter(Transactions_payout.claim_status == claim_status).scalar() or 0
    return {'total_b_earned': total_b_earned, 'total_c_earned': total_c_earned}

def get_users_list_by_access(access_level, limit=7):
    """Fetch a list of users based on access level."""
    return Users.query.filter_by(access=access_level).order_by(Users.id.desc()).limit(limit).all()


def generate_math_problem(_):
    num1 = random.randint(1, 10)
    num2 = random.randint(1, 10)
    correct_answer = num1 + num2
    return {"num1": num1, "num2": num2, "correct_answer": correct_answer}

