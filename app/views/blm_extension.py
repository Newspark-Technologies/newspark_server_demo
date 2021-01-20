from flask import Flask, request, jsonify, Blueprint, redirect, url_for, current_app
from app import db
import json
import random

# Create Blueprint
blm_extension_blueprint = Blueprint('blm_extension', __name__)


@blm_extension_blueprint.route('/get_blm_charities', methods=['POST'])
def get_blm_charities():
    article_name = request.json['article_name']

    with open('./data/blm_charities.json') as charity_data:
        data = json.load(charity_data)

    sampling = random.sample(data, 5)

    return jsonify(sampling)
