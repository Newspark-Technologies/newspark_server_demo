from flask import Flask, request, jsonify, Blueprint, redirect, url_for, current_app
from app import db, mail, s3, redis, application
from app.helper.misc import secure_password, save_payment_info
from app.models import Organization, Project, Donation, Publisher
from flask_jwt_extended import (
    jwt_required, create_access_token,
    get_jwt_identity
)
from flask_mail import Message
from werkzeug.utils import secure_filename
from io import StringIO
from datetime import timedelta, datetime
import pandas as pd
import random
import string
import os
import hashlib
import json
import pickle
import requests

# Create Blueprint
charity_blueprint = Blueprint('charity', __name__)


@charity_blueprint.route('/login', methods=['POST'])
def login():
    """
    Logs in a user to the charity interface and returns a JWT access token
    :param: request.form params: email
    :return: JWT access token
    """
    email = request.form.get('email')

    exists = Organization.query.filter_by(email=email).first()

    # email in database
    if exists:
        salt = exists.salt
        password = request.form.get('password')
        hashed_password = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)

        # user is authenticated
        if hashed_password == exists.password:
            access_token = create_access_token(identity=email)
            return jsonify(access_token=access_token), 200

        # not a valid password
        else:
            return jsonify("Invalid Password")

    # not a valid email
    else:
        return jsonify("Invalid Email")


@charity_blueprint.route('/forgot_password', methods=['POST'])
def forgot_password():
    """
    Sends a email to a user with a new password if forgotten
    :param: request.form params: email
    :return: Success if email is verified, and actually sends the email, No Account Found otherwise
    """
    email = request.form.get('email')

    exists = Organization.query.filter_by(email=email).first()

    if exists:
        new_password = ''.join([str(random.choice(string.ascii_letters)) for j in range(8)])
        salt, new_hashed_password = secure_password(new_password)
        exists.password = new_hashed_password
        exists.salt = salt

        msg = Message()
        msg.subject = "New Password from Newspark"
        msg.body = 'Hello,\n\nWe are sorry you forgot your password! We have provided you with a temporary password below. ' \
                   'Please make sure to change your password in the Settings page! \n\n New Password: {} \n\n ' \
                   'Thank You,\n\n newspark team'.format(new_password)
        msg.recipients = [email]
        msg.sender = 'founders@newspark.us'
        mail.send(msg)

        db.session.commit()

        return jsonify("Success")
    else:
        return jsonify("No Account Found")


@charity_blueprint.route('/register_organization', methods=['POST'])
def register_organization():
    email = request.form.get('email')

    # check if already in database
    exists = db.session.query(db.exists().where(Organization.email == email)).scalar()

    if exists:
        return jsonify("Account Exists")

    else:

        salt, hashed_password = secure_password(request.form.get('password'))

        phone_number = request.form.get('phone_number')
        organization_name = request.form.get('organization_name')
        organization_website = request.form.get('organization_website')
        organization_description = request.form.get('organization_description')
        organization_street_address = request.form.get('organization_street_address')
        organization_city = request.form.get('organization_city')
        organization_state = request.form.get('organization_state')
        organization_country = request.form.get('organization_country')
        organization_type = request.form.get('organization_type')
        employer_id_number = request.form.get('employer_id_number')
        year_established = request.form.get('year_established')

        organization = Organization(
            email=email,
            password=hashed_password,
            salt=salt,
            phone_number=phone_number,
            organization_name=organization_name,
            organization_website=organization_website,
            organization_description=organization_description,
            organization_street_address=organization_street_address,
            organization_city=organization_city,
            organization_state=organization_state,
            organization_country=organization_country,
            organization_type=organization_type,
            employer_id_number=employer_id_number,
            verified=False,
            year_established=year_established,
        )

        db.session.add(organization)
        db.session.commit()

        # send the organization an email
        msg = Message()
        msg.subject = 'Welcome to newspark!'
        msg.body = 'Hi {},\n\nThank you for signing up for newspark! We are very excited to have your organization ' \
                   'on our platform. A member of our team will reach out shortly.\n\nTo ' \
                   'your success,\nnewspark team'.format(organization_name.rstrip())
        msg.recipients = [email]
        msg.sender = "founders@newspark.us"
        mail.send(msg)

        # send us an email
        msg = Message()
        msg.subject = 'New User!'
        msg.body = 'A new organization just registered with newspark. ' \
                   'Below is a general overview of the organization:\n' \
                   'Organization Name: {}\n' \
                   'Organization Type: {}\n' \
                   'Website: {}\n' \
                   'Email: {}\n' \
                   'Phone Number: {}\n'.format(organization_name, organization_type, organization_website, \
                                               email, phone_number)
        msg.recipients = ['karthik6d@gmail.com', 'alex.rubin@duke.edu', 'm.holubiec@gmail.com', \
                          'mahima.varma@duke.edu', 'founders@newspark.us', 'outreach@newspark.us']
        msg.sender = "founders@newspark.us"
        mail.send(msg)

        url = 'https://us10.api.mailchimp.com/3.0/lists/9f21c018ec/members/'
        data = {
            "email_address": email,
            "status": "subscribed",
        }
        r = requests.post(url, json=data, auth=('newspark', application.config['MAILCHIMP_API_KEY']))

        access_token = create_access_token(identity=email)
        return jsonify(access_token=access_token), 200


