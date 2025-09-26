# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""
import os
import random

import pytz
from flask import Flask, render_template, redirect, request, session, url_for, flash
from flask_login import login_user, current_user, login_required
from werkzeug.utils import secure_filename

from apps import db
from apps.admin import blueprint
from flask import render_template, request
from flask_login import login_required, current_user
from jinja2 import TemplateNotFound
from apps.common.util import verify_pass, verify_pin, permission_required
from apps.admin.forms import *
from apps.common.models import *  # Assuming your model is named `UserPin`
#from apps.authentication.util import verify_pin
from apps.admin.controller import *
from apps import config
from flask import jsonify
import subprocess
IST = pytz.timezone('Asia/Kolkata')

@blueprint.route('/validate_username', methods=['GET'])
@login_required
def validate_username():
    username = request.args.get('username')
    if Users.query.filter_by(username=username).first():
        return jsonify(message='Username is already taken.', available=False)
    return jsonify(message='Username is available.', available=True)

@blueprint.route('/validate_email', methods=['GET'])
@login_required
def validate_email():
    email = request.args.get('email')
    if Users.query.filter_by(email=email).first():
        return jsonify(message='Email is already registered.', available=False)
    return jsonify(message='Email is available.', available=True)




@blueprint.route('/admin/unlock', methods=['GET', 'POST'])
@login_required
def unlock():
    if not current_user.lock_status:
        return redirect(url_for('admin_blueprint.dashboard'))

    if request.method == 'POST':
        pin = request.form.get('pin')
        password = request.form.get('password')
        #print(f'password:{password}, pin:{pin}')
        if pin:
            if current_user.unlock_app(pin):
                flash('Unlocked successfully!', 'success')
                return redirect(url_for('admin_blueprint.dashboard'))  # Redirect to index after unlocking
            flash('Incorrect PIN. Please try again.', 'danger')

        if password:
            if verify_pass(password, current_user.password):
                #print(f'password:{password}', verify_pass(password, current_user.password))
                current_user.lock_status = False
                db.session.commit()  # Save the change to the database
                flash('Unlocked successfully using password!', 'success')
                return redirect(url_for('admin_blueprint.dashboard'))  # Redirect after unlocking
            flash('Incorrect password. Please try again.', 'danger')

    return render_template('admin/dashboard/page-lock.html')



@blueprint.route('/admin/lock', methods=['GET', 'POST'])
@login_required
def lock():
    current_user.lock_status = True
    db.session.commit()  # Save the change to the database
    return redirect(url_for('admin_blueprint.unlock'))  # Redirect to the unlock page





@blueprint.route('/admin/set_pin', methods=['GET', 'POST'])
@login_required
def set_pin():
    form = PinForm()

    if request.method == 'POST':  # Explicit check for POST method
        pin = request.form.get('pin')  # Get the PIN from the hidden input field
        if pin and not form.pin.errors:
            user_id = current_user.id

            # Proceed with the logic for checking existing pins and storing the new pin
            existing_pins = UserPin.query.filter_by(user_id=user_id).order_by(UserPin.id).all()

            # Check if new pin is the same as any of the previous pins
            for stored_pin_obj in existing_pins:
                if verify_pin(pin, stored_pin_obj.pin_hash):
                    flash('New pin cannot be the same as any of your previous pins. Please choose a different pin.', 'danger')
                    return render_template('admin/dashboard/pin_generate.html', form=form)

            # Deactivate old pins
            for stored_pin_obj in existing_pins:
                stored_pin_obj.is_active = False

            # Save new pin
            new_pin = UserPin(user_id=user_id, pin=pin, is_active=True)
            db.session.add(new_pin)

            # Commit new pin to the database
            db.session.commit()

            # After committing the new pin, ensure that only 5 pins are kept
            existing_pins = UserPin.query.filter_by(user_id=user_id).order_by(UserPin.id).all()

            # If there are more than 5 pins, delete the oldest ones
            if len(existing_pins) > 5:
                # Calculate how many pins need to be deleted
                pins_to_delete = len(existing_pins) - 5

                # Delete the extra pins (the oldest ones)
                for old_pin in existing_pins[:pins_to_delete]:
                    db.session.delete(old_pin)

                # Commit the changes after deleting
                db.session.commit()

            flash('Pin set successfully!', 'success')
            return redirect(url_for('admin_blueprint.set_pin'))

    return render_template('admin/dashboard/pin_generate.html', form=form)






@blueprint.route('b2b/dashboard')
@login_required
@permission_required("b2b_access")
def b2b_dashboard():
    if current_user.lock_status:  # Check if the user is locked
        return redirect(url_for('admin_blueprint.unlock'))  # Redirect to lock page if locked

    if current_user.is_b2b():
        merchants = current_user.get_associated_merchants()
        trans_payin = current_user.get_associated_transactions_pay_in()  # Ensure this method exists
        trans_payout = current_user.get_associated_transactions_pay_out()  # Ensure this method exists
        pay_in_claim = current_user.get_b2b_associated_transactions_claim_pay_in()
        pay_in_pending = current_user.get_b2b_associated_transactions_pending_pay_in()
        pay_out_claim = current_user.get_b2b_associated_transactions_claim_pay_out()
        pay_out_pending = current_user.get_b2b_associated_transactions_pending_pay_out()
        merchants_count = current_user.get_merchants_count()
        trans_pay_in_count = current_user.get_transaction_pay_in_count()  # Corrected method name
        trans_payout_count = current_user.get_transaction_payout_count()  # Corrected method name

        #print(f'merchants: {merchants}')  # Fetch associatmerchants
        return render_template('admin/dashboard/b2b_dashboard.html',
        user_id = current_user.id,
        total_merchants = merchants_count,

        transactions = trans_payin,
        transactions_payout = trans_payout,

            # Totals for merchants and B2B users

            # Earnings
        total_b_earned_claim = pay_in_claim,

        total_b_earned_pending = pay_in_pending,
        total_merchants_list=merchants,

            # Transaction totals
        total_trans =  trans_pay_in_count,
        total_b_earned_claim_payout = pay_out_claim,

        total_b_earned_pending_payout = pay_out_pending,

        total_trans_payout = trans_payout_count
                               )

    if current_user.is_super_admin():
        return redirect(url_for('admin_blueprint.dashboard'))

    else:
        return render_template('admin/page-403.html'), 403


    #return redirect(url_for('admin_blueprint.b2b_dashboard'))


@blueprint.route('b2b/member_list', methods=['GET', 'POST'])
@login_required
@permission_required("b2b_access")
def b2b_member_list():
    if current_user.lock_status:  # Check if the user is locked
        return redirect(url_for('admin_blueprint.unlock'))  # Redirect to lock page if locked

    if current_user.is_b2b():
        per_page = request.args.get('per_page', 10, type=int)
        search_query = request.args.get('search', '')
        page = request.args.get('page', 1, type=int)  # Extract page number from the request

        current_user_token = current_user.user_token

        # Correcting the query logic: Ref contains the token should be part of the main filter condition
        query = Users.query.filter(
            (Users.ref.contains(current_user_token)) & (
                    (Users.username.ilike(f'%{search_query}%')) |
                    (Users.mobile.ilike(f'%{search_query}%')) |
                    (Users.email.ilike(f'%{search_query}%'))
            )
        ).order_by(Users.id.desc())  # Order by user ID in descending order

        # Paginate results
        users = query.paginate(page=page, per_page=per_page)

        return render_template('admin/dashboard/b2b_member_list.html', users=users)

    if current_user.is_super_admin():
        return redirect(url_for('admin_blueprint.dashboard'))

    else:
        return render_template('admin/page-403.html'), 403


@blueprint.route('/b2b/view_transaction_payIn', methods=['GET'])
@login_required
@permission_required("b2b_access")
def b2b_view_transaction():
    # Get pagination parameters

    if current_user.lock_status:  # Check if the user is locked
        return redirect(url_for('admin_blueprint.unlock'))  # Redirect to lock page if locked

    if current_user.is_b2b():

        current_user_token = current_user.user_token
        associated_users = Users.query.filter(Users.ref.contains(current_user_token)).all()
        total_b_earned_claim = db.session.query(db.func.sum(Transactions.b_earned_amount)) \
                                   .join(Users) \
                                   .filter(Transactions.user_id.in_([user.id for user in associated_users]),Transactions.claim_status == True).scalar() or 0


        total_b_earned_pending = db.session.query(db.func.sum(Transactions.b_earned_amount)) \
                                     .join(Users) \
                                     .filter(Transactions.user_id.in_([user.id for user in associated_users]),Transactions.claim_status == False
                                             ).scalar() or 0
        total_trans = db.session.query(db.func.sum(Transactions.transaction_amount)) \
                      .join(Users).filter(Transactions.user_id.in_([user.id for user in associated_users])) \
                      .scalar() or 0

        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        search_query = request.args.get('search', '')

        start_date = request.args.get('start_date', None)
        end_date = request.args.get('end_date', None)

        # Parse the date inputs if provided
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')

        # Query to filter transactions, joining with Users and UserContact
        query = Transactions.query.join(Users).join(UserContact).filter(Transactions.user_id.in_([user.id for user in associated_users]))
         # Order by transaction date
        if search_query:
            query = query.filter(
                (Users.username.ilike(f'%{search_query}%')) |
                (UserContact.business_name.ilike(f'%{search_query}%')) |
                (UserContact.firstName.ilike(f'%{search_query}%'))
            )

        # Apply date range filter
        if start_date and end_date:
            query = query.filter(Transactions.transaction_date.between(start_date, end_date))

        # Order by transaction date descending
        query = query.order_by(Transactions.transaction_date.desc())

        # Correct pagination call
        transactions = query.paginate(page=page, per_page=limit, error_out=False)

        # Prepare transaction details
        transaction_list = [{
            'id': transaction.id,
            'username': transaction.user.username,
            'business_name': transaction.user.user_contact.business_name,
            'first_name': transaction.user.user_contact.firstName,
            'transaction_amount': transaction.transaction_amount,
            #'b_markup_percentage': transaction.b_markup_percentage,
            'b_earned_amount': transaction.b_earned_amount,
            #'c_markup_percentage': transaction.c_markup_percentage,
            'c_earned_amount': transaction.c_earned_amount,
            'claim_status':transaction.claim_status,
            'transaction_date': transaction.transaction_date.strftime('%d %B %Y')  # Format date
        } for transaction in transactions.items]

        return render_template('admin/dashboard/b2b_transactions.html',
                           total_b_earned_claim=total_b_earned_claim,
                           #total_c_earned_claim=total_c_earned_claim,
                           total_b_earned_pending=total_b_earned_pending,
                           #total_c_earned_pending=total_c_earned_pending,
                           total_trans=total_trans,
                           transactions=transaction_list, pagination=transactions)
    if current_user.is_super_admin():
        return redirect(url_for('admin_blueprint.dashboard'))

    else:
        return render_template('admin/page-403.html'), 403


