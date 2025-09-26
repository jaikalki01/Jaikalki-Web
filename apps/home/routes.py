# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""
import random
from functools import wraps

from flask import Flask, render_template, redirect, request, session, url_for, flash, jsonify, Response
from flask_login import login_user, current_user, login_required

import apps.common.util
from apps import db, mail

from apps.home import blueprint
from apps.home.forms import *
from apps.common.models import CallbackRequest, Role, Permission
from flask import render_template, request
from flask_login import login_required, current_user
from jinja2 import TemplateNotFound
from flask_cors import cross_origin

domain_directory_map = {

    "jaikalki.com": "jaikalki_web",

    "www.jaikalki.com": "jaikalki_web",

    "localhost": "jaikalki_web",  # Localhost support
    "127.0.0.1": "jaikalki_web",

    # Localhost IP
}



# Call this function after creating tables


@blueprint.route('/')
def route_default():
    try:
        # Map domains (including localhost) to directories


        # Get the current host and map to the appropriate directory
        current_host = request.host.split(':')[0]  # Remove port if present
        base_directory = domain_directory_map.get(current_host, "home")  # Default to "home" if not matched

        # Construct the path for the default index template
        default_template = f"{base_directory}/index.html"

        # Debug log (optional)
        # print(f"Rendering default template: {default_template} for host: {current_host}")

        form = CallbackForm()
        return render_template(default_template, segment='index', form=form)

    except TemplateNotFound:
        # Debug log (optional)
        # print(f"Template not found for default route")
        return render_template('home/404.html'), 404
    except Exception as e:
        # Debug log (optional)
        # print(f"Error occurred: {e}")
        return render_template('home/404.html'), 500


@blueprint.route('/sitemap.xml', methods=['GET'])
def sitemap():
    """Generate sitemap with static links"""
    pages = [
        {"loc": "https://jaikalki.com/", "lastmod": "2024-01-30", "changefreq": "daily", "priority": "1.0"},
        {"loc": "https://jaikalki.com/about.html", "lastmod": "2024-01-30", "changefreq": "monthly", "priority": "0.8"},
        {"loc": "https://jaikalki.com/services.html", "lastmod": "2024-01-30", "changefreq": "weekly", "priority": "0.9"},
        {"loc": "https://jaikalki.com/services/GravityDigiPayment.html", "lastmod": "2024-01-30", "changefreq": "weekly", "priority": "0.9"},
        {"loc": "https://jaikalki.com/services/WebTech.html", "lastmod": "2024-01-30", "changefreq": "weekly", "priority": "0.9"},
        {"loc": "https://jaikalki.com/services/RankBoost.html", "lastmod": "2024-01-30", "changefreq": "weekly", "priority": "0.9"},
        {"loc": "https://jaikalki.com/services/GravityDigiPayment/Pay-In-Solution.html", "lastmod": "2024-01-30", "changefreq": "monthly", "priority": "0.7"},
        {"loc": "https://jaikalki.com/services/GravityDigiPayment/Pay-Out-Solution.html", "lastmod": "2024-01-30", "changefreq": "monthly", "priority": "0.7"},
        {"loc": "https://jaikalki.com/services/GravityDigiPayment/Relation-Officer.html", "lastmod": "2024-01-30", "changefreq": "monthly", "priority": "0.7"},
        {"loc": "https://jaikalki.com/services/WebTech/Web-Design.html", "lastmod": "2024-01-30", "changefreq": "weekly", "priority": "0.8"},
        {"loc": "https://jaikalki.com/services/WebTech/Web-Development.html", "lastmod": "2024-01-30", "changefreq": "weekly", "priority": "0.8"},
        {"loc": "https://jaikalki.com/services/WebTech/Mobile-App-Development.html", "lastmod": "2024-01-30", "changefreq": "weekly", "priority": "0.8"},
        {"loc": "https://jaikalki.com/services/WebTech/API-Integration.html", "lastmod": "2024-01-30", "changefreq": "weekly", "priority": "0.8"},
        {"loc": "https://jaikalki.com/services/WebTech/Rest-API-%20Construction.html", "lastmod": "2024-01-30", "changefreq": "weekly", "priority": "0.8"},
        {"loc": "https://jaikalki.com/services/WebTech/website_in_24hrs.html", "lastmod": "2024-01-30", "changefreq": "weekly", "priority": "0.8"},
        {"loc": "https://jaikalki.com/services/RankBoost/Jaikalki-Research.html", "lastmod": "2024-01-30", "changefreq": "weekly", "priority": "0.7"},
        {"loc": "https://jaikalki.com/services/RankBoost/Link-Building.html", "lastmod": "2024-01-30", "changefreq": "weekly", "priority": "0.7"},
        {"loc": "https://jaikalki.com/services/RankBoost/Internation-SEO.html", "lastmod": "2024-01-30", "changefreq": "weekly", "priority": "0.7"},
        {"loc": "https://jaikalki.com/services/RankBoost/Domestic-Local-SEO.html", "lastmod": "2024-01-30", "changefreq": "weekly", "priority": "0.7"},
        {"loc": "https://jaikalki.com/services/RankBoost/SEO-Audit.html", "lastmod": "2024-01-30", "changefreq": "weekly", "priority": "0.7"},
        {"loc": "https://jaikalki.com/services/RankBoost/Graphic-Design.html", "lastmod": "2024-01-30", "changefreq": "weekly", "priority": "0.7"},
        {"loc": "https://jaikalki.com/terms.html", "lastmod": "2024-01-30", "changefreq": "yearly", "priority": "0.6"},
        {"loc": "https://jaikalki.com/privacy.html", "lastmod": "2024-01-30", "changefreq": "yearly", "priority": "0.6"},
        {"loc": "https://jaikalki.com/refund.html", "lastmod": "2024-01-30", "changefreq": "yearly", "priority": "0.6"},
        {"loc": "https://jaikalki.com/contact.html", "lastmod": "2024-01-30", "changefreq": "monthly", "priority": "0.8"},
          ]

    xml = render_template("jaikalki_web/sitemap.xml", pages=pages)
    return Response(xml, mimetype="application/xml")