@charity_blueprint.route('/get_organization', methods=['GET'])
@jwt_required
def get_organization():
    """
    Returns all relevant information about a organization from a JWT
    :params: JWT token
    :return: serialized information of a Organization Object
    """
    current_org = get_jwt_identity()

    # check if already in database
    exists = db.session.query(db.exists().where(Organization.email == current_org)).scalar()

    if exists:
        organization = Organization.query.filter_by(email=current_org).first()
        return jsonify(organization=organization.serialize())

    else:
        return jsonify("Organization Does Not Exist")


@charity_blueprint.route('/edit_organization', methods=['POST'])
@jwt_required
def edit_organization():
    current_org = get_jwt_identity()

    # check if already in database
    exists = Organization.query.filter_by(email=current_org).first()

    if exists:
        password = request.form.get('password')
        if password:
            salt, hashed_password = secure_password(password)
            exists.password = hashed_password
            exists.salt = salt

        exists.phone_number = request.form.get('phone_number')
        exists.organization_website = request.form.get('organization_website')
        exists.organization_name = request.form.get('organization_name')
        exists.organization_description = request.form.get('organization_description')
        exists.organization_street_address = request.form.get('organization_street_address')
        exists.organization_city = request.form.get('organization_city')
        exists.organization_state = request.form.get('organization_state')
        exists.organization_country = request.form.get('organization_country')
        exists.organization_type = request.form.get('organization_type')

        if request.form.get('year_established'):
            exists.year_established = request.form.get('year_established')

        db.session.commit()

        for i in redis.keys():
            data = pickle.loads(redis.get(i))
            for j in data:
                if j['organization_id'] == current_org:
                    redis.delete(i)
                    break

        return jsonify("Success")
    else:
        return jsonify("Organization Does Not Exist")


@charity_blueprint.route('/get_projects', methods=['GET'])
@jwt_required
def get_projects():
    """
    Returns all projects associated with an organization from a JWT
    :params: JWT token
    :return: json object: organization name, projects (without ones that have been deleted, all_projects
    """
    organization_email = get_jwt_identity()

    # check if already in database
    exists = db.session.query(db.exists().where(Organization.email == organization_email)).scalar()

    if exists:
        organization_name = Organization.query.filter_by(email=organization_email)[0].organization_name
        projects = [p.serialize() for p in Project.query.filter_by(organization_id=organization_email)]
        projects_filtered = [p for p in projects if not p['removed']]

        project_names = set()

        unique_projects = []
        for project in projects_filtered:
            # print(project['removed'])
            project_name = project['project_name']
            if project_name not in project_names:
                project_names.add(project_name)
                unique_projects.append(project)

        unique_projects.reverse()

        return jsonify(organization_name=organization_name, projects=unique_projects, all_projects=projects)

    else:
        return jsonify("Organization Does Not Exist")