@blueprint.route('/b2b/view_transaction_user_payIn/<user_token>', methods=['GET'])
@login_required
@permission_required("b2b_access")
def b2b_view_transaction_user(user_token):

    if current_user.lock_status:  # Check if the user is locked
        return redirect(url_for('admin_blueprint.unlock'))  # Redirect to lock page if locked

    if current_user.is_b2b():

        current_user_token = current_user.user_token
        associated_users = Users.query.filter(Users.ref.contains(current_user_token)).all()

        total_b_earned_claim = db.session.query(db.func.sum(Transactions.b_earned_amount)) \
                                    .join(Users)\
                                   .filter(Transactions.claim_status == True, Users.user_token==user_token).scalar() or 0


        total_b_earned_pending = db.session.query(db.func.sum(Transactions.b_earned_amount)) \
                                     .join(Users) \
                                     .filter(Transactions.claim_status == False, Users.user_token==user_token).scalar() or 0
        total_trans = db.session.query(db.func.sum(Transactions.transaction_amount)) \
                  .join(Users) \
                  .filter(Users.user_token==user_token).scalar() or 0


        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        search_query = request.args.get('search', '')
        start_date = request.args.get('start_date', None)
        end_date = request.args.get('end_date', None)

        # Parse the date inputs if provided
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')

        # Construct query
        query = Transactions.query.join(Users).join(UserContact).filter(Transactions.user_id.in_([user.id for user in associated_users]),Users.user_token == user_token)

        # Apply search filter
        if search_query:
            query = query.filter(
                (Users.username.ilike(f'%{search_query}%')) |
                (UserContact.business_name.ilike(f'%{search_query}%')) |
                (UserContact.firstName.ilike(f'%{search_query}%'))
            )

        # Apply date range filter
        if start_date and end_date:
            query = query.filter(Transactions.transaction_date.between(start_date, end_date))

        # Order by transaction date descending
        query = query.order_by(Transactions.transaction_date.desc())

        # Paginate query
        transactions = query.paginate(page=page, per_page=limit, error_out=False)

        # Prepare transaction details
        transaction_list = [{
            'id': transaction.id,
            'username': transaction.user.username,
            'business_name': transaction.user.user_contact.business_name,
            'first_name': transaction.user.user_contact.firstName,
            'transaction_amount': transaction.transaction_amount,
            'b_earned_amount': transaction.b_earned_amount,
            'c_earned_amount': transaction.c_earned_amount,
            'claim_status': transaction.claim_status,
            'transaction_date': transaction.transaction_date.strftime('%d %B %Y')
        } for transaction in transactions.items]

        return render_template('admin/dashboard/b2b_user_transactions.html',
                           user_token=user_token,
                           total_b_earned_claim=total_b_earned_claim,
                           #total_c_earned_claim=total_c_earned_claim,
                           total_b_earned_pending=total_b_earned_pending,
                           #total_c_earned_pending=total_c_earned_pending,
                           total_trans=total_trans,
                           transactions=transaction_list, pagination=transactions)

    if current_user.is_super_admin():
        return redirect(url_for('admin_blueprint.dashboard'))

    else:
        return render_template('admin/page-403.html'), 403


@blueprint.route('/b2b/view_transaction_payOut', methods=['GET'])
@login_required
@permission_required("b2b_access")
def b2b_view_transaction_payout():
    # Get pagination parameters
    if current_user.lock_status:  # Check if the user is locked
        return redirect(url_for('admin_blueprint.unlock'))  # Redirect to lock page if locked

    if current_user.is_b2b():
            current_user_token = current_user.user_token
            associated_users = Users.query.filter(Users.ref.contains(current_user_token)).all()

            total_b_earned_claim = db.session.query(db.func.sum(Transactions_payout.b_earned_amount)) \
                                       .join(Users) \
                                       .filter(Transactions_payout.user_id.in_([user.id for user in associated_users]),Transactions_payout.claim_status == True).scalar() or 0


            total_b_earned_pending = db.session.query(db.func.sum(Transactions_payout.b_earned_amount)) \
                                         .join(Users) \
                                         .filter(Transactions_payout.user_id.in_([user.id for user in associated_users]),Transactions_payout.claim_status == False
                                                 ).scalar() or 0

            total_trans = db.session.query(db.func.sum(Transactions_payout.transaction_amount)) \
                              .join(Users).filter(Transactions_payout.user_id.in_([user.id for user in associated_users])) \
                              .scalar() or 0

            page = request.args.get('page', 1, type=int)
            limit = request.args.get('limit', 10, type=int)
            search_query = request.args.get('search', '')

            start_date = request.args.get('start_date', None)
            end_date = request.args.get('end_date', None)

            # Parse the date inputs if provided
            if start_date:
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
            if end_date:
                end_date = datetime.strptime(end_date, '%Y-%m-%d')

            # Query to filter transactions, joining with Users and UserContact
            query = Transactions_payout.query.join(Users).join(UserContact).filter(Transactions_payout.user_id.in_([user.id for user in associated_users]))
             # Order by transaction date
            if search_query:
                query = query.filter(
                    (Users.username.ilike(f'%{search_query}%')) |
                    (UserContact.business_name.ilike(f'%{search_query}%')) |
                    (UserContact.firstName.ilike(f'%{search_query}%'))
                )

            # Apply date range filter
            if start_date and end_date:
                query = query.filter(Transactions_payout.transaction_date.between(start_date, end_date))

            # Order by transaction date descending
            query = query.order_by(Transactions_payout.transaction_date.desc())

            # Correct pagination call
            transactions = query.paginate(page=page, per_page=limit, error_out=False)

            # Prepare transaction details
            transaction_list = [{
                'id': transaction.id,
                'username': transaction.user.username,
                'business_name': transaction.user.user_contact.business_name,
                'first_name': transaction.user.user_contact.firstName,
                'transaction_amount': transaction.transaction_amount,
                #'b_markup_percentage': transaction.b_markup_percentage,
                'b_earned_amount': transaction.b_earned_amount,
                #'c_markup_percentage': transaction.c_markup_percentage,
                'c_earned_amount': transaction.c_earned_amount,
                'claim_status':transaction.claim_status,
                'transaction_date': transaction.transaction_date.strftime('%d %B %Y')  # Format date
            } for transaction in transactions.items]

            return render_template('admin/dashboard/b2b_transactions_payout.html',
                                   total_b_earned_claim=total_b_earned_claim,
                                   #total_c_earned_claim=total_c_earned_claim,
                                   total_b_earned_pending=total_b_earned_pending,
                                   #total_c_earned_pending=total_c_earned_pending,
                                   total_trans=total_trans,
                                   transactions=transaction_list, pagination=transactions)
    if current_user.is_super_admin():
        return redirect(url_for('admin_blueprint.dashboard'))

    else:
        return render_template('admin/page-403.html'), 403

@blueprint.route('/b2b/view_transaction_user_payOut/<user_token>', methods=['GET'])
@login_required
@permission_required("b2b_access")
def b2b_view_transaction_user_payout(user_token):
    if current_user.lock_status:  # Check if the user is locked
        return redirect(url_for('admin_blueprint.unlock'))  # Redirect to lock page if locked

    if current_user.is_b2b():
            current_user_token = current_user.user_token
            associated_users = Users.query.filter(Users.ref.contains(current_user_token)).all()

            total_b_earned_claim = db.session.query(db.func.sum(Transactions_payout.b_earned_amount)) \
                                        .join(Users)\
                                       .filter(Transactions_payout.claim_status == True, Users.user_token==user_token).scalar() or 0

            total_c_earned_claim = db.session.query(db.func.sum(Transactions_payout.c_earned_amount)) \
                                       .join(Users) \
                                       .filter(Transactions_payout.claim_status == True, Users.user_token==user_token).scalar() or 0

            total_b_earned_pending = db.session.query(db.func.sum(Transactions_payout.b_earned_amount)) \
                                         .join(Users) \
                                         .filter(Transactions_payout.claim_status == False, Users.user_token==user_token).scalar() or 0
            total_c_earned_pending = db.session.query(db.func.sum(Transactions_payout.c_earned_amount)) \
                                         .join(Users) \
                                         .filter(Transactions_payout.claim_status == False, Users.user_token==user_token).scalar() or 0
            total_trans = db.session.query(db.func.sum(Transactions_payout.transaction_amount)) \
                              .join(Users) \
                              .filter(Users.user_token==user_token).scalar() or 0

            # Get parameters from request
            page = request.args.get('page', 1, type=int)
            limit = request.args.get('limit', 20, type=int)
            search_query = request.args.get('search', '')
            start_date = request.args.get('start_date', None)
            end_date = request.args.get('end_date', None)

            # Parse the date inputs if provided
            if start_date:
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
            if end_date:
                end_date = datetime.strptime(end_date, '%Y-%m-%d')

            # Construct query
            query = Transactions_payout.query.join(Users).join(UserContact).filter(Transactions_payout.user_id.in_([user.id for user in associated_users]),Users.user_token == user_token)

            # Apply search filter
            if search_query:
                query = query.filter(
                    (Users.username.ilike(f'%{search_query}%')) |
                    (UserContact.business_name.ilike(f'%{search_query}%')) |
                    (UserContact.firstName.ilike(f'%{search_query}%'))
                )

            # Apply date range filter
            if start_date and end_date:
                query = query.filter(Transactions_payout.transaction_date.between(start_date, end_date))

            # Order by transaction date descending
            query = query.order_by(Transactions_payout.transaction_date.desc())

            # Paginate query
            transactions = query.paginate(page=page, per_page=limit, error_out=False)

            # Prepare transaction details
            transaction_list = [{
                'id': transaction.id,
                'username': transaction.user.username,
                'business_name': transaction.user.user_contact.business_name,
                'first_name': transaction.user.user_contact.firstName,
                'transaction_amount': transaction.transaction_amount,
                'b_earned_amount': transaction.b_earned_amount,
                'c_earned_amount': transaction.c_earned_amount,
                'claim_status': transaction.claim_status,
                'transaction_date': transaction.transaction_date.strftime('%d %B %Y')
            } for transaction in transactions.items]

            return render_template('admin/dashboard/b2b_user_transactions_payout.html',
                                   user_token=user_token,
                                   total_b_earned_claim=total_b_earned_claim,
                                   total_c_earned_claim=total_c_earned_claim,
                                   total_b_earned_pending=total_b_earned_pending,
                                   total_c_earned_pending=total_c_earned_pending,
                                   total_trans=total_trans,
                                   transactions=transaction_list, pagination=transactions)

    if current_user.is_super_admin():
        return redirect(url_for('admin_blueprint.dashboard'))

    else:
        return render_template('admin/page-403.html'), 403


