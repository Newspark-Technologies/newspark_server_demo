from flask import Flask, request, jsonify, Blueprint, redirect, url_for, current_app
from app import db
from app.models import Organization, Project, Donation, Publisher

# Create Blueprint
crowd_funding_blueprint = Blueprint('crowd_funding', __name__)