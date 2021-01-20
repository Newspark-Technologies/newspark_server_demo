from flask import Flask, request, jsonify, Blueprint, redirect, url_for, current_app
from app.helper.misc import secure_password, update_recommendations, save_payment_info, get_projects_from_article
import pandas as pd
from app.models import *
from flask_jwt_extended import (
    jwt_required, create_access_token,
    get_jwt_identity
)
import random
import string
from flask_mail import Message
from app import mail
from app import admin_required
import datetime
from datetime import timedelta
import hashlib
from io import StringIO
from app import s3
from app import redis
from app import application
import pickle

# Create Blueprint
publisher_blueprint = Blueprint('publisher', __name__)


@publisher_blueprint.route('/owner_login', methods=['POST'])
def owner_login():
    """
    Logs in a publisher owner to the publisher interface and returns a JWT access token
    :param: request.form params: username
    :return: JWT access token
    """

    username = request.form.get('username')
    exists = Owner.query.filter_by(username=username).first()

    # Owner in database
    if exists:
        salt = exists.salt
        password = request.form.get('password')
        hashed_password = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)

        # user is authenticated
        if hashed_password == exists.password:
            access_token = create_access_token(identity=username)
            return jsonify(access_token=access_token), 200

        # not a valid password
        else:
            return jsonify("Invalid Password")

    # not a valid username
    else:
        return jsonify("Invalid Username")


@publisher_blueprint.route('/owner_forgot_password', methods=['POST'])
def owner_forgot_password():
    """
    Sends a email to a user with a new password if forgotten
    :param: request.form params: email
    :return: Success if email is verified, and actually sends the email, No Account Found otherwise
    """

    email = request.form.get('email')
    owner = Owner.query.filter_by(email=email).first()

    if owner:
        new_password = ''.join([str(random.choice(string.ascii_letters)) for j in range(8)])
        salt, new_hashed_password = secure_password(new_password)
        owner.password = new_hashed_password
        owner.salt = salt

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


@publisher_blueprint.route('/get_donations_from_publishers', methods=['GET'])
@admin_required
def get_donations_from_publishers():
    """
    Queries the donations and calculates the cumulative donations that were given to charities featured
    on any of the owner's publishing platforms.
    :param: request.form params: username
    :return: Donations, cumulative donations, and first and last dates that a donation took place
    if username is verified, No Account Found otherwise
    """

    username = get_jwt_identity()
    exists = Owner.query.filter_by(username=username).first()

    if exists:

        sql_query = '''select donation_date_time, newspaper_article_title, newspaper_article_link, amount_donated,
                        project_name, organization_name, donations.newspaper_id
                        from donations, projects, organizations
                        where donations.project_id=projects.project_id
                        and donations.organization_id=organizations.email
                        and donations.newspaper_id in 
                        (select publisher_id from Owning where owner_id='{}');'''.format(username)

        conn = db.engine.connect().connection
        donation_df = pd.read_sql(sql_query, conn)
        donation_list = list(donation_df.T.to_dict().values())

        donation_df = donation_df[['donation_date_time', 'amount_donated']]
        first_date = donation_df['donation_date_time'].min() - timedelta(days=7)
        last_date = donation_df['donation_date_time'].max()

        cum_sum_df = donation_df.groupby(['donation_date_time']).sum().cumsum()

        # create dict of dates with 0 donated for each date
        today = datetime.datetime.now()
        delta = today - first_date
        num_days = delta.days
        date_dict = {}
        for i in range(num_days + 1):
            date = first_date + timedelta(days=i)
            # date = date.replace(hour=0, minute=0, second=0, microsecond=0)
            date_dict[date.date()] = 0

        # fill in values for dict of dates
        for i in range(cum_sum_df.shape[0]):
            date = cum_sum_df.iloc[i].name
            amount_donated = cum_sum_df.iloc[i]['amount_donated']
            date_dict[date.date()] = amount_donated

        items = [list(i) for i in list(date_dict.items())]
        items_sorted = sorted(items, key=lambda x: x[0])

        # make sure no values of 0 between donation dates
        for i in range(1, len(items_sorted)):
            amount_donated = items_sorted[i][1]
            if amount_donated == 0:
                items_sorted[i][1] = items_sorted[i - 1][1]

        # convert items into a list of dicts
        items_list_of_dicts = {"labels": [], "values": []}
        for item in items_sorted:
            date = item[0].strftime('%m/%d/%Y')
            amount_donated = int(item[1])
            items_list_of_dicts["labels"].append(date)
            items_list_of_dicts["values"].append(amount_donated)

        # remove time from dates
        for i in range(len(donation_list)):
            donation_list[i]['donation_date_time'] = donation_list[i]['donation_date_time'].strftime('%m/%d/%Y')

        # sort donation list
        donation_list = sorted(donation_list, key=lambda x: x["donation_date_time"], reverse=True)

        return jsonify(donations=donation_list, cumulative_donations=items_list_of_dicts, \
                       first_date=first_date.strftime('%m/%d/%Y'), last_date=last_date.strftime('%m/%d/%Y'))

    else:
        return jsonify("No Account Found")


