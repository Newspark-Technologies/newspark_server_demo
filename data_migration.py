import os
import hashlib
import datetime
import pandas as pd
from app.models import *
from app import redis


def secure_password(password):
    salt = os.urandom(32)  # 32 bytes
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)  # 64 bytes
    return salt, key


def create_admin_owner():
    salt, hashed_password = secure_password('Newspark2020#')

    owner = Owner(
        username='admin',
        email='founders@newspark.us',
        password=hashed_password,
        salt=salt,
        phone_number='917-363-4115',
        admin_access=True)

    db.session().add(owner)
    db.session.commit()

    return None


def generate_publishers():
    publisher_list = [
        {
            "publisher_name": "Indiana Daily Student",
            "website": "https://www.idsnews.com/",
            "school": "Indiana",
            "street_address": "601 E. Kirkwood Ave.",
            "city": "Bloomington",
            "state": "Indiana"
        },
        {
            "publisher_name": "The Emory Wheel",
            "website": "https://emorywheel.com",
            "school": "Emory",
            "street_address": "605 Asbury Circle, Drawer W",
            "city": "Atlanta",
            "state": "Georgia",
        },
    ]

    num_rows = len(publisher_list)
    usernames = ['greg', 'vivek']
    emails = ['gmenkedi@indiana.edu', 'vivrao@iu.edu']
    passwords = ['password' for i in range(num_rows)]
    publisher_names = []

    for i in range(num_rows):
        publisher_dict = publisher_list[i]
        publisher_names.append(publisher_dict['publisher_name'])
        salt, hashed_password = secure_password(passwords[i])

        publisher = Publisher(
            publisher_name=publisher_names[i],
            school=publisher_dict['school'],
            publisher_website=publisher_dict['website'],
            publisher_phone_number=None,
            publisher_street_address=publisher_dict['street_address'],
            publisher_city=publisher_dict['city'],
            publisher_state=publisher_dict['state'],
            publisher_country="United States",
            commissions_raised=0.0,
            commissions_available=0.0,
        )

        db.session().add(publisher)

        # create owner for newspaper
        owner = Owner(
            username=usernames[i],
            email=emails[i],
            password=hashed_password,
            salt=salt,
            phone_number=None,
            admin_access=True)

        db.session().add(owner)
        db.session.commit()

        # create relationship
        owning = Owning(
            owner_id=usernames[i],
            publisher_id=publisher_names[0]
        )

        db.session().add(owning)

    db.session.commit()

    for i in publisher_names:
        owning = Owning(
            owner_id='admin',
            publisher_id=i
        )
        db.session().add(owning)

    db.session.commit()

    return None


def generate_organizations():
    df = pd.read_csv('data/organization.csv')

    for index, row in df.iterrows():

        if pd.isnull(row['year_established']):
            row['year_established'] = 2020

        organization = Organization(
            email=row['email'],
            password=eval(row['password']),
            salt=eval(row['salt']),
            phone_number=row['phone_number'],
            organization_name=row['organization_name'],
            organization_website=row['organization_website'],
            organization_description=row['organization_description'],
            organization_street_address=row['organization_street_address'],
            organization_city=row['organization_city'],
            organization_state=row['organization_state'],
            organization_country=row['organization_country'],
            organization_type=row['organization_type'],
            employer_id_number=row['employer_id_number'],
            verified=row['verified'],
            year_established=row['year_established'],
            total_amount_raised=0.0,
            funds_available=0.0,
        )

        db.session().add(organization)

    db.session.commit()

    return None


def generate_projects():
    df = pd.read_csv('data/project.csv')

    for index, row in df.iterrows():
        project = Project(
            organization_id=row['organization_id'],
            project_name=row['project_name'],
            project_short_description=row['project_description'][:150],
            project_description=row['project_description'],
            project_picture_link=row['project_picture_link'],
            project_goal=row['project_goal'],
            project_raised=row['project_raised'],
            project_city=row['project_city'],
            project_state=row['project_state'],
            project_country=row['project_country'],
            newspaper_id=row['newspaper_id'],
            removed=row['removed'],
        )

        db.session().add(project)

    db.session.commit()

    return None


def generate_articles():
    df = pd.read_csv('data/article.csv')

    article_links = ['https://www.idsnews.com/article/2020/06/iu-professors-voice-concerns-about-fall-semester-plan',
                     'https://www.idsnews.com/article/2020/07/theatre-drama-department-commits-to-change-over-lack-of-diversity-inclusion',
                     'https://www.idsnews.com/article/2020/07/international-students-faced-with-a-terrible-decision-degrees-or-deportation',
                     'https://www.idsnews.com/article/2020/07/opinion-5-things-we-can-do-to-make-antiracism-a-more-enduring-part-of-white-life']

    for index, row in df.iterrows():

        if row['article_link'] not in article_links:
            continue

        if pd.isnull(row['project_id1']):
            row['project_id1'] = None

        if pd.isnull(row['project_id2']):
            row['project_id2'] = None

        if pd.isnull(row['project_id3']):
            row['project_id3'] = None

        if pd.isnull(row['project_id4']):
            row['project_id4'] = None

        if pd.isnull(row['project_id5']):
            row['project_id5'] = None

        if pd.isnull(row['project_id6']):
            row['project_id6'] = None

        row['date_published'] = datetime.datetime.now().date()

        article = Article(
            article_link=row['article_link'],
            article_title=row['article_title'],
            publisher_id=row['publisher_id'],
            widget_status=row['widget_status'],
            date_published=row['date_published'],
            fund_name=None,
            project_id1=row['project_id1'],
            project_id2=row['project_id2'],
            project_id3=row['project_id3'],
            project_id4=row['project_id4'],
            project_id5=row['project_id5'],
            project_id6=row['project_id6'],
            edited_by_publisher=row['edited_by_publisher'],
            edited_by_newspark=row['edited_by_newspark'],
        )

        db.session().add(article)

    db.session.commit()

    return None


