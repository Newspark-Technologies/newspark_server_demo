from flask import Flask, request, jsonify, Blueprint, render_template
from app.helper.nlp import full_json_with_matching
from app.models import *
from app.helper.scrapers import indiana_scraper, emory_scraper
from app.helper.misc import get_projects_from_article, get_available_projects, save_article_data
from app import s3
from datetime import datetime
from app import application
from flask_mail import Message
from app import mail
from app import redis
import pickle
import requests
import pandas as pd
import stripe

# Create Blueprint
widget_blueprint = Blueprint('widget', __name__)


@widget_blueprint.route('/get_charities', methods=['POST'])
def get_charities():
    """
    Gets the recommended projects for an article.
    :param: request.form params: article link
    :return: Info for each recommended project.
    """

    return jsonify([])

    charity_amount = application.config['CHARITY_AMOUNT']
    num_choices = application.config['NUM_CHOICES']

    article_url = request.form.get('article_link').split('?')[0]
    article_url = article_url.split('#')[0]

    if redis.exists(article_url):
        # Get from the redis cache
        charity_match = pickle.loads(redis.get(article_url))
        return jsonify(charity_match)

    else:
        print('checking article')
        # Check the article
        article = Article.query.filter_by(article_link=article_url).first()

        # article exists
        if article:
            print('article exists')
            widget_status = article.widget_status
            print(widget_status)
            if widget_status:
                # get number of ids that are not null and assume nulls follow consecutively
                project_ids = article.get_project_ids()
                if None in project_ids:
                    num_ids = project_ids.index(None)
                else:
                    num_ids = charity_amount

                project_info_list = get_projects_from_article(article_url=article_url, num_ids=num_ids)
                # Save to redis cache
                redis.set(article_url, pickle.dumps(project_info_list))

                return jsonify(project_info_list)
            else:
                return jsonify([])

        else:
            widget_status = True
            article_title = request.form.get('article_title')

            # testing client on local host
            if article_title == '':
                article_info = indiana_scraper(article_url)
                article_title = article_info['title']
                article_date_time = article_info['date']

            else:
                article_date_time = datetime.strptime(request.form.get('article_date'), "%b %d %Y")
                article_text = request.form.get('article_text').replace(u'\xa0', u'')

                # store article data in a json file and upload to a s3 bucket
                save_article_data(s3_client=s3, article_link=article_url, article_title=article_title,
                                  article_date_time=article_date_time, article_text=article_text)

                # turn off widget for too old articles
                date_cut_off = datetime.strptime('Jun 28 2020', '%b %d %Y')
                if article_date_time < date_cut_off:
                    widget_status = False

            # select projects that are not removed and are from verified charities
            projects_df = get_available_projects()

            project_ids = [None for i in range(charity_amount)]
            matching_project_ids = full_json_with_matching(projects_df, article_title,
                                                           num_choices)  # relevant project ids
            for i in range(len(matching_project_ids)):
                project_ids[i] = matching_project_ids[i]

            # all_project_ids = list(projects_df['project_id'])
            # project_ids = [None for i in range(charity_amount)]
            # random_project_ids = random.sample(all_project_ids, num_choices)
            # for i in range(len(random_project_ids)):
            #     project_ids[i] = random_project_ids[i]

            # Add to database
            article = Article(
                article_link=article_url,
                article_title=article_title,
                publisher_id="Indiana Daily Student",
                widget_status=widget_status,
                date_published=article_date_time,
                fund_name=None,
                project_id1=project_ids[0],
                project_id2=project_ids[1],
                project_id3=project_ids[2],
                project_id4=project_ids[3],
                project_id5=project_ids[4],
                project_id6=project_ids[5],
                edited_by_publisher=False,
                edited_by_newspark=False,
            )

            db.session.add(article)
            db.session.commit()

            if widget_status:
                project_info_list = get_projects_from_article(article_url=article_url, num_ids=num_choices)
                # Save to redis cache
                redis.set(article_url, pickle.dumps(project_info_list))
                return jsonify(project_info_list)

            else:
                return jsonify([])


@widget_blueprint.route('/pay', methods=['POST'])
def pay():
    amount = request.form.get('amount')
    amount_converted = int(float(amount) * 100)
    stripe.api_key = application.config['STRIPE_API_KEY']

    try:
        intent = stripe.PaymentIntent.create(
            amount=amount_converted,
            currency='usd',
            payment_method_types=['card'],
            statement_descriptor="Newspark Inc."
        )
        money_details = {'amount': amount_converted / 100.0, 'intentSecret': intent.client_secret}
        return jsonify(money_details)

    except Exception as e:
        return jsonify(error=str(e)), 403


@widget_blueprint.route('/update_db_after_payment', methods=['POST'])
def update_db_after_payment():
    organization_id = request.form.get('organization_id')
    project_id = request.form.get('project_id')
    donor_name = request.form.get('name')
    donor_email = request.form.get('email')
    newspaper_article_link = request.form.get('article_link')
    amount_donated = float(request.form.get('amount'))
    amount_paid_to_charity = 0.92 * amount_donated  # $9.20
    amount_paid_to_publisher = 0.04 * amount_donated  # $0.40
    donation_date_time = datetime.now()

    article = Article.query.filter_by(article_link=newspaper_article_link).first()
    if article:
        newspaper_id = article.publisher_id
        newspaper_article_title = article.article_title

    else:
        return jsonify("Article Does Not Exist.")

    organization = Organization.query.filter_by(email=organization_id).first()
    if organization:
        organization.total_amount_raised += amount_paid_to_charity

    else:
        return jsonify("Organization Does Not Exist.")

    project = Project.query.filter_by(project_id=project_id).first()
    if project:
        project.project_raised += amount_paid_to_charity
        project.funds_available += amount_paid_to_charity

    else:
        return jsonify("Initiative Does Not Exist.")

    publisher = Publisher.query.filter_by(publisher_name=newspaper_id).first()
    if publisher:
        publisher.commissions_available += amount_paid_to_publisher
        publisher.commissions_raised += amount_paid_to_publisher

    else:
        return jsonify("Publisher Does Not Exist")

    # need to make sure the 4 foreign keys reference existing values before adding the donation
    donation = Donation(
        organization_id=organization_id,
        project_id=project_id,
        fund_name=None,
        donation_date_time=donation_date_time,
        donor_name=donor_name,
        donor_email=donor_email,
        amount_donated=amount_donated,
        newspaper_id=newspaper_id,
        newspaper_article_title=newspaper_article_title,
        newspaper_article_link=newspaper_article_link
    )

    # send the donor an email
    msg = Message()
    msg.subject = 'Thank you for Donating!'
    msg.html = render_template('payment.html', name=donor_name,
                               amount=int(amount_donated), project=project.project_name,
                               organization=organization.organization_name)

    msg.recipients = [donor_email]
    msg.bcc = ["founders@newspark.us"]
    msg.sender = "founders@newspark.us"
    mail.send(msg)

    db.session.add(donation)
    db.session.commit()

    # subscribe donor to newsletter
    url = 'https://us10.api.mailchimp.com/3.0/lists/9f21c018ec/members/'
    data = {
        "email_address": donor_email,
        "status": "subscribed",
        "merge_fields": {
            "FNAME": donor_name.split(' ')[0],
            "LNAME": donor_name.split(' ')[1]
        }
    }
    r = requests.post(url, json=data, auth=('newspark', application.config['MAILCHIMP_API_KEY']))
    # print(r.status_code)

    return jsonify("Success")