@publisher_blueprint.route('/get_donations_from_publisher_csv', methods=['GET'])
@admin_required
def get_donations_from_publisher_csv():
    """
    Returns the url to a CSV with the donation logs
    :param: JWT token for a owner
    :return: JSON object of url
    """
    username = get_jwt_identity()
    exists = Owner.query.filter_by(username=username).first()

    if exists:
        sql_query = '''select donation_date_time, newspaper_article_title, newspaper_article_link, amount_donated,
                                project_name, organization_name, donations.newspaper_id
                                from donations, projects, organizations
                                where donations.project_id=projects.project_id
                                and donations.organization_id=organizations.email
                                and donations.newspaper_id in 
                                    (select publisher_id from Owning where owner_id='{}');'''.format(username)
        conn = db.engine.connect().connection
        donation_df = pd.read_sql(sql_query, conn)

        csv_buffer = StringIO()
        donation_df.to_csv(csv_buffer)
        filename = username + '_payment_logs.csv'
        s3.put_object(Bucket='newspark-charity-data', Key=filename, Body=csv_buffer.getvalue())

        return jsonify({"url": s3.generate_presigned_url('get_object',
                                                         Params={'Bucket': 'newspark-charity-data', 'Key': filename},
                                                         ExpiresIn=300)})
    return jsonify({})


@publisher_blueprint.route('/change_widget_status', methods=['POST'])
@admin_required
def change_widget_status():
    """
    Change the status of the widget for an article
    :param: JWT token for a owner, article link
    :return: Success if widget status changed, Article Not Found if article not found in database,
    or Publisher Not Found if owner not found in database
    """

    username = get_jwt_identity()
    exists = Owner.query.filter_by(username=username).first()

    if exists:
        article_link = request.form.get('article_link')
        article = Article.query.filter_by(article_link=article_link).first()

        if article:
            # Check if the value is in the cache
            if not article.widget_status and redis.exists(article.article_link):
                redis.delete(article.article_link)

            # Checks admin privileges for account
            if username == 'admin':
                article.edited_by_newspark = True

            else:
                article.edited_by_publisher = True

            article.widget_status = not article.widget_status

            db.session.commit()

            return jsonify("Success")

        else:
            return jsonify("Article Not Found")

    else:
        return jsonify("Account Not Found")


