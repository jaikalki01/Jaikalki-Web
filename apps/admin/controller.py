# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""


from apps.admin.forms import *
from apps.common.models import *
from apps import db
from datetime import datetime, date
from sqlalchemy import func, and_
from sqlalchemy import or_
# Inspiration -> https://www.vitoshacademy.com/hashing-passwords-in-python/

"""def total_balance():
    total_credit = db.session.query(db.func.sum(Expense.amount)).filter_by(trans_type='Credit').scalar() or 0
    total_debit = db.session.query(db.func.sum(Expense.amount)).filter_by(trans_type='Debit').scalar() or 0
    return total_credit - total_debit"""

def total_balance(user_id=None):
    query_credit = db.session.query(func.sum(Expense.amount)).filter_by(trans_type='Credit')
    query_debit = db.session.query(func.sum(Expense.amount)).filter_by(trans_type='Debit')

    if user_id:
        query_credit = query_credit.filter_by(user_id=user_id)
        query_debit = query_debit.filter_by(user_id=user_id)

    total_credit = query_credit.scalar() or 0
    total_debit = query_debit.scalar() or 0

    return total_credit - total_debit

def total_received_fund(user_id=None):
    total_credit = db.session.query(db.func.sum(Expense.amount)).filter_by(trans_type='Credit')

    if user_id:
        total_credit= total_credit.filter_by(user_id=user_id)

    total_credits = total_credit.scalar() or 0
    return total_credits


def total_expense(user_id=None):
    total_debit = db.session.query(db.func.sum(Expense.amount)).filter_by(trans_type='Debit')

    if user_id:
        total_debit = total_debit.filter_by(user_id=user_id)

    total_debits = total_debit.scalar() or 0

    return total_debits





def total_credit_current_month(user_id=None):
    """Total credit (received funds) for the current month"""
    current_month = date.today().month
    current_year = date.today().year

    total_credit = db.session.query(func.sum(Expense.amount)).filter(
        Expense.trans_type == 'Credit',
        func.extract('month', Expense.date_of_transaction) == current_month,
        func.extract('year', Expense.date_of_transaction) == current_year
    )
    if user_id:
        total_credit = total_credit.filter_by(user_id=user_id)
    total_credits = total_credit.scalar() or 0


    return total_credits


def total_debit_current_month(user_id=None):
    """Total debit (expenses) for the current month"""
    current_month = date.today().month
    current_year = date.today().year

    total_debit = db.session.query(func.sum(Expense.amount)).filter(
        Expense.trans_type == 'Debit',
        func.extract('month', Expense.date_of_transaction) == current_month,
        func.extract('year', Expense.date_of_transaction) == current_year
    )
    if user_id:
        #total_credit = total_credit.filter_by(user_id=user_id)
        total_debit = total_debit.filter_by(user_id=user_id)
    #total_credits = total_credit.scalar() or 0
    total_debits = total_debit.scalar() or 0

    return total_debits




def opening_balance_current_month(user_id=None):
    """Opening balance as of the start of the current month"""
    current_month = date.today().month
    current_year = date.today().year

    # Total credit and debit before the current month
    total_credit_before = db.session.query(func.sum(Expense.amount)).filter(
        Expense.trans_type == 'Credit',
        or_(
            func.extract('year', Expense.date_of_transaction) < current_year,
            and_(
                func.extract('year', Expense.date_of_transaction) == current_year,
                func.extract('month', Expense.date_of_transaction) < current_month
            )
        )
    )

    total_debit_before = db.session.query(func.sum(Expense.amount)).filter(
        Expense.trans_type == 'Debit',
        or_(
            func.extract('year', Expense.date_of_transaction) < current_year,
            and_(
                func.extract('year', Expense.date_of_transaction) == current_year,
                func.extract('month', Expense.date_of_transaction) < current_month
            )
        )
    )
    if user_id:
        total_credit_before = total_credit_before.filter_by(user_id=user_id)
        total_debit_before = total_debit_before.filter_by(user_id=user_id)
    total_credits_before = total_credit_before.scalar() or 0
    total_debits_before = total_debit_before.scalar() or 0



    return total_credits_before - total_debits_before

def total_balance_current_month(user_id=None):
    """Total balance for the current month"""
    current_month = date.today().month
    current_year = date.today().year
    op = opening_balance_current_month()
    total_credit = db.session.query(func.sum(Expense.amount)).filter(
        Expense.trans_type == 'Credit',
        func.extract('month', Expense.date_of_transaction) == current_month,
        func.extract('year', Expense.date_of_transaction) == current_year
    )

    total_debit = db.session.query(func.sum(Expense.amount)).filter(
        Expense.trans_type == 'Debit',
        func.extract('month', Expense.date_of_transaction) == current_month,
        func.extract('year', Expense.date_of_transaction) == current_year
    )
    if user_id:
        total_credit = total_credit.filter_by(user_id=user_id)
        total_debit = total_debit.filter_by(user_id=user_id)
    total_credits = total_credit.scalar() or 0
    total_debits = total_debit.scalar() or 0

    return total_credits - total_debits + op

def get_total_enquiry():
    """Fetch total users based on access level."""
    return CallbackRequest.query.count()

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
