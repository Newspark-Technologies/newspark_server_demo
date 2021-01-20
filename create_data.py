import random
import string
import pandas as pd
from datetime import datetime, timedelta
from app.models import *
from random import sample
from app.helper.misc import *


def save_to_file(f_name, data):
    with open(f_name, 'w') as f:
        json.dump(data, f, indent=4)


def generate_random_text(size, num_rows):
    return [''.join([str(random.choice(string.ascii_letters)) for j in range(size)]) for i in range(num_rows)]


def generate_random_sentences(size, num_rows):
    random_text = generate_random_text(size, num_rows)
    random_sentences = []
    for row in random_text:
        modified_row = ' '.join([row[i:i + 8] for i in range(0, len(row), 8)])[:size]
        random_sentences.append(modified_row)

    return random_sentences


def randomDate(start_date, end_date):
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    random_number_of_days = random.randrange(days_between_dates)
    random_date = start_date + timedelta(days=random_number_of_days)
    random_date = random_date.replace(hour=0, minute=0, second=0, microsecond=0)
    return random_date


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
    usernames = generate_random_text(12, num_rows)
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
            email=None,
            password=hashed_password,
            salt=salt,
            phone_number=None,
            admin_access=True)

        db.session().add(owner)
        db.session.commit()

        # create relationship
        owning = Owning(
            owner_id=usernames[i],
            publisher_id=publisher_names[i]
        )

        db.session().add(owning)

        # create admin relationship
        owning = Owning(
            owner_id='admin',
            publisher_id=publisher_names[i]
        )

        db.session().add(owning)
        db.session.commit()

    return publisher_names


def generate_organizations(num_rows):
    emails = [''.join([str(random.choice(string.ascii_letters)) for j in range(8)]) + "@gmail.com" \
              for i in range(num_rows)]

    if len(set(emails)) != len(emails):
        raise Exception("Sorry the emails are not unique")

    # passwords = generate_random_text(12, num_rows)
    passwords = ['password' for i in range(num_rows)]
    phone_numbers = [''.join([str(random.choice(range(10))) for j in range(10)]) for i in range(num_rows)]
    org_website_links = ['https://www.google.com/' for i in range(num_rows)]
    org_names = generate_random_text(12, num_rows)
    org_descriptions = generate_random_sentences(450, num_rows)
    org_street_addresses = generate_random_text(12, num_rows)
    org_cities = generate_random_text(12, num_rows)
    org_states = generate_random_text(12, num_rows)
    org_countries = generate_random_text(12, num_rows)

    types = ['Non-profit', 'Business']
    org_types = [random.choice(types) for i in range(num_rows)]

    funds = Fund.query.all()

    for i in range(num_rows):
        salt, hashed_password = secure_password(passwords[i])

        employer_id_number = ''.join([str(random.choice(range(10))) for i in range(2)]) + "-" + ''.join(
            [str(random.choice(range(10))) for i in range(7)])

        organization_description = org_descriptions[i]

        if len(organization_description) > 450:
            organization_description = organization_description[:450]

        organization = Organization(
            email=emails[i],
            password=hashed_password,
            salt=salt,
            phone_number=phone_numbers[i],
            organization_name=org_names[i],
            organization_website=org_website_links[i],
            organization_description=organization_description,
            organization_street_address=org_street_addresses[i],
            organization_city=org_cities[i],
            organization_state=org_states[i],
            organization_country=org_countries[i],
            organization_type=org_types[i],
            employer_id_number=employer_id_number,
            verified=True,
            year_established=random.choice([i for i in range(2000, 2021)]),
            total_amount_raised=0.0,
            funds_available=0.0,
        )

        db.session().add(organization)
        db.session.commit()

        random_fund = random.choice(funds)
        fund_id = random_fund.fund_name

        funding = Funding(
            fund_id=fund_id,
            organization_id=emails[i]
        )

        db.session().add(funding)

    db.session.commit()

    return emails


def generate_projects(org_ids, newspaper_ids):
    projects_df = pd.read_json('charities/us_global_giving_charities.json')
    num_rows = projects_df.shape[0]

    ids = [i + 1 for i in range(num_rows)]
    ids_from_org = [random.choice(org_ids) for i in range(num_rows)]
    project_names = list(projects_df['project_name'])
    project_descriptions = list(projects_df['project_description'])
    project_pictures = [p for p in list(projects_df['project_logo_link'])]
    project_goals = [int(i[1:].replace(',', '')) for i in projects_df['project_goal']]
    project_cities = generate_random_text(12, num_rows)
    project_states = ['New York' for i in range(num_rows)]
    project_countries = list(projects_df['project_country'])
    newspaper_names = [random.choice(newspaper_ids) for i in range(num_rows)]

    for i in range(num_rows):

        project_description = project_descriptions[i]

        if len(project_description) > 600:
            project_description = project_description[:600]

        project = Project(
            organization_id=ids_from_org[i],
            project_name=project_names[i],
            project_short_description=project_description[:150],
            project_description=project_description,
            project_picture_link=project_pictures[i],
            project_goal=project_goals[i],
            project_raised=0,
            project_city=project_cities[i],
            project_state=project_states[i],
            project_country=project_countries[i],
            newspaper_id=newspaper_names[i],
            removed=False
        )

        db.session().add(project)

    db.session.commit()

    return ids