@charity_blueprint.route('/add_project', methods=['POST'])
@jwt_required
def add_project():
    organization_email = get_jwt_identity()
    project_name = request.form.get('project_name')
    project_short_description = request.form.get('project_short_description')
    project_description = request.form.get('project_description')
    project_goal = request.form.get('project_goal')
    project_city = request.form.get('project_city')
    project_state = request.form.get('project_state')
    project_country = request.form.get('project_country')
    newspaper_id = request.form.get('newspaper_id')
    project_raised = 0

    # Setting up uploading the picture
    f = request.files['project_picture_link']
    filename_split = secure_filename(f.filename).split('.')
    filename = filename_split[0] + str(project_name) + filename_split[1]

    s3.put_object(ACL='public-read', Bucket='newspark-charity-data', Key=filename, Body=f)
    project_picture_link = 'https://newspark-charity-data.s3.amazonaws.com/' + filename

    project = Project(
        organization_id=organization_email,
        project_name=project_name,
        project_short_description=project_short_description,
        project_description=project_description,
        project_picture_link=project_picture_link,
        project_goal=project_goal,
        project_city=project_city,
        project_state=project_state,
        project_country=project_country,
        project_raised=project_raised,
        newspaper_id=newspaper_id,
        removed=False
    )

    db.session.add(project)
    db.session.commit()

    # send us an email
    organization = Organization.query.filter_by(email=organization_email).first()
    msg = Message()
    msg.subject = 'Added Project'
    msg.body = 'A new project has been added in newspark ' \
               'Below is a general overview of the organization:\n' \
               'Organization Email: {} Organization Name: {}\n'.format(organization.organization_name, organization_email)
    msg.recipients = ['karthik6d@gmail.com', 'alex.rubin@duke.edu', 'm.holubiec@gmail.com', \
                      'mahima.varma@duke.edu', 'founders@newspark.us', 'outreach@newspark.us']
    msg.sender = "founders@newspark.us"
    mail.send(msg)

    return jsonify("Success")


@charity_blueprint.route('/edit_project', methods=['POST'])
@jwt_required
def edit_project():
    organization_email = get_jwt_identity()
    project_id = request.form.get('project_id')

    # check if already in database
    project = Project.query.filter_by(project_id=project_id).first()

    if project:

        if organization_email != project.organization_id:
            return jsonify("Project does not belong to this account")

        project.project_name = request.form.get('project_name')
        project.project_short_description = request.form.get('project_short_description')
        project.project_description = request.form.get('project_description')
        project.project_goal = request.form.get('project_goal')
        project.project_city = request.form.get('project_city')
        project.project_state = request.form.get('project_state')
        project.project_country = request.form.get('project_country')
        project.newspaper_id = request.form.get('newspaper_id')
        url = ''

        # print(request.files)
        # Setting up picture upload
        if 'project_picture_link' in request.files:
            # print("Does it come here")
            f = request.files['project_picture_link']
            filename_split = secure_filename(f.filename).split('.')
            filename = filename_split[0] + str(project_id) + filename_split[1]

            s3.put_object(ACL='public-read', Bucket='newspark-charity-data', Key=filename, Body=f)
            project.project_picture_link = 'https://newspark-charity-data.s3.amazonaws.com/' + filename
            url = 'https://newspark-charity-data.s3.amazonaws.com/' + filename

        else:
            if 'project_picture_link' in request.form:
                project.project_picture_link = request.form.get('project_picture_link')
                url = request.form.get('project_picture_link')

        db.session.commit()

        # Remove the edited versions from the cache
        sql_query = '''select article_link from articles where
                       project_id1={} or project_id2={} or project_id3={}
                       or project_id4={} or project_id5={} or project_id6={};'''.format(project_id, project_id,
                                                                                        project_id, project_id,
                                                                                        project_id, project_id)
        conn = db.engine.connect().connection
        df = pd.read_sql(sql_query, conn)
        conn.close()
        unique_articles = list(df['article_link'].unique())

        for i in unique_articles:
            if redis.exists(i):
                redis.delete(i)

        return jsonify("Success")

    else:
        return jsonify("Initiative Does Not Exist")


@charity_blueprint.route('/delete_project', methods=['POST'])
@jwt_required
def delete_project():
    """
    Changes the project to "deleted" status
    :param: request.form params: project_id
    :return: Returns Deleted if the project was successfully deleted
    """

    organization_email = get_jwt_identity()
    project_id = request.form.get('project_id')

    project = Project.query.filter_by(project_id=project_id).first()
    # print(project)

    if project:

        if organization_email != project.organization_id:
            return jsonify("Project does not belong to this account")

        project.removed = True
        db.session.commit()
        return jsonify("Deleted")

    else:
        return jsonify("Project Does Not Exist")


