from flask import Flask, request, jsonify, Blueprint, render_template
from app.models import *
from app.helper.scrapers import emory_scraper, indiana_scraper
from app.helper.fund_matching import get_best_fund
from app.helper.misc import save_article_data
from app import redis
from datetime import datetime
from app import s3
from flask_mail import Message
from app import application
from app import mail
import pickle
import pandas as pd
import requests

# Create Blueprint
funds_blueprint = Blueprint('funds', __name__)


@funds_blueprint.route('/get_fund', methods=['POST'])
def get_fund():
    article_url = request.form.get('article_link')

    if redis.exists(article_url):
        # Get from the redis cache
        fund_match = pickle.loads(redis.get(article_url))
        return jsonify(fund=fund_match)

    else:
        print('checking article')
        # Check the article
        article = Article.query.filter_by(article_link=article_url).first()

        # article exists
        if article and article.fund_name is not None:
            print('article exists')
            widget_status = article.widget_status
            print(widget_status)
            if widget_status:
                fund = Fund.query.filter_by(fund_name=article.fund_name).first()
                # Save to redis cache
                redis.set(article_url, pickle.dumps(fund.serialize()))
                return jsonify(fund=fund.serialize())

        else:
            article_title = request.form.get('article_title')
            article_text = request.form.get('article_text')

            if 'emorywheel' in article_url:
                publisher_id = 'The Emory Wheel'

            else:
                publisher_id = 'Indiana Daily Student'

            if article_title is None:

                if publisher_id == 'The Emory Wheel':
                    article_info = emory_scraper(article_url)

                else:
                    article_info = indiana_scraper(article_url)

                article_title = article_info['title']
                article_text = article_info['content']
                article_text = article_text[:len(article_text) // 2]

            else:
                article_title = article_title.lower()
                article_text = article_text.lower()[:len(article_text) // 2]

                # store article data in a json file and upload to a s3 bucket
                # save_article_data(s3_client=s3, article_link=article_url, article_title=article_title,
                #                   article_date_time=datetime.now(), article_text=article_text)

            fund = get_best_fund(article_text)

            # fund name is null
            if article:
                article.fund_name = fund.fund_name

            else:
                # Add to database
                article = Article(
                    article_link=article_url,
                    article_title=article_title,
                    publisher_id=publisher_id,
                    widget_status=True,
                    date_published=datetime.now(),
                    fund_name=fund.fund_name,
                    project_id1=None,
                    project_id2=None,
                    project_id3=None,
                    project_id4=None,
                    project_id5=None,
                    project_id6=None,
                    edited_by_publisher=False,
                    edited_by_newspark=False,
                )
                db.session.add(article)

            db.session.commit()

            redis.set(article_url, pickle.dumps(fund.serialize()))
            return jsonify(fund=fund.serialize())


@funds_blueprint.route('/get_charities_for_fund', methods=['POST'])
def get_charities_for_fund():
    fund_name = request.form.get('fund_name')

    sql_query = '''select organization_name, organization_website
                    from organizations, funding
                    where organizations.email=funding.organization_id
                    and funding.fund_id='{}';'''.format(fund_name)
    conn = db.engine.connect().connection
    df = pd.read_sql(sql_query, conn)

    return jsonify(charities=list(df.T.to_dict().values()))


@funds_blueprint.route('/fund_payment_update', methods=['POST'])
def fund_payment_update():
    fund_name = request.form.get('fund_name')
    donor_name = request.form.get('name')
    donor_email = request.form.get('email')
    newspaper_article_link = request.form.get('article_link')
    amount_donated = float(request.form.get('amount'))
    amount_paid_to_charity = 0.92 * amount_donated  # $9.20
    amount_paid_to_publisher = 0.04 * amount_donated  # $0.40
    donation_date_time = datetime.now()

    # check if fund exists
    fund = Fund.query.filter_by(fund_name=fund_name).first()
    if fund is None:
        return jsonify("Fund Does Not Exist.")

    # check if article exists
    article = Article.query.filter_by(article_link=newspaper_article_link).first()
    if article:
        newspaper_id = article.publisher_id
        newspaper_article_title = article.article_title

    else:
        return jsonify("Article Does Not Exist.")

    publisher = Publisher.query.filter_by(publisher_name=newspaper_id).first()
    if publisher:
        publisher.commissions_available += amount_paid_to_publisher
        publisher.commissions_raised += amount_paid_to_publisher

    else:
        return jsonify("Publisher Does Not Exist")

    organizations = Organization.query.all()
    organization_map = {}
    for org in organizations:
        organization_map[org.email] = org

    # join funds with organizations
    fund_relations = Funding.query.all()
    organizations_from_fund = []
    for f in fund_relations:
        organization_id, fund_id = f.organization_id, f.fund_id
        if fund_id == fund_name:
            if organization_id in organization_map:
                org = organization_map[organization_id]
                organizations_from_fund.append(org)

    if len(organizations_from_fund) == 0:
        return jsonify('No organizations in the fund.')

    # update amount raised for each org that belongs to the fund and add donation
    amount_per_organization = amount_paid_to_charity / len(organizations_from_fund)
    for org in organizations_from_fund:
        org.total_amount_raised += amount_per_organization
        org.funds_available += amount_per_organization

        donation = Donation(
            organization_id=org.email,
            project_id=None,
            fund_name=fund_name,
            donation_date_time=donation_date_time,
            donor_name=donor_name,
            donor_email=donor_email,
            amount_donated=amount_per_organization,
            newspaper_id=newspaper_id,
            newspaper_article_title=newspaper_article_title,
            newspaper_article_link=newspaper_article_link
        )

        db.session.add(donation)

    db.session.commit()

    # send the donor an email
    msg = Message()
    msg.subject = 'Thank you for Donating!'
    msg.html = render_template('payment_funds.html', name=donor_name, amount=float(amount_donated), fund=fund_name)

    msg.recipients = [donor_email]
    msg.bcc = ["founders@newspark.us"]
    msg.sender = "founders@newspark.us"
    mail.send(msg)

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

    return jsonify("Success")