@blueprint.route('/admin/query', methods=['GET', 'POST'])
@login_required
@permission_required("query_access")
def query():

    if current_user.lock_status:  # Check if the user is locked
        return redirect(url_for('admin_blueprint.unlock'))  # Redirect to lock page if locked

    if current_user.is_super_admin():
        # Get search query from the request arguments
        search_query = request.args.get('search', '')

        # Construct search query using filter with LIKE
        if search_query:
            users = CallbackRequest.query.filter(
                (CallbackRequest.email.ilike(f"%{search_query}%")) |
                (CallbackRequest.mobile.ilike(f"%{search_query}%"))
            ).paginate(per_page=10, page=request.args.get('page', 1, type=int))
        else:
            # Fetch users without a search filter
            users = CallbackRequest.query.paginate(per_page=10, page=request.args.get('page', 1, type=int))

        # Handle delete action if present
        if request.method == 'POST':
            delete_id = request.form.get('delete_id')
            if delete_id:
                callback_request = CallbackRequest.query.get(delete_id)
                if callback_request:
                    db.session.delete(callback_request)
                    db.session.commit()
                    flash('Callback request has been deleted successfully.', 'success')
                else:
                    flash('Callback request not found.', 'danger')
            return redirect(url_for('admin_blueprint.query'))

        return render_template('admin/dashboard/query.html', users=users, search_query=search_query)
    if current_user.is_b2b():
        return redirect(url_for('admin_blueprint.b2b_dashboard'))

    else:
        return render_template('admin/page-403.html'), 403



@blueprint.route('/expense_summary', methods=['GET', 'POST'])
@login_required
@permission_required("expanse_view")
def expense_summary():
    if current_user.lock_status:
        return redirect(url_for('admin_blueprint.unlock'))

    if current_user.is_super_admin():
        page = request.args.get('page', 1, type=int)
        selected_user_id = request.args.get('user_id', type=int)
        #search_term = request.args.get('search', '', type=str)  # Get search term

        users = Users.query.filter_by(access=1).all()

        query = Expense.query
        if selected_user_id:
            query = query.filter_by(user_id=selected_user_id)

        # Apply search filter if search term is provided
        #if search_term:
            #query = query.filter(Expense.remark.ilike(f"%{search_term}%"))

        pagination = query.order_by(Expense.id.desc()).paginate(page=page, per_page=20)

        balance = total_balance(selected_user_id)
        received_fund = total_received_fund(selected_user_id)
        expense = total_expense(selected_user_id)
        cur_month_balance = total_balance_current_month(selected_user_id)
        cur_month_received_fund = total_credit_current_month(selected_user_id)
        cur_month_expense = total_debit_current_month(selected_user_id)
        opening_balance_cur_month = opening_balance_current_month(selected_user_id)

        form = ExpenseForm()

        if form.validate_on_submit():
            new_expense = Expense(
                trans_type=form.trans_type.data,
                amount=form.amount.data,
                remark=form.remark.data,
                date_of_transaction=form.date_of_transaction.data,
                user_id=current_user.id
            )
            db.session.add(new_expense)
            db.session.commit()
            flash('Transaction has been added successfully!', 'success')
            return redirect(url_for('admin_blueprint.expense_summary'))

        return render_template('admin/dashboard/expense_summary.html',
                               expenses=pagination.items,
                               pagination=pagination,
                               balance=balance, received_fund=received_fund,
                               expense=expense,
                               cur_month_blance=cur_month_balance,
                               cur_month_received_fund=cur_month_received_fund,
                               cur_month_expanse=cur_month_expense,
                               opening_blance_cur_month=opening_balance_cur_month,
                               users=users,
                               selected_user_id=selected_user_id,
                               #search_term=search_term,  # Pass search term
                               form=form
                               )

    if current_user.is_b2b():
        return redirect(url_for('admin_blueprint.b2b_dashboard'))

    return render_template('admin/page-403.html'), 403


@blueprint.route('/delete_expense/<int:expense_id>')
@login_required
@permission_required("expanse_delete")
def delete_expense(expense_id):
    # Fetch the expense by ID
    if current_user.lock_status:  # Check if the user is locked
        return redirect(url_for('admin_blueprint.unlock'))  # Redirect to lock page if locked

    if current_user.is_super_admin():
        expense = Expense.query.get_or_404(expense_id)

        # Delete the expense from the database
        db.session.delete(expense)
        db.session.commit()

        # Flash a success message
        flash(f'Expense ID {expense_id} deleted successfully!', 'success')

        # Redirect to the expenses list page
        return redirect(url_for('admin_blueprint.expense_summary'))  # Redirect to a page where expenses are displayed
    if current_user.is_b2b():
        return redirect(url_for('admin_blueprint.b2b_dashboard'))

    else:
        return render_template('admin/page-403.html'), 403


@blueprint.route('/admin/dashboard')
@login_required
def dashboard():
    if current_user.lock_status:  # Check if the user is locked
        return redirect(url_for('admin_blueprint.unlock'))  # Redirect to lock page if locked

    if current_user.is_super_admin() or current_user.is_employee():
        # Fetching totals
        tatal_query = get_total_enquiry()
        total_merchants = get_total_users_by_access(ACCESS['merchant'])
        total_b2b_users = get_total_users_by_access(ACCESS['b2b'])

        # Fetching earnings (claimed and pending)
        earned_claim = get_earned_amounts_by_claim_status(True)
        earned_pending = get_earned_amounts_by_claim_status(False)

        # Fetching transaction amounts
        total_trans = get_total_transactions()
        total_trans_payout = get_total_transactions_payout()

        # Fetching payout amounts
        earned_claim_payout = get_total_earned_payout_by_claim_status(True)
        earned_pending_payout = get_total_earned_payout_by_claim_status(False)

        # Fetch recent transactions
        transaction_list = get_transaction_list(limit=7)
        transaction_list_payout = get_transaction_list(limit=7)

        # Fetch recent merchants and B2B users
        total_merchants_list = get_users_list_by_access(ACCESS['merchant'], limit=7)
        total_b2b_users_list = get_users_list_by_access(ACCESS['b2b'], limit=7)

        # Pass these totals to the template
        return render_template(
            'admin/dashboard/dashboard.html',
            segment='index',
            user_id=current_user.id,
            total_merchants_list=total_merchants_list,
            total_b2b_users_list=total_b2b_users_list,
            transactions=transaction_list,
            transactions_payout=transaction_list_payout,
            total_query=tatal_query,
            # Totals for merchants and B2B users
            total_merchants=total_merchants,
            total_b2b_users=total_b2b_users,

            # Earnings
            total_b_earned_claim=earned_claim['total_b_earned'],
            total_c_earned_claim=earned_claim['total_c_earned'],
            total_b_earned_pending=earned_pending['total_b_earned'],
            total_c_earned_pending=earned_pending['total_c_earned'],

            # Transaction totals
            total_trans=total_trans,
            total_b_earned_claim_payout=earned_claim_payout['total_b_earned'],
            total_c_earned_claim_payout=earned_claim_payout['total_c_earned'],
            total_b_earned_pending_payout=earned_pending_payout['total_b_earned'],
            total_c_earned_pending_payout=earned_pending_payout['total_c_earned'],
            total_trans_payout=total_trans_payout
        )

    if current_user.is_b2b():
        return redirect(url_for('admin_blueprint.b2b_dashboard'))

    else:
        return render_template('admin/page-403.html'), 403


@blueprint.route('admin/register', methods=['GET', 'POST'])
@login_required
@permission_required("register_user")
def register_user():
    if current_user.lock_status:  # Check if the user is locked
        return redirect(url_for('admin_blueprint.unlock'))  # Redirect to lock page if locked

    if current_user.is_super_admin():
        form = RegistrationForm()

        if form.validate_on_submit():
            # Create a new user
            new_user = Users(
                username=form.username.data,
                email=form.email.data,
                mobile=form.mobile.data,
                password=form.password.data,
                access=form.access.data,
                user_token=str(uuid.uuid4()), # Generate UUID for user token
                ref = form.b2b_user.data
            )

            db.session.add(new_user)
            db.session.commit()

            flash(f'User {new_user.username} registered successfully!', 'success')
            return redirect(url_for('admin_blueprint.register_user'))
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        users = Users.query.paginate(page=page, per_page=per_page)
        return render_template('admin/dashboard/create_user.html', form=form, users=users)
    if current_user.is_b2b():
        return redirect(url_for('admin_blueprint.b2b_dashboard'))

    else:
        return render_template('admin/page-403.html'), 403