@publisher_blueprint.route('/get_articles', methods=['GET'])
@admin_required
def get_articles():
    """
    Gets all of the articles that were published by newspapers owned by the account
    :param: JWT token for a owner
    :return: json object: articles, boolean indicating whether the account belongs to newspark if owner found
    in the database, Account Not Found otherwise
    """

    username = get_jwt_identity()
    exists = Owner.query.filter_by(username=username).first()

    if exists:

        if username == 'admin':
            admin_account = True
        else:
            admin_account = False

        sql_query = '''select donations.donation_id, donations.amount_donated, articles.article_link,
                       articles.article_title, articles.widget_status, publisher_id, date_published,
                       articles.project_id1, articles.project_id2, articles.project_id3, articles.project_id4,
                       articles.project_id5, articles.project_id6, edited_by_newspark, edited_by_publisher 
                       from articles
                       left join donations on donations.newspaper_article_link=articles.article_link where
                       articles.publisher_id in 
                                    (select publisher_id from Owning where owner_id='{}');'''.format(username)
        conn = db.engine.connect().connection
        df = pd.read_sql(sql_query, conn)
        all_articles = []

        unique_articles = list(df['article_link'].unique())

        for i in unique_articles:
            temp = df[df.article_link == i]

            ids = [temp['project_id' + str(i)].iloc[0] for i in range(1, 7)]
            # print(ids)
            count = sum([0 if pd.isnull(idd) else 1 for idd in ids])

            dic = {}
            dic['publisher_name'] = temp['publisher_id'].iloc[0]
            dic['num_projects'] = count
            # dic['date_published'] = temp['date_published'].iloc[0].strftime('%m/%d/%Y')
            dic['date_published'] = temp['date_published'].iloc[0]
            dic['article_link'] = i
            dic['article_title'] = temp['article_title'].iloc[0]
            dic['edited_by_newspark'] = bool(temp['edited_by_newspark'].iloc[0])
            dic['edited_by_publisher'] = bool(temp['edited_by_publisher'].iloc[0])
            dic['widget_status'] = bool(temp['widget_status'].iloc[0])
            dic['revenue'] = int(temp['amount_donated'].sum())
            dic['amount_donations'] = len(temp)
            all_articles.append(dic)

        all_articles = sorted(all_articles, key=lambda x: x['date_published'], reverse=True)

        # for article in all_articles:
        #     print(type(article['date_published']))

        return jsonify(articles=all_articles, admin_account=admin_account)

    else:
        return jsonify("Account Not Found")


@publisher_blueprint.route('/get_articles_csv', methods=['GET'])
@admin_required
def get_articles_csv():
    """
    Returns the url to a CSV with the article logs
    :param: JWT token for a owner
    :return: JSON object of url if owner found, Account Not Found otherwise
    """

    username = get_jwt_identity()
    exists = Owner.query.filter_by(username=username).first()

    if exists:
        sql_query = '''select donations.donation_id, donations.amount_donated, articles.article_link,
                               articles.article_title, articles.widget_status, publisher_id
                               from donations
                               left join articles on donations.newspaper_article_link=articles.article_link where
                               articles.publisher_id in 
                                            (select publisher_id from Owning where owner_id='{}');'''.format(username)
        conn = db.engine.connect().connection
        df = pd.read_sql(sql_query, conn)
        # print(df.head())
        all_articles = []

        unique_articles = list(df['article_link'].unique())

        for i in unique_articles:
            temp = df[df.article_link == i]
            dic = {}
            dic['publisher_name'] = temp['publisher_id'].iloc[0]
            dic['article_link'] = i
            dic['article_title'] = temp['article_title'].iloc[0]
            dic['widget_status'] = bool(temp['widget_status'].iloc[0])
            dic['revenue'] = int(temp['amount_donated'].sum())
            dic['amount_donations'] = len(temp)
            all_articles.append(dic)

        df_csv = pd.DataFrame(all_articles)
        csv_buffer = StringIO()
        df_csv.to_csv(csv_buffer)
        filename = username + '_article_logs.csv'
        s3.put_object(Bucket='newspark-charity-data', Key=filename, Body=csv_buffer.getvalue())

        return jsonify({"url": s3.generate_presigned_url('get_object',
                                                         Params={'Bucket': 'newspark-charity-data', 'Key': filename},
                                                         ExpiresIn=300)})
    else:
        return jsonify('Account Not Found')


@publisher_blueprint.route('/get_relevant_projects', methods=['POST'])
@admin_required
def get_relevant_projects():
    """
    Gets the projects that were recommended for this article
    :param: JWT token for a owner, article link
    :return: JSON object of recommended projects
    """

    username = get_jwt_identity()
    owner = Owner.query.filter_by(username=username).first()
    if owner:
        elements = Owning.query.filter_by(owner_id=username).all()
        publisher_names = [e.publisher_id for e in elements]
        # print(publisher_names)
    else:
        return jsonify('Owner does not exist.')

    article_link = request.form.get('article_link')
    article = Article.query.filter_by(article_link=article_link).first()

    # article exists with this link
    if article:
        article_publisher_name = article.publisher_id
        # print(article_publisher_name)
    else:
        return jsonify('Article does not exist.')

    # publisher belonging to article not among publishers belonging to owner
    if not (article_publisher_name in publisher_names):
        return jsonify('Article does not exist.')

    output = []
    projects = ['project_id' + str(i) for i in range(1, 7)]
    project_info_list = []
    for p in projects:
        sql_query = '''select *
                        from articles, projects, organizations
                        where articles.article_link='{}'
                        and articles.{}=projects.project_id
                        and projects.organization_id=organizations.email
                        '''.format(article_link, p)

        conn = db.engine.connect().connection
        df = pd.read_sql(sql_query, conn)

        df.drop(projects + ['password', 'salt'], axis=1, inplace=True)

        project_info = list(df.T.to_dict().values())
        if len(project_info) != 0:
            project_info_list.append(project_info[0])

        for i in range(len(project_info)):
            project_info[i]['date_published'] = project_info[i]['date_published'].strftime('%m/%d/%Y')

    return jsonify(project_info=project_info_list)