def generate_donations():
    df = pd.read_csv('data/donation.csv')

    for index, row in df.iterrows():

        donation = Donation(
            organization_id=row['organization_id'],
            project_id=row['project_id'],
            fund_name=None,
            donation_date_time=row['donation_date_time'],
            donor_name=row['donor_name'],
            donor_email=row['donor_email'],
            amount_donated=row['amount_donated'],
            newspaper_id=row['newspaper_id'],
            newspaper_article_title=row['newspaper_article_title'],
            newspaper_article_link=row['newspaper_article_link'],
        )

        db.session().add(donation)

    db.session.commit()

    return None


def clear_articles():
    sql_query = '''select articles.article_link 
                    from donations left join articles on donations.newspaper_article_link=articles.article_link;'''

    conn = db.engine.connect().connection
    df = pd.read_sql(sql_query, conn)
    article_links = list(df['article_link'])

    articles = Article.query.all()

    for a in articles:
        if a.article_link not in article_links:
            db.session.delete(a)

    db.session.commit()

    return None


def clear_cache():
    for i in redis.keys():
        redis.delete(i)


def create_owner(username, email, admin_access, publisher_name):

    salt, hashed_password = secure_password('password')
    # create owner for newspaper
    owner = Owner(
        username=username,
        email=email,
        password=hashed_password,
        salt=salt,
        phone_number=None,
        admin_access=admin_access)

    db.session().add(owner)
    db.session.commit()

    # create relationship
    owning = Owning(
        owner_id=username,
        publisher_id=publisher_name
    )

    db.session().add(owning)
    db.session.commit()

    return None


def create_more_owners():

    create_owner(username='jsoper',
                 email='jsoper@indiana.edu',
                 admin_access=True,
                 publisher_name="Indiana Daily Student")

    create_owner(username='maston',
                 email='maston@indiana.edu',
                 admin_access=True,
                 publisher_name="Indiana Daily Student")

    create_owner(username='idsmrktg',
                 email='marketing@idsnews.com',
                 admin_access=False,
                 publisher_name="Indiana Daily Student")

    return None


def create_charity():

    email = ''
    salt, hashed_password = secure_password('password')
    phone_number = '{}-{}-{}'.format('', '', '')
    organization_name = ''
    organization_website = ''
    organization_description = ''
    organization_street_address = ''
    organization_city = ''
    organization_state = ''
    organization_country=''
    organization_type = 'Non-profit'
    employer_id_number = '{}-{}'.format('', '')
    year_established = 2020

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
        total_amount_raised=0.0,
        funds_available=0.0,
    )

    db.session().add(organization)
    db.session.commit()

    return None


def verify_charity(email):
    org = Organization.query.filter_by(email=email).first()
    org.verified = True
    db.session.commit()
    return None


def remove_project(project_id):
    project = Project.query.filter_by(project_id=project_id).first()
    db.session.delete(project)
    db.session.commit()
    return None


def generate_funds():
    fund_list = [
        {
            "fund_name": "Racial Justice Fund",
            "fund_topic": "racial justice",
            "fund_description": None,
            "fund_picture_link": "https://ibb.co/ZmyXvDw",
        },
        {
            "fund_name": "Coronavirus Relief Fund",
            "fund_topic": "Coronavirus",
            "fund_description": None,
            "fund_picture_link": "https://ibb.co/ZmyXvDw",
        },
        {
            "fund_name": "Local Community Fund",
            "fund_topic": "the local community",
            "fund_description": None,
            "fund_picture_link": "https://ibb.co/ZmyXvDw",
        },
        {
            "fund_name": "Environmental Fund",
            "fund_topic": "the environment",
            "fund_description": None,
            "fund_picture_link": "https://ibb.co/ZmyXvDw",
        },
        {
            "fund_name": "World Fund",
            "fund_topic": "the world",
            "fund_description": None,
            "fund_picture_link": "https://ibb.co/ZmyXvDw",
        },
    ]

    for f in fund_list:
        fund = Fund(
            fund_name=f['fund_name'],
            fund_topic=f['fund_topic'],
            fund_description=f['fund_description'],
            fund_picture_link=f['fund_picture_link'],
            total_amount_raised=0.0,
        )
        db.session().add(fund)
    db.session.commit()

    return None


def assign_funds():
    df = pd.read_csv('fund_assignments.csv')

    for row in df.iterrows():
        fund_id, organization_id = row[1][0], row[1][1]

        funding = Funding(
            fund_id=fund_id,
            organization_id=organization_id,
        )
        db.session().add(funding)
    db.session.commit()

    return None


def create_data():
    db.drop_all()
    db.create_all()

    create_admin_owner()
    print("CREATED ADMIN ACCOUNT TO MANAGE PUBLISHERS")

    generate_publishers()
    print("CREATED PUBLISHERS")

    generate_organizations()
    print("CREATED ORGANIZATIONS")

    generate_projects()
    print("CREATED PROJECTS")

    generate_articles()
    print("CREATED ARTICLES")

    generate_donations()
    print("CREATED DONATIONS")

    create_more_owners()
    print("CREATED MORE OWNERS")

    generate_funds()
    print("CREATED FUNDS")

    assign_funds()
    print("ASSIGNED ORGANIZATIONS TO FUNDS")

    return None


if __name__ == "__main__":

    # clear_cache()
    # clear_articles()
    create_data()