@blueprint.route('admin/edit_user/<user_token>', methods=['GET', 'POST'])
@login_required
@permission_required("register_user_edit")
def edit_user(user_token):
    if current_user.lock_status:
        return redirect(url_for('admin_blueprint.unlock'))

    if current_user.is_super_admin():
        user = Users.query.filter_by(user_token=user_token).first_or_404()

        # Instantiate the forms
        password_form = PasswordForm()
        #b2b_form = B2BUserForm(obj=user)
        details_form = UserDetailsForm(obj=user)  # Pre-populate with user data

        # Handle Password Form Submission
        if password_form.submit.data and password_form.validate_on_submit():
            if password_form.password.data:
                user.password = hash_pass(password_form.password.data)
                db.session.commit()
                flash('Password updated successfully!', 'success')
            else:
                flash('Please enter a new password.', 'danger')

        # Handle B2B User Form Submission

        # Handle User Details Form Submission
        if details_form.submit.data and details_form.validate_on_submit():
            details_form.populate_obj(user)
            db.session.commit()
            flash(f'User {user.username} updated successfully!', 'success')

        # Render the forms
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        users = Users.query.paginate(page=page, per_page=per_page)
        return render_template('admin/dashboard/edit_user.html', user=user, users=users,
                               password_form=password_form,
                               #b2b_form=b2b_form,
                               details_form=details_form)

    if current_user.is_b2b():
        return redirect(url_for('admin_blueprint.b2b_dashboard'))
    else:
        return render_template('admin/page-403.html'), 403

        # Render the forms







@blueprint.route('admin/member_list', methods=['GET', 'POST'])
@login_required
@permission_required("member_list_view")
def member_list():
    if current_user.lock_status:  # Check if the user is locked
        return redirect(url_for('admin_blueprint.unlock'))  # Redirect to lock page if locked

    if current_user.is_super_admin():
        page = request.args.get('page', 1, type=int)
        #limit = request.args.get('limit', 10, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search_query = request.args.get('search', '')
        query = Users.query.filter(
            (Users.username.ilike(f'%{search_query}%')) |
            (Users.mobile.ilike(f'%{search_query}%')) |
            (Users.email.ilike(f'%{search_query}%'))
        ).order_by(Users.id.desc())  # Order by transaction date

        # Correct pagination call
        users = query.paginate(page=page, per_page=per_page)

        #page = request.args.get('page', 1, type=int)

        #users = Users.query.paginate(page=page, per_page=per_page)
        return render_template('admin/dashboard/member_list.html',  users=users)

    if current_user.is_b2b():
        return redirect(url_for('admin_blueprint.b2b_dashboard'))

    else:
        return render_template('admin/page-403.html'), 403


@blueprint.route('admin/merchant_list', methods=['GET', 'POST'])
@login_required
@permission_required("b2b_access")
def merchant_list():
    if current_user.lock_status:  # Check if the user is locked
        return redirect(url_for('admin_blueprint.unlock'))  # Redirect to lock page if locked

    if current_user.is_super_admin():
        page = request.args.get('page', 1, type=int)
        #limit = request.args.get('limit', 10, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search_query = request.args.get('search', '')
        query = Users.query.filter(Users.access==2 and
            (Users.username.ilike(f'%{search_query}%')) |
            (Users.mobile.ilike(f'%{search_query}%')) |
            (Users.email.ilike(f'%{search_query}%'))
        ).order_by(Users.id.desc())  # Order by transaction date

        # Correct pagination call
        users = query.paginate(page=page, per_page=per_page)

        #page = request.args.get('page', 1, type=int)

        #users = Users.query.paginate(page=page, per_page=per_page)
        return render_template('admin/dashboard/merchant_list.html',  users=users)
    if current_user.is_b2b():
        return redirect(url_for('admin_blueprint.b2b_dashboard'))

    else:
        return render_template('admin/page-403.html'), 403


@blueprint.route('admin/b2b_list', methods=['GET', 'POST'])
@login_required
@permission_required("b2b_access")
def b2b_list():
    if current_user.lock_status:  # Check if the user is locked
        return redirect(url_for('admin_blueprint.unlock'))  # Redirect to lock page if locked

    if current_user.is_super_admin():
        page = request.args.get('page', 1, type=int)
        #limit = request.args.get('limit', 10, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search_query = request.args.get('search', '')
        query = Users.query.filter(
            (Users.username.ilike(f'%{search_query}%')) |
            (Users.mobile.ilike(f'%{search_query}%')) |
            (Users.email.ilike(f'%{search_query}%'))
        ).order_by(Users.id.desc())  # Order by transaction date

        # Correct pagination call
        users = query.paginate(page=page, per_page=per_page)

        #page = request.args.get('page', 1, type=int)

        #users = Users.query.paginate(page=page, per_page=per_page)
        return render_template('admin/dashboard/b2b_list.html',  users=users)
    if current_user.is_b2b():
        return redirect(url_for('admin_blueprint.b2b_dashboard'))

    else:
        return render_template('admin/page-403.html'), 403




@blueprint.route('/user/<user_token>/add_details', methods=['GET', 'POST'])
@login_required
@permission_required("register_user")
def add_details(user_token):
    if current_user.lock_status:  # Check if the user is locked
        return redirect(url_for('admin_blueprint.unlock'))  # Redirect to lock page if locked

    if current_user.is_super_admin():
    # Fetch the user using the user_id
        user = Users.query.filter_by(user_token=user_token).first()

        # Check if the user already has a contact record, else create a blank one
        user_contact = UserContact.query.filter_by(user_id=user.id).first()

        form = UserContactForm()

        # If form is submitted and validated, update or add details
        if form.validate_on_submit():
            if user_contact:
                # Update the existing details
                user_contact.firstName = form.firstName.data
                user_contact.middleName = form.middleName.data
                user_contact.lastName = form.lastName.data
                user_contact.dob = form.dob.data
                user_contact.address = form.address.data
                user_contact.city = form.city.data
                user_contact.state = form.state.data
                user_contact.pincode = form.pincode.data
                user_contact.business_name = form.business_name.data
                user_contact.c_markup = 0
                user_contact.b_markup = 0
                user_contact.c_markup_payout = 0
                user_contact.b_markup_payout = 0
                user_contact.gender = form.gender.data
            else:
                # Create new contact details
                user_contact = UserContact(
                    user_id=user.id,
                    firstName=form.firstName.data,
                    middleName=form.middleName.data,
                    lastName=form.lastName.data,
                    dob=form.dob.data,
                    address=form.address.data,
                    city=form.city.data,
                    state=form.state.data,
                    pincode=form.pincode.data,
                    business_name=form.business_name.data,
                    c_markup =0,
                    b_markup = 0,
                    c_markup_payout=0,
                    b_markup_payout=0,
                    gender = form.gender.data
                )
                db.session.add(user_contact)

            db.session.commit()
            flash('Details updated successfully!', 'success')
            return redirect(url_for('admin_blueprint.add_details', user_token=user_token))  # Redirect to profile or another route

        # Populate form with existing details if they exist
        if user_contact:
            form.firstName.data = user_contact.firstName
            form.middleName.data = user_contact.middleName
            form.lastName.data = user_contact.lastName
            form.dob.data = user_contact.dob
            form.address.data = user_contact.address
            form.city.data = user_contact.city
            form.state.data = user_contact.state
            form.pincode.data = user_contact.pincode
            form.business_name.data = user_contact.business_name
            form.gender.data = user_contact.gender

        return render_template('admin/dashboard/add_details.html', form=form, user=user)
    if current_user.is_b2b():
        return redirect(url_for('admin_blueprint.b2b_dashboard'))

    else:
        return render_template('admin/page-403.html'), 403


@blueprint.route('/user/<user_token>/add_kyc')
@login_required
@permission_required("register_user")
def add_kyc(user_token):
    # Logic for adding KYC
    pass

@blueprint.route('/user/<user_token>/add_transaction_payIn', methods=['GET', 'POST'])
@login_required
@permission_required("b2b_access")
def add_transaction(user_token):
    if current_user.lock_status:  # Check if the user is locked
        return redirect(url_for('admin_blueprint.unlock'))  # Redirect to lock page if locked

    if current_user.is_super_admin():
        user = Users.query.filter_by(user_token=user_token).first()  # Ensure user exists
        form = TransactionForm()

        # Check if there's an existing transaction for this user (assuming each user has one transaction to update)
        #transaction = Transactions.query.filter_by(user_id=user_id).first()

        if form.validate_on_submit():
            transaction_amount = form.transaction_amount.data
            #b_markup_percentage = form.b_markup_percentage.data
            #c_markup_percentage = form.c_markup_percentage.data
            transaction_date = form.transaction_date.data  # Get the transaction date from the form

            """if transaction:  # Update existing transaction
                transaction.transaction_amount = transaction_amount
                transaction.b_markup_percentage = b_markup_percentage
                transaction.c_markup_percentage = c_markup_percentage
                transaction.transaction_date = transaction_date"""

                #flash(f'Transaction for {user.username} has been updated successfully!', 'success')
            #else:  # Create a new transaction
            transaction = Transactions(
                user_id=user.id,
                transaction_amount=transaction_amount,
                #b_markup_percentage=b_markup_percentage,
                #c_markup_percentage=c_markup_percentage,
                transaction_date=transaction_date,
                trans_token=str(uuid.uuid4())
            )

            db.session.add(transaction)
            flash(f'New transaction for {user.username} has been added successfully!', 'success')

            db.session.commit()
            return redirect(url_for('admin_blueprint.add_transaction',user_token=user_token))  # Redirect to a different page after success


        return render_template('admin/dashboard/add_transaction.html', form=form, user=user)
    if current_user.is_b2b():
        return redirect(url_for('admin_blueprint.b2b_dashboard'))

    else:
        return render_template('admin/page-403.html'), 403


@blueprint.route('/user/<user_token>/add_transaction_payOut', methods=['GET', 'POST'])
@login_required
@permission_required("b2b_access")
def add_transaction_payout(user_token):
    if current_user.lock_status:  # Check if the user is locked
        return redirect(url_for('admin_blueprint.unlock'))  # Redirect to lock page if locked

    if current_user.is_super_admin():
        user = Users.query.filter_by(user_token=user_token).first()  # Ensure user exists
        form = TransactionForm()

        # Check if there's an existing transaction for this user (assuming each user has one transaction to update)
        #transaction = Transactions.query.filter_by(user_id=user_id).first()

        if form.validate_on_submit():
            transaction_amount = form.transaction_amount.data
            #b_markup_percentage = form.b_markup_percentage.data
            #c_markup_percentage = form.c_markup_percentage.data
            transaction_date = form.transaction_date.data  # Get the transaction date from the form

            """if transaction:  # Update existing transaction
                transaction.transaction_amount = transaction_amount
                transaction.b_markup_percentage = b_markup_percentage
                transaction.c_markup_percentage = c_markup_percentage
                transaction.transaction_date = transaction_date"""

                #flash(f'Transaction for {user.username} has been updated successfully!', 'success')
            #else:  # Create a new transaction
            transaction = Transactions_payout(
                user_id=user.id,
                transaction_amount=transaction_amount,
                #b_markup_percentage=b_markup_percentage,
                #c_markup_percentage=c_markup_percentage,
                transaction_date=transaction_date,
                trans_token=str(uuid.uuid4())
            )

            db.session.add(transaction)
            flash(f'New transaction for {user.username} has been added successfully!', 'success')

            db.session.commit()
            return redirect(url_for('admin_blueprint.add_transaction_payout',user_token=user_token))  # Redirect to a different page after success

        # Pre-fill the form with existing data if a transaction exists


        return render_template('admin/dashboard/add_transaction.html', form=form, user=user)
    if current_user.is_b2b():
        return redirect(url_for('admin_blueprint.b2b_dashboard'))

    else:
        return render_template('admin/page-403.html'), 403