@publisher_blueprint.route('/get_article_info', methods=['POST'])
@admin_required
def get_article_info():
    """
    Get all available information on this article from database
    :param: JWT token for a owner, article link
    :return: JSON object of article information
    """

    username = get_jwt_identity()
    exists = Owner.query.filter_by(username=username).first()

    if exists:
        article_link = request.form.get('article_link')
        article = Article.query.filter_by(article_link=article_link).first()
        article_dict = article.serialize()
        article_dict['date_published'] = article_dict['date_published'].strftime('%m/%d/%Y')

        return jsonify(article_info=article_dict)

    else:
        return jsonify("Account Not Found")


@publisher_blueprint.route('/add_project_to_article', methods=['POST'])
@admin_required
def add_project_to_article():
    """
    Adds project to this article
    :param: JWT token for a owner, article link, project id
    :return: Success if project added to the article
    """

    username = get_jwt_identity()
    exists = Owner.query.filter_by(username=username).first()

    if exists:
        article_link = request.form.get('article_link')
        project_id = int(request.form.get('project_id'))

        article = Article.query.filter_by(article_link=article_link).first()

        if article:
            ids = article.get_project_ids()

            if project_id in ids:
                return jsonify("Project is already suggested.")

            else:
                # project id missing
                if None in ids:
                    ids[ids.index(None)] = project_id

                else:
                    return jsonify("Maximum count of projects.")

            article.project_id1 = ids[0]
            article.project_id2 = ids[1]
            article.project_id3 = ids[2]
            article.project_id4 = ids[3]
            article.project_id5 = ids[4]
            article.project_id6 = ids[5]

            if username == 'admin':
                article.edited_by_newspark = True

            else:
                article.edited_by_publisher = True

            db.session.commit()

            sql_query = '''select project_id
                            from projects, organizations
                            where projects.organization_id=organizations.email
                            and projects.removed=FALSE
                            and organizations.verified=TRUE;'''
            conn = db.engine.connect().connection
            df = pd.read_sql(sql_query, conn)
            other_ids = list(filter(lambda x: not (x in ids), list(df['project_id'])))

            # store recommendations in a json file and upload to a s3 bucket
            update_recommendations(s3_client=s3, article_link=article_link, ids=ids, other_ids=other_ids)

            # Re-run the commands to get the right data for the articles in the cache
            # TODO: set up a celery worker to do all of this
            if redis.exists(article_link):
                redis.delete(article_link)

            project_info_list = get_projects_from_article(article_url=article_link,
                                                          num_ids=application.config['NUM_CHOICES'])
            # Save to redis cache
            redis.set(article_link, pickle.dumps(project_info_list))

            return jsonify("Success")

        else:
            return jsonify("Article does not exist.")

    else:
        return jsonify("Publisher does not exist.")