@charity_blueprint.route('/get_payment_logs', methods=['GET'])
@jwt_required
def get_payment_logs():
    """
    Returns the payments logs associated with one organization
    :param: JWT token for an organization
    :return: JSON object of payment_logs, total_donated_this_week, intiative_totals, total_donated, total_goal
    """
    current_org = get_jwt_identity()
    query1 = Donation.query.filter_by(organization_id=current_org).all()
    today = datetime.now()
    last_week = today - timedelta(days=7)

    serialize_query1 = []
    total_donated_this_week = 0
    for p in query1:
        log = p.serialize()
        project_id = log['project_id']
        log['project_name'] = Project.query.filter_by(project_id=project_id).first().project_name
        serialize_query1.append(log)

        donation_date_time = log['donation_date_time']

        if (donation_date_time >= last_week) and (donation_date_time <= today):
            total_donated_this_week += log['amount_donated']

    serialize_query1 = sorted(serialize_query1, key=lambda x: x['donation_date_time'], reverse=True)

    for i in range(len(serialize_query1)):
        d = serialize_query1[i]
        d['donation_date_time'] = d['donation_date_time'].strftime('%m/%d/%Y')

    donation_df = pd.DataFrame(serialize_query1)

    query2 = Project.query.filter_by(organization_id=current_org).all()
    output_dic = {"payment_logs": serialize_query1, "total_donated_this_week": total_donated_this_week, \
                  "initiative_totals": [], "total_donated": 0, "total_goal": 0}

    initiative_totals = []
    for project in query2:
        project_id = project.project_id
        dic = {}

        if donation_df.shape[0] != 0:
            donations_for_project = donation_df[donation_df.project_id == project_id]

            if donations_for_project.shape[0] != 0:
                initiative_total = donations_for_project['amount_donated'].sum()

            else:
                initiative_total = 0

        else:
            initiative_total = 0

        dic['total_donated'] = int(initiative_total)
        dic['goal'] = int(project.project_goal)
        dic['name'] = str(project.project_name)
        initiative_totals.append(dic)
        output_dic['total_donated'] += dic['total_donated']
        output_dic['total_goal'] += dic['goal']

    initiative_totals = sorted(initiative_totals, key=lambda d: d['total_donated'], reverse=True)

    initiative_totals_dict = {}
    for initiative in initiative_totals:
        t = (initiative['name'], initiative['goal'])
        if t not in initiative_totals_dict:
            initiative_totals_dict[t] = 0
        initiative_totals_dict[t] += initiative['total_donated']

    initiative_totals_grouped = []
    for name, goal in initiative_totals_dict.keys():
        d = {
            "total_donated": initiative_totals_dict[(name, goal)],
            "goal": goal,
            "name": name,
        }
        initiative_totals_grouped.append(d)

    output_dic['initiative_totals'] += initiative_totals_grouped

    return jsonify(output_dic)


@charity_blueprint.route('/get_payment_csv', methods=['GET'])
@jwt_required
def get_payment_csv():
    """
    Returns the url to a CSV with the payment logs
    :param: JWT token for an organization
    :return: JSON object of url
    """
    current_org = get_jwt_identity()
    organization = Organization.query.filter_by(email=current_org).first()
    query1 = Donation.query.filter_by(organization_id=current_org).all()

    serialize_query1 = []
    for p in query1:
        log = p.serialize()
        project_id = log['project_id']
        log['project_name'] = Project.query.filter_by(project_id=project_id).first().project_name

        del log['donation_id']
        del log['project_id']
        del log['organization_id']

        log['donor_name'] = 'NOT AVAILABLE'
        log['donor_email'] = 'NOT AVAILABLE'
        log['publisher_name'] = log.pop('newspaper_id')
        log['article_link'] = log.pop('newspaper_article_link')

        serialize_query1.append(log)

    donation_df = pd.DataFrame(serialize_query1)
    # print(donation_df.head())
    # donation_df = donation_df.sort_values(by=['donation_date_time'], ascending=False)

    csv_buffer = StringIO()
    donation_df.to_csv(csv_buffer)
    filename = organization.organization_name + '_payment_logs.csv'
    s3.put_object(Bucket='newspark-charity-data', Key=filename, Body=csv_buffer.getvalue())

    return jsonify({"url": s3.generate_presigned_url('get_object',
                                                     Params={'Bucket': 'newspark-charity-data', 'Key': filename},
                                                     ExpiresIn=300)})