@blueprint.route('/user/<user_token>/view_profile')
@login_required
@permission_required("view_profile")
def view_profile(user_token):
    user = Users.query.filter_by(user_token=user_token).first()
    contact = UserContact.query.filter_by(user_id=user.id).first()
    kyc_docs = UserKycDocs.query.filter_by(user_id=user.id).all()

    return render_template('admin/dashboard/view_profile.html',user_id=user.id, user=user,user_token=user_token, contact=contact, kyc_docs=kyc_docs)


@blueprint.route('/user/<user_token>/view_profile_for_all')
@login_required
@permission_required("view_profile")
def view_profile_for_all(user_token):
    user = Users.query.filter_by(user_token=user_token).first()
    contact = UserContact.query.filter_by(user_id=user.id).first()
    kyc_docs = UserKycDocs.query.filter_by(user_id=user.id).all()

    return render_template('admin/dashboard/other_view_profile.html',user_id=user.id, user=user,user_token=user_token, contact=contact, kyc_docs=kyc_docs)

@blueprint.route('/user/<user_token>/upload_cover_photo', methods=['POST'])
@login_required
@permission_required("register_user")
def upload_cover_photo(user_token):
    users = Users.query.filter_by(user_token=user_token).first()
    if not users:
        #print("User not found.")
        return jsonify(success=False, message='User not found.'), 404

    user_id = users.id
    user = UserContact.query.get_or_404(user_id)
    cover_photo = request.files.get('cover_photo')

    if cover_photo:
        if user.cover_profile and os.path.exists(user.cover_profile):
            os.remove(user.cover_profile)

        filename = f"{uuid.uuid4()}.jpg"
        save_path = os.path.join('apps', 'static', 'assets', 'img', 'team', filename)

        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        cover_photo.save(save_path)
        user.cover_profile = filename
        db.session.commit()

        #print(f"Cover photo uploaded successfully: {save_path}")
        return jsonify(success=True, message='Cover photo uploaded successfully!', image_url=f"/static/assets/img/team/{filename}")
    else:
        #print("Failed to upload cover photo.")
        return jsonify(success=False, message='Failed to upload cover photo.'), 400


@blueprint.route('/user/<user_token>/upload_profile_photo', methods=['POST'])
@login_required
@permission_required("register_user")
def upload_profile_photo(user_token):
    users = Users.query.filter_by(user_token=user_token).first()
    if not users:
        #print("User not found.")
        return jsonify(success=False, message='User not found.'), 404

    user_id = users.id
    user = UserContact.query.get_or_404(user_id)
    profile_photo = request.files.get('profile_photo')

    if profile_photo:
        if user.profile and os.path.exists(user.profile):
            os.remove(user.profile)

        filename = f"{uuid.uuid4()}.jpg"
        save_path = os.path.join('apps', 'static', 'assets', 'img', 'team', filename)

        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        profile_photo.save(save_path)
        user.profile = filename
        db.session.commit()

        #print(f"Profile photo uploaded successfully: {save_path}")
        return jsonify(success=True, message='Profile photo uploaded successfully!',
                       image_url=f"/static/assets/img/team/{filename}")

        #return jsonify(success=True, message='Profile photo uploaded successfully!', image_url=f"/static/assets/img/team/{filename}")
    else:
        #print("Failed to upload profile photo.")
        return jsonify(success=False, message='Failed to upload profile photo.'), 400


#from flask import request, redirect, url_for, flash

@blueprint.route('/transaction_payIn/action/<transaction_token>', methods=['POST'])
@login_required
@permission_required("b2b_access")
def transaction_action(transaction_token):
    if current_user.lock_status:  # Check if the user is locked
        return redirect(url_for('admin_blueprint.unlock'))  # Redirect to lock page if locked

    if current_user.is_super_admin():
        action = request.form.get('action')
        transaction = Transactions.query.filter_by(trans_token=transaction_token)

        if not transaction:
            flash('Transaction not found.', 'error')
            return redirect(url_for('admin_blueprint.view_transaction'))

        if action == 'claim':
            transaction.claim_status = True
            flash('Transaction claimed successfully.', 'success')
        elif action == 'cancel':
            transaction.claim_status = False
            flash('Claim cancelled successfully.', 'success')

        db.session.commit()
        return redirect(url_for('admin_blueprint.view_transaction'))
    if current_user.is_b2b():
        return redirect(url_for('admin_blueprint.b2b_dashboard'))

    else:
        return render_template('admin/page-403.html'), 403


@blueprint.route('/user/view_transaction_payIn', methods=['GET'])
@login_required
@permission_required("b2b_access")
def view_transaction():
    if current_user.lock_status:  # Check if the user is locked
        return redirect(url_for('admin_blueprint.unlock'))  # Redirect to lock page if locked

    if current_user.is_super_admin():
    # Get pagination parameters
        total_b_earned_claim = db.session.query(db.func.sum(Transactions.b_earned_amount)) \
                                   .join(Users) \
                                   .filter(Transactions.claim_status == True).scalar() or 0

        total_c_earned_claim = db.session.query(db.func.sum(Transactions.c_earned_amount)) \
                                   .join(Users) \
                                   .filter(Transactions.claim_status == True).scalar() or 0

        total_b_earned_pending = db.session.query(db.func.sum(Transactions.b_earned_amount)) \
                                     .join(Users) \
                                     .filter(Transactions.claim_status == False
                                             ).scalar() or 0
        total_c_earned_pending = db.session.query(db.func.sum(Transactions.c_earned_amount)) \
                                     .join(Users) \
                                     .filter(Transactions.claim_status == False
                                             ).scalar() or 0
        total_trans = db.session.query(db.func.sum(Transactions.transaction_amount)) \
                          .join(Users) \
                          .scalar() or 0

        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        search_query = request.args.get('search', '')

        start_date = request.args.get('start_date', None)
        end_date = request.args.get('end_date', None)

        # Parse the date inputs if provided
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')

        # Query to filter transactions, joining with Users and UserContact
        query = Transactions.query.join(Users).join(UserContact)
         # Order by transaction date
        if search_query:
            query = query.filter(
                (Users.username.ilike(f'%{search_query}%')) |
                (UserContact.business_name.ilike(f'%{search_query}%')) |
                (UserContact.firstName.ilike(f'%{search_query}%'))
            )

    # Apply date range filter
        if start_date and end_date:
            query = query.filter(Transactions.transaction_date.between(start_date, end_date))

        # Order by transaction date descending
        query = query.order_by(Transactions.transaction_date.desc())

        # Correct pagination call
        transactions = query.paginate(page=page, per_page=limit, error_out=False)

        # Prepare transaction details
        transaction_list = [{
            'id': transaction.id,
            'username': transaction.user.username,
            'business_name': transaction.user.user_contact.business_name,
            'first_name': transaction.user.user_contact.firstName,
            'transaction_amount': transaction.transaction_amount,
            #'b_markup_percentage': transaction.b_markup_percentage,
            'b_earned_amount': transaction.b_earned_amount,
            #'c_markup_percentage': transaction.c_markup_percentage,
            'c_earned_amount': transaction.c_earned_amount,
            'claim_status':transaction.claim_status,
            'transaction_date': transaction.transaction_date.strftime('%d %B %Y')  # Format date
        } for transaction in transactions.items]

        return render_template('admin/dashboard/transactions.html',
                               total_b_earned_claim=total_b_earned_claim,
                               total_c_earned_claim=total_c_earned_claim,
                               total_b_earned_pending=total_b_earned_pending,
                               total_c_earned_pending=total_c_earned_pending,
                               total_trans=total_trans,
                               transactions=transaction_list, pagination=transactions)
    if current_user.is_b2b():
        return redirect(url_for('admin_blueprint.b2b_dashboard'))

    else:
        return render_template('admin/page-403.html'), 403