@publisher_blueprint.route('/remove_project_from_article', methods=['POST'])
@admin_required
def remove_project_from_article():
    """
    Removes project from this article
    :param: JWT token for a owner, article link, project id
    :return: Success if project removed from this article
    """

    username = get_jwt_identity()
    exists = Owner.query.filter_by(username=username).first()

    if exists:
        article_link = request.form.get('article_link')
        project_id = int(request.form.get('project_id'))

        article = Article.query.filter_by(article_link=article_link).first()

        if article:
            ids = article.get_project_ids()

            for i in range(len(ids)):
                if ids[i] == project_id:
                    ids[i] = None

            ids = sorted(ids, key=lambda x: x is None)  # move None's to back

            article.project_id1 = ids[0]
            article.project_id2 = ids[1]
            article.project_id3 = ids[2]
            article.project_id4 = ids[3]
            article.project_id5 = ids[4]
            article.project_id6 = ids[5]

            if username == 'admin':
                article.edited_by_newspark = True

            else:
                article.edited_by_publisher = True

            db.session.commit()

            sql_query = '''select project_id
                            from projects, organizations
                            where projects.organization_id=organizations.email
                            and projects.removed=FALSE
                            and organizations.verified=TRUE;'''
            conn = db.engine.connect().connection
            df = pd.read_sql(sql_query, conn)
            other_ids = list(filter(lambda x: not (x in ids), list(df['project_id'])))

            # store recommendations in a json file and upload to a s3 bucket
            update_recommendations(s3_client=s3, article_link=article_link, ids=ids, other_ids=other_ids)

            # Re-run the commands to get the right data for the articles in the cache
            # TODO: set up a celery worker to do all of this
            if redis.exists(article_link):
                redis.delete(article_link)

            project_info_list = get_projects_from_article(article_url=article_link,
                                                          num_ids=application.config['NUM_CHOICES'])
            # Save to redis cache
            redis.set(article_link, pickle.dumps(project_info_list))

            return jsonify("Success")

        else:
            return jsonify("Article does not exist.")

    else:
        return jsonify("Publisher does not exist.")


@publisher_blueprint.route('/get_projects_for_publisher', methods=['POST'])
@admin_required
def get_projects_for_publisher():
    """
    Get all available projects (not currently recommended) for a publisher owned by the account
    :param: JWT token for a owner, publisher name
    :return: JSON object of available projects
    """

    publisher_name = request.form.get('publisher_name')
    exists = Publisher.query.filter_by(publisher_name=publisher_name).first()

    if exists:
        sql_query = '''select *
                        from organizations, projects
                        where projects.newspaper_id='{}'
                        and projects.organization_id=organizations.email
                        and projects.removed=FALSE
                        and organizations.verified=TRUE;'''.format(publisher_name)

        conn = db.engine.connect().connection
        project_info_df = pd.read_sql(sql_query, conn)

        project_info_df.drop(['password', 'salt'], axis=1, inplace=True)

        return jsonify(project_info=list(project_info_df.T.to_dict().values()))

    else:
        return jsonify('Account Not Found')


@publisher_blueprint.route('/get_publishers', methods=['GET'])
@admin_required
def get_publishers():
    """ Returns information for each publisher belonging to the owner. """

    username = get_jwt_identity()
    exists = Owner.query.filter_by(username=username).first()

    if exists:
        elements = Owning.query.filter_by(owner_id=username).all()
        publisher_names = [e.publisher_id for e in elements]

        publisher_list = []
        for name in publisher_names:
            publisher = Publisher.query.filter_by(publisher_name=name).first()
            publisher_list.append(publisher.serialize())

        return jsonify(publishers=publisher_list)

    else:
        return jsonify("Publisher Does Not Exist")


@publisher_blueprint.route('/get_owner', methods=['GET'])
@admin_required
def get_owner():
    """ Returns the owner's information. """

    username = get_jwt_identity()
    exists = Owner.query.filter_by(username=username).first()

    if exists:
        return jsonify(owner=exists.serialize())

    else:
        return jsonify("Publisher Does Not Exist")


@publisher_blueprint.route('/edit_owner', methods=['POST'])
@admin_required
def edit_owner():
    """ Edits the owner's information. """

    username = get_jwt_identity()
    owner = Owner.query.filter_by(username=username).first()

    if owner:
        password = request.form.get('password')
        if password:
            salt, hashed_password = secure_password(password)
            owner.password = hashed_password
            owner.salt = salt

        owner.email = request.form.get('email')
        owner.phone_number = request.form.get('phone_number')

        db.session.commit()
        return jsonify("Success")
    else:
        return jsonify("Owner Does Not Exist")


@publisher_blueprint.route('/edit_payment_info_publisher', methods=['POST'])
@admin_required
def edit_payment_info_publisher():
    """
    Store payment information in a s3 bucket
    :param: JWT token for a owner, publisher name
    :return: Success if payment information added, No Account Found if owner not found in database
    """

    username = get_jwt_identity()
    exists = Owner.query.filter_by(username=username).first()

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
                          publisher_charity='publisher',
                          primary_id=username)

        return jsonify("Success")

    else:
        return jsonify("No Account Found")
