from flask import Flask, request, jsonify, Blueprint, redirect, url_for, current_app
from app import db, application
from app.models import Organization, Project, Donation, Publisher
import requests

# Create Blueprint
newsletter_blueprint = Blueprint('newsletter', __name__)


@newsletter_blueprint.route('/add_subscriber', methods=['POST'])
def add_subscriber():
    url = 'https://us10.api.mailchimp.com/3.0/lists/9f21c018ec/members/'
    data = {
        "email_address": request.form.get('email'),
        "status": "subscribed",
        "merge_fields": {
            "FNAME": request.form.get('first_name'),
            "LNAME": request.form.get('last_name')
        }
    }
    r = requests.post(url, json=data, auth=('newspark', application.config['MAILCHIMP_API_KEY']))
    r.raise_for_status()

    return jsonify("success")