@blueprint.route('/user/view_transaction_user_payIn/<user_token>', methods=['GET'])
@login_required
@permission_required("b2b_access")
def view_transaction_user(user_token):
    if current_user.lock_status:  # Check if the user is locked
        return redirect(url_for('admin_blueprint.unlock'))  # Redirect to lock page if locked

    if current_user.is_super_admin():
        total_b_earned_claim = db.session.query(db.func.sum(Transactions.b_earned_amount)) \
                                    .join(Users)\
                                   .filter(Transactions.claim_status == True, Users.user_token==user_token).scalar() or 0

        total_c_earned_claim = db.session.query(db.func.sum(Transactions.c_earned_amount)) \
                                   .join(Users) \
                                   .filter(Transactions.claim_status == True, Users.user_token==user_token).scalar() or 0

        total_b_earned_pending = db.session.query(db.func.sum(Transactions.b_earned_amount)) \
                                     .join(Users) \
                                     .filter(Transactions.claim_status == False, Users.user_token==user_token).scalar() or 0
        total_c_earned_pending = db.session.query(db.func.sum(Transactions.c_earned_amount)) \
                                     .join(Users) \
                                     .filter(Transactions.claim_status == False, Users.user_token==user_token).scalar() or 0
        total_trans = db.session.query(db.func.sum(Transactions.transaction_amount)) \
                          .join(Users) \
                          .filter(Users.user_token==user_token).scalar() or 0

        # Get parameters from request
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        search_query = request.args.get('search', '')
        start_date = request.args.get('start_date', None)
        end_date = request.args.get('end_date', None)

        # Parse the date inputs if provided
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')

        # Construct query
        query = Transactions.query.join(Users).join(UserContact).filter(Users.user_token == user_token)

        # Apply search filter
        if search_query:
            query = query.filter(
                (Users.username.ilike(f'%{search_query}%')) |
                (UserContact.business_name.ilike(f'%{search_query}%')) |
                (UserContact.firstName.ilike(f'%{search_query}%'))
            )

        # Apply date range filter
        if start_date and end_date:
            query = query.filter(Transactions.transaction_date.between(start_date, end_date))

        # Order by transaction date descending
        query = query.order_by(Transactions.transaction_date.desc())

        # Paginate query
        transactions = query.paginate(page=page, per_page=limit, error_out=False)

        # Prepare transaction details
        transaction_list = [{
            'id': transaction.id,
            'username': transaction.user.username,
            'business_name': transaction.user.user_contact.business_name,
            'first_name': transaction.user.user_contact.firstName,
            'transaction_amount': transaction.transaction_amount,
            'b_earned_amount': transaction.b_earned_amount,
            'c_earned_amount': transaction.c_earned_amount,
            'claim_status': transaction.claim_status,
            'transaction_date': transaction.transaction_date.strftime('%d %B %Y')
        } for transaction in transactions.items]

        return render_template('admin/dashboard/user_transactions.html',
                               user_token=user_token,
                               total_b_earned_claim=total_b_earned_claim,
                               total_c_earned_claim=total_c_earned_claim,
                               total_b_earned_pending=total_b_earned_pending,
                               total_c_earned_pending=total_c_earned_pending,
                               total_trans=total_trans,
                               transactions=transaction_list, pagination=transactions)
    if current_user.is_b2b():
        return redirect(url_for('admin_blueprint.b2b_dashboard'))

    else:
        return render_template('admin/page-403.html'), 403



@blueprint.route('/transaction_payOut/action/<transaction_token>', methods=['POST'])
@login_required
@permission_required("b2b_access")
def transaction_action_payout(transaction_token):
    if current_user.lock_status:  # Check if the user is locked
        return redirect(url_for('admin_blueprint.unlock'))  # Redirect to lock page if locked

    if current_user.is_super_admin():
        action = request.form.get('action')
        transaction = Transactions_payout.query.filter_by(trans_token=transaction_token)

        if not transaction:
            flash('Transaction not found.', 'error')
            return redirect(url_for('admin_blueprint.view_transaction'))

        if action == 'claim':
            transaction.claim_status = True
            flash('Transaction claimed successfully.', 'success')
        elif action == 'cancel':
            transaction.claim_status = False
            flash('Claim cancelled successfully.', 'success')

        db.session.commit()
        return redirect(url_for('admin_blueprint.view_transaction'))

    if current_user.is_b2b():
        return redirect(url_for('admin_blueprint.b2b_dashboard'))

    else:
        return render_template('admin/page-403.html'), 403



@blueprint.route('/user/view_transaction_payOut', methods=['GET'])
@login_required
@permission_required("b2b_access")
def view_transaction_payout():
    if current_user.lock_status:  # Check if the user is locked
        return redirect(url_for('admin_blueprint.unlock'))  # Redirect to lock page if locked

    if current_user.is_super_admin():
        # Get pagination parameters

        total_b_earned_claim = db.session.query(db.func.sum(Transactions_payout.b_earned_amount)) \
                                   .join(Users) \
                                   .filter(Transactions_payout.claim_status == True).scalar() or 0

        total_c_earned_claim = db.session.query(db.func.sum(Transactions_payout.c_earned_amount)) \
                                   .join(Users) \
                                   .filter(Transactions_payout.claim_status == True).scalar() or 0

        total_b_earned_pending = db.session.query(db.func.sum(Transactions_payout.b_earned_amount)) \
                                     .join(Users) \
                                     .filter(Transactions_payout.claim_status == False
                                             ).scalar() or 0
        total_c_earned_pending = db.session.query(db.func.sum(Transactions_payout.c_earned_amount)) \
                                     .join(Users) \
                                     .filter(Transactions_payout.claim_status == False
                                             ).scalar() or 0
        total_trans = db.session.query(db.func.sum(Transactions_payout.transaction_amount)) \
                          .join(Users) \
                          .scalar() or 0
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 10, type=int)
        search_query = request.args.get('search', '')

        start_date = request.args.get('start_date', None)
        end_date = request.args.get('end_date', None)

        # Parse the date inputs if provided
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')

        # Query to filter transactions, joining with Users and UserContact
        query = Transactions_payout.query.join(Users).join(UserContact)
         # Order by transaction date
        if search_query:
            query = query.filter(
                (Users.username.ilike(f'%{search_query}%')) |
                (UserContact.business_name.ilike(f'%{search_query}%')) |
                (UserContact.firstName.ilike(f'%{search_query}%'))
            )

        # Apply date range filter
        if start_date and end_date:
            query = query.filter(Transactions_payout.transaction_date.between(start_date, end_date))

        # Order by transaction date descending
        query = query.order_by(Transactions_payout.transaction_date.desc())

        # Correct pagination call
        transactions = query.paginate(page=page, per_page=limit, error_out=False)

        # Prepare transaction details
        transaction_list = [{
            'id': transaction.id,
            'username': transaction.user.username,
            'business_name': transaction.user.user_contact.business_name,
            'first_name': transaction.user.user_contact.firstName,
            'transaction_amount': transaction.transaction_amount,
            #'b_markup_percentage': transaction.b_markup_percentage,
            'b_earned_amount': transaction.b_earned_amount,
            #'c_markup_percentage': transaction.c_markup_percentage,
            'c_earned_amount': transaction.c_earned_amount,
            'claim_status':transaction.claim_status,
            'transaction_date': transaction.transaction_date.strftime('%d %B %Y')  # Format date
        } for transaction in transactions.items]

        return render_template('admin/dashboard/transactions_payout.html',
                               total_b_earned_claim=total_b_earned_claim,
                               total_c_earned_claim=total_c_earned_claim,
                               total_b_earned_pending=total_b_earned_pending,
                               total_c_earned_pending=total_c_earned_pending,
                               total_trans=total_trans,
                               transactions=transaction_list, pagination=transactions)
    if current_user.is_b2b():
        return redirect(url_for('admin_blueprint.b2b_dashboard'))

    else:
        return render_template('admin/page-403.html'), 403


@blueprint.route('/user/view_transaction_user_payOut/<user_token>', methods=['GET'])
@login_required
@permission_required("b2b_access")

def view_transaction_user_payout(user_token):
    if current_user.lock_status:  # Check if the user is locked
        return redirect(url_for('admin_blueprint.unlock'))  # Redirect to lock page if locked

    if current_user.is_super_admin():


        total_b_earned_claim = db.session.query(db.func.sum(Transactions_payout.b_earned_amount)) \
                                    .join(Users)\
                                   .filter(Transactions_payout.claim_status == True, Users.user_token==user_token).scalar() or 0

        total_c_earned_claim = db.session.query(db.func.sum(Transactions_payout.c_earned_amount)) \
                                   .join(Users) \
                                   .filter(Transactions_payout.claim_status == True, Users.user_token==user_token).scalar() or 0

        total_b_earned_pending = db.session.query(db.func.sum(Transactions_payout.b_earned_amount)) \
                                     .join(Users) \
                                     .filter(Transactions_payout.claim_status == False, Users.user_token==user_token).scalar() or 0
        total_c_earned_pending = db.session.query(db.func.sum(Transactions_payout.c_earned_amount)) \
                                     .join(Users) \
                                     .filter(Transactions_payout.claim_status == False, Users.user_token==user_token).scalar() or 0
        total_trans = db.session.query(db.func.sum(Transactions_payout.transaction_amount)) \
                          .join(Users) \
                          .filter(Users.user_token==user_token).scalar() or 0

        # Get parameters from request
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        search_query = request.args.get('search', '')
        start_date = request.args.get('start_date', None)
        end_date = request.args.get('end_date', None)

        # Parse the date inputs if provided
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')

        # Construct query
        query = Transactions_payout.query.join(Users).join(UserContact).filter(Users.user_token == user_token)

        # Apply search filter
        if search_query:
            query = query.filter(
                (Users.username.ilike(f'%{search_query}%')) |
                (UserContact.business_name.ilike(f'%{search_query}%')) |
                (UserContact.firstName.ilike(f'%{search_query}%'))
            )

        # Apply date range filter
        if start_date and end_date:
            query = query.filter(Transactions_payout.transaction_date.between(start_date, end_date))

        # Order by transaction date descending
        query = query.order_by(Transactions_payout.transaction_date.desc())

        # Paginate query
        transactions = query.paginate(page=page, per_page=limit, error_out=False)

        # Prepare transaction details
        transaction_list = [{
            'id': transaction.id,
            'username': transaction.user.username,
            'business_name': transaction.user.user_contact.business_name,
            'first_name': transaction.user.user_contact.firstName,
            'transaction_amount': transaction.transaction_amount,
            'b_earned_amount': transaction.b_earned_amount,
            'c_earned_amount': transaction.c_earned_amount,
            'claim_status': transaction.claim_status,
            'transaction_date': transaction.transaction_date.strftime('%d %B %Y')
        } for transaction in transactions.items]

        return render_template('admin/dashboard/user_transactions_payout.html',
                               user_token=user_token,
                               total_b_earned_claim=total_b_earned_claim,
                               total_c_earned_claim=total_c_earned_claim,
                               total_b_earned_pending=total_b_earned_pending,
                               total_c_earned_pending=total_c_earned_pending,
                               total_trans=total_trans,
                               transactions=transaction_list, pagination=transactions)

    if current_user.is_b2b():
        return redirect(url_for('admin_blueprint.b2b_dashboard'))

    else:
        return render_template('admin/page-403.html'), 403



@blueprint.route('/user/<user_token>/view_kyc')
@login_required
@permission_required("view_kyc")
def view_kyc(user_token):
    # Logic for viewing KYC
    pass