def generate_articles(publisher_ids, num_rows=100):
    article_links = generate_random_text(12, num_rows)
    article_titles = generate_random_text(12, num_rows)
    ids_from_publishers = [random.choice(publisher_ids) for i in range(num_rows)]
    date_times = [datetime.strptime(f'{random.choice(["Dec", "May", "Jul"])} {random.choice(range(1, 29))} \
    {random.choice(range(2005, 2021))}', "%b %d %Y") for i in range(num_rows)]
    funds = Fund.query.all()
    for i in range(num_rows):
        publisher_id = ids_from_publishers[i]
        projects = sample([p for p in Project.query.filter_by(newspaper_id=publisher_id).all()], 6)
        random_fund = random.choice(funds)

        article = Article(
            article_link=article_links[i],
            article_title=article_titles[i],
            publisher_id=publisher_id,
            widget_status=True,
            date_published=date_times[i],
            fund_name=random_fund.fund_name,
            project_id1=projects[0].project_id,
            project_id2=projects[1].project_id,
            project_id3=projects[2].project_id,
            project_id4=projects[3].project_id,
            project_id5=projects[4].project_id,
            project_id6=projects[5].project_id,
            edited_by_publisher=False,
            edited_by_newspark=False,
        )
        db.session().add(article)
    db.session.commit()

    return article_links


def generate_donations(org_ids, article_ids, num_rows):
    ids = [i + 1 for i in range(num_rows)]

    # ids_from_projects = [random.choice(project_ids) for i in range(num_rows)]
    ids_from_orgs = [random.choice(org_ids) for i in range(num_rows)]
    date_times = [randomDate(start_date=(datetime.now() - timedelta(days=365)), \
                             end_date=datetime.now()) for i in range(num_rows)]
    donor_names = generate_random_text(12, num_rows)
    donor_emails = ['newspark.info@gmail.com' for i in range(num_rows)]
    amounts = [random.choice(range(100, 200)) for i in range(num_rows)]
    # newspaper_names = [random.choice(newspaper_ids) for i in range(num_rows)]
    newspaper_article_titles = generate_random_text(12, num_rows)
    ids_from_articles = [random.choice(article_ids) for i in range(num_rows)]

    for i in range(num_rows):
        amount = amounts[i]
        organization_id = ids_from_orgs[i]

        project = random.choice([p for p in Project.query.filter_by(organization_id=organization_id).all()])
        project.project_raised += amount

        project_id = project.project_id
        newspaper_id = project.newspaper_id

        donation = Donation(
            organization_id=organization_id,
            project_id=project_id,
            fund_name=None,
            donation_date_time=date_times[i],
            donor_name=donor_names[i],
            donor_email=donor_emails[i],
            amount_donated=amount,
            newspaper_id=newspaper_id,
            newspaper_article_title=newspaper_article_titles[i],
            newspaper_article_link=ids_from_articles[i]
        )

        db.session().add(donation)

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


def generate_crowd_funding_newspaper():
    publisher = Publisher(
        publisher_name= 'Newspark Crowdfunding',
        school=None,
        publisher_website='crowdfunding.newspark.us',
        publisher_phone_number=None,
        publisher_street_address='21 East 90th st',
        publisher_city='New York',
        publisher_state='New York',
        publisher_country="United States",
        commissions_raised=0.0,
        commissions_available=0.0,
    )

    db.session().add(publisher)
    db.session.commit()

    owning = Owning(
        owner_id='admin',
        publisher_id='Newspark Crowdfunding'
    )

    db.session().add(owning)
    db.session.commit()


def generate_article_for_project():
    projects = Project.query.all()
    unique_project_names = set()

    for project in projects:
        project_name = project.project_name

        if project_name not in unique_project_names:
            unique_project_names.add(project_name)

        else:
            continue

        article = Article(
            article_link=project.project_name,
            article_title=project.project_name,
            publisher_id='Newspark Crowdfunding',
            widget_status=True,
            date_published=datetime.now(),
            fund_name=None,
            project_id1=project.project_id,
            project_id2=None,
            project_id3=None,
            project_id4=None,
            project_id5=None,
            project_id6=None,
            edited_by_publisher=False,
            edited_by_newspark=False
        )

        db.session.add(article)
    db.session.commit()


def create_data():

    db.drop_all()
    db.create_all()

    random.seed(34)

    create_admin_owner()
    print("CREATED ADMIN ACCOUNT TO MANAGE PUBLISHERS")

    generate_crowd_funding_newspaper()
    print("CREATED CROWD FUNDING NEWSPAPER")

    publisher_ids = generate_publishers()
    print("CREATED PUBLISHERS")

    generate_funds()
    print("CREATED FUNDS")

    org_ids = generate_organizations(num_rows=20)
    print("CREATED ORGANIZATIONS")

    project_ids = generate_projects(org_ids, publisher_ids)
    print("CREATED PROJECTS")

    article_ids = generate_articles(publisher_ids, num_rows=50)
    print("CREATED ARTICLES")

    generate_donations(org_ids, article_ids, num_rows=50)
    print("CREATED DONATIONS")

    generate_article_for_project()
    print("CREATED ARTICLES FOR EVERY PROJECT")

    return None


if __name__ == "__main__":
    create_data()