ALLOWED_ORIGINS = [
    "https://jaikalki.com",


    "https://www.jaikalki.com",
    "https://gurutvapay.com/",
    "https://www.gurutvapay.com/",
    "localhost",
    "http://127.0.0.1:5000/",

]

def validate_origin(f):
    """Decorator to validate the request's Origin header."""
    @wraps(f)
    def wrapped_function(*args, **kwargs):
        origin = request.headers.get('Origin')
        if origin not in ALLOWED_ORIGINS:
            return jsonify({"error": "Access denied. Invalid domain."}), 403
        return f(*args, **kwargs)
    return wrapped_function



# Register the filter with Jinja
#blueprint.jinja_env.filters['math_problem'] = generate_math_problem

from flask_mail import Message as mail_msg
def send_email(subject, sender, recipients, text_body, html_body):
    try:
        msg = mail_msg(subject, sender=sender, recipients=recipients)
        msg.body = text_body
        msg.html = html_body
        mail.send(msg)
        return True
    except Exception as e:
        # print(e)
        return False

@blueprint.route('/api/get_math_problem', methods=['GET'])
#@cross_origin(origins=['http://127.0.0.1:3000'])
#@cross_origin(origins=ALLOWED_ORIGINS)
@cross_origin(origins=["https://gurutvapay.com", "https://www.gurutvapay.com"])

#@validate_origin
def get_math_problem():
    """Generates a random math problem and sends it to the frontend."""
    num1 = random.randint(1, 20)
    num2 = random.randint(1, 20)
    correct_answer = num1 + num2

    return jsonify({"num1": num1, "num2": num2, "correct_answer": correct_answer})

@blueprint.route('/api/submit', methods=['POST'])
#@cross_origin(origins=ALLOWED_ORIGINS)
@cross_origin(origins=["https://gurutvapay.com", "https://www.gurutvapay.com"])