# Assuming blueprint is defined elsewhere
@blueprint.route('admin/add_me_bro', methods=['GET','POST'])
def add_me_bro():
    # Define the user details
    username = "super_admin"
    password = "Love@1718"
    mobile = "8655402556"
    email = "digipayments@gmail.com"
    access = 1  # Assuming 1 corresponds to super admin

    # Create a new user instance
    new_user = Users(
        username=username,
        email=email,
        mobile=mobile,
        password=password,  # Ensure you hash this password
        access=access,
        user_token=str(uuid.uuid4()),  # Generate UUID for user token
        ref=None  # Assuming no B2B reference for this user
    )

    # Add user to the session and commit
    db.session.add(new_user)
    db.session.commit()

    flash(f'User {new_user.username} registered successfully!', 'success')
    return redirect(url_for('admin_blueprint.dashboard'))  # Redirect to the user registration page or another page


@blueprint.route('/admin/phonebook', methods=['GET', 'POST'])
@login_required
@permission_required("phonebook_access")
def phonebook():
    if current_user.lock_status:  # Check if the user is locked
        return redirect(url_for('admin_blueprint.unlock'))  # Redirect to unlock page

    if current_user.is_super_admin():  # Only super admin can access this
        form = PhonebookForm()
        page = request.args.get('page', 1, type=int)
        search_query = request.args.get('query', '')

        # If there's a search query, filter by name, number, or company name
        if search_query:
            phonebook_entries = Phonebook.query.filter(
                (Phonebook.name.ilike(f'%{search_query}%')) |
                (Phonebook.number.ilike(f'%{search_query}%')) |
                (Phonebook.company_name.ilike(f'%{search_query}%'))
            ).paginate(page=page, per_page=10)
        else:
            phonebook_entries = Phonebook.query.paginate(page=page, per_page=10)

        if form.validate_on_submit():
            new_entry = Phonebook(
                name=form.name.data,
                number=form.number.data,
                company_name=form.company_name.data,
                address=form.address.data,
                user_id=current_user.id
            )
            db.session.add(new_entry)
            db.session.commit()
            flash('Phonebook entry added successfully!', 'success')
            return redirect(url_for('admin_blueprint.phonebook'))

        return render_template('admin/dashboard/phonebook.html', phonebook_entries=phonebook_entries, form=form, search_query=search_query)

    elif current_user.is_b2b():  # Redirect B2B users to their dashboard
        return redirect(url_for('admin_blueprint.b2b_dashboard'))

    else:
        return render_template('admin/page-403.html'), 403


@blueprint.route('/admin/phonebook/delete/<int:expense_id>', methods=['POST'])
@login_required
@permission_required("phonebook_access")
def delete_phonebook(expense_id):
    if current_user.lock_status:  # Check if the user is locked
        return redirect(url_for('admin_blueprint.unlock'))  # Redirect to lock page if locked

    entry = Phonebook.query.get_or_404(expense_id)
    if current_user.is_super_admin():  # Add necessary permissions check
        db.session.delete(entry)
        db.session.commit()
        flash('Entry deleted successfully', 'success')
    return redirect(url_for('admin_blueprint.phonebook'))

# Edit route
@blueprint.route('/admin/phonebook/edit/<int:expense_id>', methods=['GET', 'POST'])
@login_required
@permission_required("phonebook_access")
def edit_phonebook(expense_id):
    if current_user.lock_status:  # Check if the user is locked
        return redirect(url_for('admin_blueprint.unlock'))  # Redirect to lock page if locked

    entry = Phonebook.query.get_or_404(expense_id)
    form = PhonebookForm(obj=entry)
    if form.validate_on_submit():
        form.populate_obj(entry)
        db.session.commit()
        flash('Entry updated successfully', 'success')
        return redirect(url_for('admin_blueprint.phonebook'))
    return render_template('admin/edit_phonebook.html', form=form, entry=entry)


from flask_paginate import Pagination, get_page_parameter  # Pagination support


def get_user_list(page, per_page):
    # Get all usernames from /etc/passwd
    result = subprocess.run(['cut', '-d:', '-f1', '/etc/passwd'], capture_output=True, text=True)
    users = result.stdout.splitlines()  # Split output into list of usernames

    # Filter users that have a Maildir
    maildir_users = [user for user in users if os.path.exists(f'/home/{user}/Maildir')]

    # Pagination logic
    start = (page - 1) * per_page
    end = start + per_page
    return maildir_users[start:end], len(maildir_users)  # Return the filtered user list and the total count


@blueprint.route('/create_email_for_user', methods=['GET', 'POST'])
@login_required
@permission_required("create_email_access")
def create_email_for_user():
    if current_user.lock_status:
        return redirect(url_for('admin_blueprint.unlock'))

    if current_user.is_super_admin():
        page = request.args.get(get_page_parameter(), type=int, default=1)
        users, total_users = get_user_list(page, per_page=10)

        pagination = Pagination(page=page, total=total_users, per_page=10, css_framework='bootstrap4')

        form = CreateUserForm()
        if form.validate_on_submit():  # Check if form is valid
            username = form.username.data
            password = form.password.data

            try:
                # Check if the user already exists
                user_exists = subprocess.run(['id', username], capture_output=True)

                if user_exists.returncode == 0:  # User exists
                    # Update password
                    subprocess.run(['sudo', 'passwd', username], input=f"{password}\n{password}".encode())
                    subprocess.run(['sudo', 'mkdir', '-p', f'/home/{username}/Maildir/cur',
                                    f'/home/{username}/Maildir/new', f'/home/{username}/Maildir/tmp'])

                    # Set ownership and permissions
                    subprocess.run(['sudo', 'chown', '-R', f'{username}:{username}', f'/home/{username}/Maildir'])
                    subprocess.run(['sudo', 'chmod', '-R', '700', f'/home/{username}/Maildir'])

                    flash(f"Password and Mail Directory updated for user '{username}'!", 'success')
                else:  # User does not exist
                    # Create user command
                    subprocess.run(['sudo', 'adduser', '--disabled-password', '--gecos', '', username])
                    flash(f"User '{username}' created successfully!", 'success')

                # Create Maildir structure
                subprocess.run(['sudo', 'mkdir', '-p', f'/home/{username}/Maildir/cur',
                                f'/home/{username}/Maildir/new', f'/home/{username}/Maildir/tmp'])

                # Set ownership and permissions
                subprocess.run(['sudo', 'chown', '-R', f'{username}:{username}', f'/home/{username}/Maildir'])
                subprocess.run(['sudo', 'chmod', '-R', '700', f'/home/{username}/Maildir'])

                return redirect(url_for('admin_blueprint.create_email_for_user'))  # Redirect after successful operation

            except Exception as e:
                flash(f"Failed to create/update user: {str(e)}", 'danger')  # Flash message for errors

        return render_template('admin/dashboard/email_user.html', form=form, users=users, pagination=pagination)

    elif current_user.is_b2b():
        return redirect(url_for('admin_blueprint.b2b_dashboard'))
    else:
        return render_template('admin/page-403.html'), 403


@blueprint.route('/delete_user/<username>', methods=['POST'])
@login_required
@permission_required("create_email_access")
def delete_user(username):
    if current_user.lock_status:  # Check if the user is locked
        return redirect(url_for('admin_blueprint.unlock'))  # Redirect to lock page if locked

    if current_user.is_super_admin():
        try:
            subprocess.run(['sudo', 'deluser', username])
            flash(f"User '{username}' deleted successfully!", 'success')
        except Exception as e:
            flash(f"Failed to delete user: {str(e)}", 'danger')

    return redirect(url_for('admin_blueprint.create_email_for_user'))


# Route to change user password
@blueprint.route('/change_password/<username>', methods=['POST'])
@login_required
@permission_required("create_email_access")
def change_password(username):
    if current_user.lock_status:  # Check if the user is locked
        return redirect(url_for('admin_blueprint.unlock'))  # Redirect to lock page if locked


    if current_user.is_super_admin():
        new_password = request.form['new_password']
        try:
            subprocess.run(['sudo', 'passwd', username], input=f"{new_password}\n{new_password}".encode())
            flash(f"Password for '{username}' changed successfully!", 'success')
        except Exception as e:
            flash(f"Failed to change password: {str(e)}", 'danger')

    return redirect(url_for('admin_blueprint.create_email_for_user'))




# Admin Route: Generate OTP (Deactivates old OTPs and creates a new one)
@blueprint.route('/generate_otp', methods=['POST'])
@login_required
@permission_required("generate_otp_access")
def generate_otp():
    if current_user.lock_status:  # Check if the user is locked
        return redirect(url_for('admin_blueprint.unlock'))  # Redirect to lock page if locked

    now = datetime.now(IST)
    # Deactivate all old OTPs
    OTP.query.update({OTP.is_active: False})
    active_otp = OTP.query.filter_by(is_active=True).first()
    # Generate new OTP
    new_otp = OTP(otp_code=random.randint(100000, 999999), is_active=True, generated_at=now)
    db.session.add(new_otp)
    db.session.commit()
    flash(f"New OTP generated: {new_otp.otp_code}", "success")

    return redirect(url_for('admin_blueprint.generate_view'))
    #return render_template('admin/dashboard/generate_otp.html',active_otp=active_otp)

@blueprint.route('/generate_otp_view', methods=['GET'])
@login_required
@permission_required("generate_otp_access")
def generate_view():
    if current_user.lock_status:  # Check if the user is locked
        return redirect(url_for('admin_blueprint.unlock'))  # Redirect to lock page if locked


    active_otp = OTP.query.filter_by(is_active=True).first()
    if active_otp:
        active_otps = active_otp.otp_code
    else:
        active_otps= "Not Generated"
    # Generate new OTP

    #return redirect(url_for('admin_blueprint.attendance_calendar'))
    return render_template('admin/dashboard/generate_otp.html',active_otp=active_otps)