@charity_blueprint.route('/get_publisher_counts', methods=['GET'])
@jwt_required
def get_publisher_counts():
    """
    Get all the publishers and counts
    :param: JWT token for an organization
    :return: JSON object of newspaper_names, counts
    """
    current_org = get_jwt_identity()

    sql_query = '''select newspaper_id, count(*)
                   from projects
                   where organization_id='{}'
                   and removed=FALSE
                   group by newspaper_id;
                   '''.format(current_org)

    conn = db.engine.connect().connection
    df = pd.read_sql(sql_query, conn)
    count_dict = list(df.T.to_dict().values())
    conn.close()

    newspaper_names = []
    counts = []
    for item in count_dict:
        newspaper_names.append(item['newspaper_id'])
        counts.append(item['count'])

    return jsonify(newspaper_names=newspaper_names, counts=counts)


@charity_blueprint.route('/contact_us', methods=['POST'])
@jwt_required
def contact_us():
    """
    Sends an email to us from the contact us
    :param: JWT token for an organization, request.form fields: first_name, last_name, email, body, primaryID
    :return: DONE if email is sent
    """
    organization_email = get_jwt_identity()
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    email = request.form.get('email')
    body = request.form.get('body')
    is_publisher = (request.form.get('isPublisher') == 'True')
    primary_id = request.form.get('primaryID')

    party = "charity/business"
    if is_publisher:
        party = "publisher"

    msg = Message()
    msg.subject = "CONTACT US EMAIL FROM: " + "{} {}, {} ({})".format(first_name, last_name, party, primary_id)
    msg.html = '<p>' + 'message: ' + body + '</p>' + '<p>' + 'reply to: {}'.format(email) + '</p>'
    msg.recipients = ['karthik6d@gmail.com', 'alex.rubin@duke.edu', 'founders@newspark.us', 'm.holubiec@gmail.com']
    msg.sender = email
    mail.send(msg)

    return jsonify("DONE")


@charity_blueprint.route('/edit_payment_info_charity', methods=['POST'])
@jwt_required
def edit_payment_info_charity():
    """
    Store payment information in a s3 bucket
    :param: JWT token for a owner, publisher name
    :return: Success if payment information added, No Account Found if owner not found in database
    """

    email = get_jwt_identity()
    exists = Organization.query.filter_by(email=email).first()

    if exists:
        full_name = request.form.get('accountHolder')
        bank_branch_address = request.form.get('bankBranchAddress')
        bank_name = request.form.get('bankName')
        account_type = request.form.get('accountType')
        bank_routing_number = request.form.get('bankRoutingNumber')
        bank_account_number = request.form.get('bankAccountNumber')

        save_payment_info(s3_client=s3,
                          full_name=full_name,
                          bank_branch_address=bank_branch_address,
                          bank_name=bank_name,
                          account_type=account_type,
                          bank_routing_number=bank_routing_number,
                          bank_account_number=bank_account_number,
                          publisher_charity='charity',
                          primary_id=email)

        return jsonify("Success")

    else:
        return jsonify("Charity Does Not Exist.")


@charity_blueprint.route('/get_publisher_names', methods=['GET'])
def get_publisher_names():
    """ Returns all the publisher names. """

    # publisher_names = [str(p) for p in Publisher.query.all()]
    publisher_names = [p.publisher_name for p in Publisher.query.all()]
    return jsonify(publisher_names=publisher_names)


@charity_blueprint.route('/add_charity_legal_record', methods=['POST'])
def add_charity_legal_record():
    email = request.form.get('email')
    now = datetime.now().strftime("%Y-%m-%d, %H:%M")
    bucket = "newspark-legal"
    file_name = "charities/legal_records.json"

    legal_records = json.load(s3.get_object(Bucket=bucket, Key=file_name)['Body'])
    legal_records[email] = {'version': 1, 'date_time': now}
    s3.put_object(Bucket=bucket, Key=file_name, Body=json.dumps(legal_records))

    return jsonify("Success")


@charity_blueprint.route('/check_charity_legal_record', methods=['POST'])
def check_charity_legal_record():
    email = request.form.get('email')
    bucket = "newspark-legal"
    file_name = "charities/legal_records.json"

    legal_records = json.load(s3.get_object(Bucket=bucket, Key=file_name)['Body'])

    if email in legal_records:
        return jsonify(True)
    else:
        return jsonify(False)