#@validate_origin
#@cross_origin(origins=['http://127.0.0.1:3000'])
def submit_form():
    """Handles form submission, validates input, stores data, and sends an email with IP."""
    data = request.json
    if not data:
        return jsonify({"error": "Invalid data"}), 400

    try:
        name = data.get('name')
        email = data.get('email')
        mobile = data.get('mobile')
        subject = data.get('subject')
        message = data.get('message')
        math_answer = data.get('math_answer')  # User's answer
        correct_answer = data.get('correct_answer')  # Server's correct answer
        reference = data.get('reference')
        # Retrieve the user's IP address
        #user_ip = request.remote_addr
        user_ip = data.get('user_ip')  # Fetch public IP from frontend
        if not user_ip:
            user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)  # Fallback

        # Validate fields
        if not all([name, email, mobile, subject, message, math_answer, correct_answer]):
            return jsonify({"error": "All fields are required"}), 400

        # Ensure subject is valid
        valid_subjects = ["Web Development", "SEO and Rank Boost", "GurutvaPay - Payment Solutions"]
        if subject not in valid_subjects:
            return jsonify({"error": "Invalid subject selected"}), 400
        valid_references = ["Google", "Facebook", "Instagram", "Friend", "Advertisement", "Other"]
        if reference not in valid_references:
            return jsonify({"error": "Invalid reference selected"}), 400

        # Validate the math problem
        if int(math_answer) != int(correct_answer):
            return jsonify({"error": "Incorrect math answer. Please try again."}), 400

        # Save the form data to the database
        callback_request = CallbackRequest(
            name=name,
            email=email,
            mobile=mobile,
            subject=f"{subject} and IP Address:{user_ip}",
            message=f"{message} and {reference}",
        )
        db.session.add(callback_request)
        db.session.commit()

        # Prepare email content (Including IP)
        email_subject = f"New Contact Form Submission: {subject}"
        text_body = f"""
        Name: {name}
        Email: {email}
        Mobile: {mobile}
        Subject: {subject}
        Message: {message}
        User IP: {user_ip}
        References: {reference}
        """

        html_body = f"""
        <h2>New Contact Form Submission</h2>
        <p><strong>Name:</strong> {name}</p>
        <p><strong>Email:</strong> {email}</p>
        <p><strong>Mobile:</strong> {mobile}</p>
        <p><strong>Subject:</strong> {subject}</p>
        <p><strong>Message:</strong> {message}</p>
        <p><strong>User IP:</strong> {user_ip}</p>
        <p><strong>References:</strong> {reference}</p>
        """

        # Send the email
        send_email(email_subject, sender="office.jaikalki@gmail.com", recipients=["gurutvapay@gmail.com"], text_body=text_body, html_body=html_body)

        return jsonify({"message": "Your request has been submitted successfully!"}), 200

    except Exception as e:
        print("Error occurred:", str(e))  # Debugging
        return jsonify({"error": str(e)}), 500




@blueprint.route('/<path:template>')  # Use <path:template> for subdirectory support
def route_template(template):
    try:
        # Map domains (including localhost) to directories


        # Get the current host and map to the appropriate directory
        current_host = request.host.split(':')[0]  # Remove port if present
        base_directory = domain_directory_map.get(current_host, "home")  # Default to "home" if not matched

        # Ensure the template ends with '.html'
        if not template.endswith('.html'):
            template += '.html'

        # Construct the full path
        full_path = f"{base_directory}/{template}"

        # Debug log (optional)
        # print(f"Attempting to render template: {full_path} for host: {current_host}")

        segment = get_segment(request)
        form = CallbackForm()
        return render_template(full_path, segment=segment, form=form)

    except TemplateNotFound:
        # Debug log (optional)
        # print(f"Template not found: {template}")
        return render_template('jaikalki_web/404.html'), 404
    except Exception as e:
        # Debug log (optional)
        # print(f"Error occurred: {e}")
        return render_template('jaikalki_web/404.html'), 500


# Helper - Extract current page name from request
def get_segment(request):
    try:
        segment = request.path.split('/')[-1]
        if segment == '':
            segment = 'index'
        return segment
    except:
        return None

@blueprint.route('/callback', methods=['POST', 'GET'])
def payment_callback():
    try:
        # Print incoming request data
        print("🔹 Incoming Request Headers:", request.headers)
        print("🔹 Incoming Request Data:", request.get_json())

        # Capture the request data
        callback_data = request.get_json()

        # Check if data is received
        if not callback_data:
            return jsonify({"status": "error", "message": "No data received"}), 400

        # Process the callback data (log or store it)
        # You can check the transaction status here
        transaction_id = callback_data.get("transaction_id", "N/A")
        status = callback_data.get("status", "unknown")

        print(f"✅ Transaction ID: {transaction_id}, Status: {status}")

        return jsonify({"status": "success", "message": "Callback received"}), 200

    except Exception as e:
        print("⚠️ Error:", str(e))
        return jsonify({"status": "error", "message": str(e)}), 500