# User Route: Submit OTP for Punch In / Punch Out
@blueprint.route('/submit_attendance', methods=['POST'])
@login_required
@permission_required("attendance_access")
def submit_attendance():
    if current_user.lock_status:  # Check if the user is locked
        return redirect(url_for('admin_blueprint.unlock'))  # Redirect to lock page if locked

    otp_code = request.form.get('otp')
    now = datetime.now(IST)

    otp_entry = OTP.query.filter_by(otp_code=otp_code, is_active=True).first()

    if otp_entry:
        attendance_entries = Attendance.query.filter_by(user_id=current_user.id, date=now.date()).all()

        if len(attendance_entries) >= 2:
            flash("Attendance already submitted for today!", "danger")
            return redirect(url_for('admin_blueprint.attendance_calendar'))

        if len(attendance_entries) == 0:
            # First OTP submission → Punch In
            attendance = Attendance(user_id=current_user.id, date=now.date(), punch_in=now, remark="Present", otp_used=otp_code)
            db.session.add(attendance)
            flash("Punch In recorded!", "success")

        elif len(attendance_entries) == 1:
            # Second OTP submission → Punch Out
            attendance = attendance_entries[0]
            attendance.punch_out = now
            db.session.commit()
            attendance.total_hours = attendance.punch_out - attendance.punch_in
            flash("Punch Out recorded!", "success")

        #otp_entry.is_active = False
        db.session.commit()

    else:
        flash("Invalid or expired OTP!", "danger")

    return redirect(url_for('admin_blueprint.attendance_calendar'))

# Calendar Route: Display Attendance Data
@blueprint.route('/attendance_calendar')
@login_required
@permission_required("attendance_access")
def attendance_calendar():
    if current_user.lock_status:  # Check if the user is locked
        return redirect(url_for('admin_blueprint.unlock'))  # Redirect to lock page if locked

    user_attendance = Attendance.query.filter_by(user_id=current_user.id).all()

    attendance_data = []
    for record in user_attendance:
        attendance_data.append({
            "date": record.date.strftime("%Y-%m-%d"),
            "punch_in": record.punch_in.strftime("%H:%M") if record.punch_in else None,
            "punch_out": record.punch_out.strftime("%H:%M") if record.punch_out else None,
            "total_hours": str(record.total_hours) if record.total_hours else "N/A",
            "remark": record.remark
        })

    return render_template('admin/dashboard/attendance.html', attendance_data=attendance_data)


@blueprint.route('/attendance_calendar_for_user')
@login_required
@permission_required("all_attendance_access")
def attendance_calendar_all_user():
    if current_user.lock_status:  # Check if the user is locked
        return redirect(url_for('admin_blueprint.unlock'))  # Redirect to lock page if locked

    selected_user_id = request.args.get('user_id', type=int)
    # search_term = request.args.get('search', '', type=str)  # Get search term

    users = Users.query.all()

    user_attendance = Attendance.query.filter_by(user_id=selected_user_id).all()

    attendance_data = []
    for record in user_attendance:
        attendance_data.append({
            "date": record.date.strftime("%Y-%m-%d"),
            "punch_in": record.punch_in.strftime("%H:%M") if record.punch_in else None,
            "punch_out": record.punch_out.strftime("%H:%M") if record.punch_out else None,
            "total_hours": str(record.total_hours) if record.total_hours else "N/A",
            "remark": record.remark,
            "username":record.user.username
        })

    return render_template('admin/dashboard/attendance_all_user.html', users=users, attendance_data=attendance_data)






@blueprint.route('/roles_permissions_list', methods=['GET','POST'])
@login_required
@permission_required("role_permission_access")
def roles_permissions_list():
    if current_user.lock_status:  # Check if the user is locked
        return redirect(url_for('admin_blueprint.unlock'))  # Redirect to lock page if locked

    roles = Role.query.all()
    permissions = Permission.query.all()
    users = Users.query.all()
    page = request.args.get('page', 1, type=int)
    pagination = Role.query.order_by(Role.id.asc()).paginate(page=page, per_page=20)

    roleform = RoleForm()  # Form for creating a new role
    if roleform.validate_on_submit():
        new_role = Role(name=roleform.name.data)
        db.session.add(new_role)
        db.session.commit()
        flash('Role created successfully', 'success')
        return redirect(url_for('admin_blueprint.roles_permissions_list'))
    permissionform = PermissionForm()  # Form for creating a new permission
    if permissionform.validate_on_submit():
        new_permission = Permission(name=permissionform.names.data)
        db.session.add(new_permission)
        db.session.commit()
        flash('Permission created successfully', 'success')
        return redirect(url_for('admin_blueprint.roles_permissions_list'))


    AssignRoleform = AssignRoleForm()  # Form to assign role to a user
    AssignRoleform.user_id.choices = [(user.id, user.username) for user in users]
    AssignRoleform.role_id.choices = [(role.id, role.name) for role in roles]

    if AssignRoleform.validate_on_submit():
        user = Users.query.get(AssignRoleform.user_id.data)
        role = Role.query.get(AssignRoleform.role_id.data)
        user.roles.append(role)  # Add role to user

        db.session.commit()
        flash('Role assigned to user successfully', 'success')
        return redirect(url_for('admin_blueprint.roles_permissions_list'))

    assignPermissionform = AssignPermissionForm()
    assignPermissionform.role_id.choices = [(role.id, role.name) for role in roles]
    assignPermissionform.permission_id.choices = [(perm.id, perm.name) for perm in permissions]

    if assignPermissionform.validate_on_submit():
        role = Role.query.get(assignPermissionform.role_id.data)
        permission = Permission.query.get(assignPermissionform.permission_id.data)

        if permission not in role.permissions:
            role.permissions.append(permission)  # Assign permission to the role
            db.session.commit()
            flash(f"Permission '{permission.name}' assigned to role '{role.name}'", "success")
        else:
            flash(f"Permission '{permission.name}' is already assigned to role '{role.name}'", "warning")

        return redirect(url_for('admin_blueprint.roles_permissions_list'))

    return render_template('admin/dashboard/roles_permissions_list.html', roles=roles,
                           permissions=permissions,
                           assignPermissionform=assignPermissionform,
                           permissionform=permissionform,
                           AssignRoleform=AssignRoleform,
                           roleform=roleform,
                           pagination=pagination)


@blueprint.route('/change_current_password', methods=['GET','POST'])
@login_required
@permission_required("change_password_access")
def change_user_password():
    form =PasswordForm()
    user = Users.query.filter_by(id=current_user.id).first()
    #roleform = RoleForm()  # Form for creating a new role
    if form.validate_on_submit():
        user.password = hash_pass(form.password.data)
        #db.session.add(new_role)
        db.session.commit()
        flash('Password created successfully', 'success')
        return redirect(url_for('admin_blueprint.change_user_password'))
    return render_template('admin/dashboard/password_change.html',password_form=form
                          )

#invoice
@blueprint.route('/invoice_dashboard', methods=['GET'])
@login_required
@permission_required("invoice_dashboard_access")
def invoice_dashboard():
    total_invoices = Invoice.query.count()
    pending_invoices = Invoice.query.filter_by(payment_status='Pending').count()

    return render_template('admin/invoice_dashboard.html',total_invoices=total_invoices,pending_invoices=pending_invoices)

@blueprint.route('/add_invoice', methods=['GET', 'POST'])
@login_required
@permission_required("invoice_dashboard_access")
def add_invoice():
    form = InvoiceForm()

    if form.validate_on_submit():
        try:
            # Save invoice
            new_invoice = Invoice(
                invoice_type=form.invoice_type.data,
                invoice_no=form.invoice_no.data,
                invoice_date=form.invoice_date.data,
                company_name=form.company_name.data,
                address=form.address.data,
                state=form.state.data,
                pincode=form.pincode.data,
                mobile_number=form.mobile_number.data,
                bill_to_date=form.bill_to_date.data,
                due_date=form.due_date.data,
                gstin=form.gstin.data,
                subtotal=form.subtotal.data,
                sgst_rate=form.sgst_rate.data,
                cgst_rate=form.cgst_rate.data,
                igst_rate=form.igst_rate.data,
                total_tax=form.total_tax.data,
                total_amount=form.total_amount.data
            )
            db.session.add(new_invoice)
            db.session.commit()

            # Add invoice items
            for item_form in form.items.data:
                new_item = InvoiceItem(
                    invoice_id=new_invoice.id,
                    description=item_form['description'],
                    hsn_sac_code=item_form['hsn_sac_code'],
                    quantity=int(item_form['quantity']),
                    rate=float(item_form['rate']),
                    amount=float(item_form['amount'])
                )
                db.session.add(new_item)

            db.session.commit()
            flash('Invoice added successfully!', 'success')

            # Redirect to print page
            return redirect(url_for('admin_blueprint.print_invoice', invoice_id=new_invoice.id))

        except Exception as e:
            db.session.rollback()
            flash(f'Error saving invoice: {e}', 'danger')

    else:
        flash('Form submission failed. Please check the fields.', 'danger')
        print("Form Data:", form.data)
        print("Form Errors:", form.errors)

    return render_template('admin/invoice_form.html', form=form)

@blueprint.route('/update_payment_status/<int:invoice_id>', methods=['POST'])
@login_required
@permission_required("invoice_dashboard_access")
def update_payment_status(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    new_status = request.form.get('payment_status')

    if new_status in ['Pending', 'Paid']:
        invoice.payment_status = new_status
        db.session.commit()
        flash(f'Invoice marked as {new_status}.', 'success')
    else:
        flash('Invalid status update.', 'danger')

    return redirect(url_for('admin_blueprint.list_invoices'))

@blueprint.route('/delete_invoice/<int:invoice_id>', methods=['POST'])
@login_required
@permission_required("invoice_dashboard_access")
def delete_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)

    db.session.delete(invoice)
    db.session.commit()

    flash('Invoice deleted successfully!', 'success')
    return redirect(url_for('admin_blueprint.list_invoices'))

@blueprint.route('/invoices')
@login_required
@permission_required("invoice_dashboard_access")
def list_invoices():
    total_invoices = Invoice.query.count()
    pending_invoices = Invoice.query.filter_by(payment_status='Pending').count()

    invoices = Invoice.query.all()
    return render_template('admin/invoice_list.html', invoices=invoices,total_invoices=total_invoices,pending_invoices=pending_invoices)

@blueprint.route('/print_invoice/<int:invoice_id>')
@login_required
@permission_required("invoice_dashboard_access")
def print_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    items = InvoiceItem.query.filter_by(invoice_id=invoice_id).all()

    return render_template('admin/print_invoice.html', invoice=invoice, items=items)

@blueprint.route('/invoice/<int:invoice_id>')
@login_required
@permission_required("invoice_dashboard_access")
def invoice_details(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    items = InvoiceItem.query.filter_by(invoice_id=invoice_id).all()

    return render_template('admin/invoice_details.html', invoice=invoice, items=items)
