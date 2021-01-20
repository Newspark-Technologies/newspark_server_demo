from app import db


class Organization(db.Model):
    __tablename__ = 'organizations'

    email = db.Column(db.String(), primary_key=True)
    password = db.Column(db.LargeBinary, nullable=False)
    salt = db.Column(db.LargeBinary, nullable=False)
    phone_number = db.Column(db.String(), nullable=True)
    organization_name = db.Column(db.String(), nullable=False, unique=False)
    organization_website = db.Column(db.String(), nullable=False)
    organization_description = db.Column(db.String(), nullable=False)
    organization_street_address = db.Column(db.String(), nullable=False)
    organization_city = db.Column(db.String(), nullable=False)
    organization_state = db.Column(db.String(), nullable=False)
    organization_country = db.Column(db.String(), nullable=False)
    organization_type = db.Column(db.String(), nullable=False)
    employer_id_number = db.Column(db.String(), nullable=True)
    verified = db.Column(db.Boolean, nullable=False)
    year_established = db.Column(db.Integer, nullable=True)
    funds_available = db.Column(db.Float(), nullable=False)
    total_amount_raised = db.Column(db.Float(), nullable=False)

    def __init__(self, email, password, salt, phone_number, organization_name, organization_website, \
                 organization_description, organization_street_address, organization_city, organization_state, \
                 organization_country, organization_type, employer_id_number, verified, year_established,
                 total_amount_raised, funds_available):
        self.email = email
        self.password = password
        self.salt = salt
        self.phone_number = phone_number
        self.organization_name = organization_name
        self.organization_website = organization_website
        self.organization_description = organization_description
        self.organization_street_address = organization_street_address
        self.organization_city = organization_city
        self.organization_state = organization_state
        self.organization_country = organization_country
        self.organization_type = organization_type
        self.employer_id_number = employer_id_number
        self.verified = verified
        self.year_established = year_established
        self.total_amount_raised = total_amount_raised
        self.funds_available = funds_available

    def serialize(self):
        return {
            'email': self.email,
            'phone_number': self.phone_number,
            'organization_name': self.organization_name,
            'organization_website': self.organization_website,
            'organization_description': self.organization_description,
            'organization_street_address': self.organization_street_address,
            'organization_city': self.organization_city,
            'organization_state': self.organization_state,
            'organization_country': self.organization_country,
            'organization_type': self.organization_type,
            'employer_id_number': self.employer_id_number,
            'verified': self.verified,
            'year_established': self.year_established,
        }


class Owner(db.Model):
    __tablename__ = 'owners'
    username = db.Column(db.String(), primary_key=True)
    email = db.Column(db.String(), nullable=True, unique=True)
    password = db.Column(db.LargeBinary, nullable=False)
    salt = db.Column(db.LargeBinary, nullable=False)
    phone_number = db.Column(db.String(), nullable=True)
    admin_access = db.Column(db.Boolean, nullable=False)

    def __init__(self, email, username, password, salt, phone_number, admin_access):
        self.email = email
        self.username = username
        self.password = password
        self.salt = salt
        self.phone_number = phone_number
        self.admin_access = admin_access

    def serialize(self):
        return {
            'username': self.username,
            'email': self.email,
            'phone_number': self.phone_number,
            'admin_access': self.admin_access,
        }


class Owning(db.Model):
    __tablename__ = 'owning'
    owner_id = db.Column(db.String(), db.ForeignKey('owners.username'), primary_key=True)
    publisher_id = db.Column(db.String(), db.ForeignKey('publishers.publisher_name'), primary_key=True)

    def __init__(self, owner_id, publisher_id):
        self.owner_id = owner_id
        self.publisher_id = publisher_id


class Publisher(db.Model):
    __tablename__ = 'publishers'
    publisher_name = db.Column(db.String(), primary_key=True)
    school = db.Column(db.String(), nullable=True)
    publisher_phone_number = db.Column(db.String(), nullable=True)
    publisher_website = db.Column(db.String(), nullable=False)
    publisher_street_address = db.Column(db.String(), nullable=False)
    publisher_city = db.Column(db.String(), nullable=False)
    publisher_state = db.Column(db.String(), nullable=False)
    publisher_country = db.Column(db.String(), nullable=False)
    commissions_raised = db.Column(db.Float(), nullable=False)
    commissions_available = db.Column(db.Float(), nullable=False)

    def __init__(self, publisher_name, school, publisher_phone_number, publisher_website, \
                 publisher_street_address, publisher_city, publisher_state, publisher_country,
                 commissions_raised, commissions_available):
        self.publisher_name = publisher_name
        self.school = school
        self.publisher_phone_number = publisher_phone_number
        self.publisher_website = publisher_website
        self.publisher_street_address = publisher_street_address
        self.publisher_city = publisher_city
        self.publisher_state = publisher_state
        self.publisher_country = publisher_country
        self.commissions_raised = commissions_raised
        self.commissions_available = commissions_available

    def __repr__(self):
        return '{} @ {} ({}, {})'.format(self.publisher_name, self.school, self.publisher_city, \
                                         self.publisher_state)

    def serialize(self):
        return {
            'publisher_name': self.publisher_name,
            'school': self.school,
            'publisher_phone_number': self.publisher_phone_number,
            'publisher_website': self.publisher_website,
            'publisher_street_address': self.publisher_street_address,
            'publisher_city': self.publisher_city,
            'publisher_state': self.publisher_state,
            'publisher_country': self.publisher_country
        }


class Project(db.Model):
    __tablename__ = 'projects'

    project_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    organization_id = db.Column(db.String(), db.ForeignKey('organizations.email'))
    project_name = db.Column(db.String(), nullable=False)
    project_short_description = db.Column(db.String(), nullable=True)
    project_description = db.Column(db.String(), nullable=False)
    project_picture_link = db.Column(db.String(), nullable=False)
    project_goal = db.Column(db.Integer, nullable=False)
    project_raised = db.Column(db.Float(), nullable=False)
    project_city = db.Column(db.String(), nullable=False)
    project_state = db.Column(db.String(), nullable=False)
    project_country = db.Column(db.String(), nullable=False)
    newspaper_id = db.Column(db.String(), db.ForeignKey('publishers.publisher_name'), nullable=False)
    removed = db.Column(db.Boolean, nullable=False)
    funds_available = db.Column(db.Float(), nullable=False)

    def __init__(self, organization_id, project_name, project_short_description, project_description,
                 project_picture_link, project_goal, project_raised, project_city, project_state, \
                 project_country, newspaper_id, removed):
        self.organization_id = organization_id
        self.project_name = project_name
        self.project_short_description = project_short_description
        self.project_description = project_description
        self.project_picture_link = project_picture_link
        self.project_goal = project_goal
        self.project_raised = project_raised
        self.project_city = project_city
        self.project_state = project_state
        self.project_country = project_country
        self.newspaper_id = newspaper_id
        self.removed = removed
        self.funds_available = 0.0

    def serialize(self):
        return {
            'project_id': self.project_id,
            'organization_id': self.organization_id,
            'project_name': self.project_name,
            'project_short_description': self.project_short_description,
            'project_description': self.project_description,
            'project_picture_link': self.project_picture_link,
            'project_goal': self.project_goal,
            'project_raised': self.project_raised,
            'project_city': self.project_city,
            'project_state': self.project_state,
            'project_country': self.project_country,
            'newspaper_id': self.newspaper_id,
            'removed': self.removed,
        }


class Article(db.Model):
    __tablename__ = 'articles'
    article_link = db.Column(db.String(), primary_key=True)
    article_title = db.Column(db.String(), nullable=False)
    publisher_id = db.Column(db.String(), db.ForeignKey('publishers.publisher_name'))
    widget_status = db.Column(db.Boolean, nullable=False)
    date_published = db.Column(db.DateTime, nullable=False)
    fund_name = db.Column(db.String(), db.ForeignKey('funds.fund_name'), nullable=True)
    project_id1 = db.Column(db.Integer, db.ForeignKey('projects.project_id'), nullable=True)
    project_id2 = db.Column(db.Integer, db.ForeignKey('projects.project_id'), nullable=True)
    project_id3 = db.Column(db.Integer, db.ForeignKey('projects.project_id'), nullable=True)
    project_id4 = db.Column(db.Integer, db.ForeignKey('projects.project_id'), nullable=True)
    project_id5 = db.Column(db.Integer, db.ForeignKey('projects.project_id'), nullable=True)
    project_id6 = db.Column(db.Integer, db.ForeignKey('projects.project_id'), nullable=True)
    edited_by_publisher = db.Column(db.Boolean, nullable=False)
    edited_by_newspark = db.Column(db.Boolean, nullable=False)

    def __init__(self, article_link, article_title, publisher_id, widget_status, date_published, \
                 fund_name, project_id1, project_id2, project_id3, project_id4, project_id5, project_id6, \
                 edited_by_publisher, edited_by_newspark):
        self.article_link = article_link
        self.article_title = article_title
        self.publisher_id = publisher_id
        self.widget_status = widget_status
        self.date_published = date_published
        self.fund_name = fund_name
        self.project_id1 = project_id1
        self.project_id2 = project_id2
        self.project_id3 = project_id3
        self.project_id4 = project_id4
        self.project_id5 = project_id5
        self.project_id6 = project_id6
        self.edited_by_publisher = edited_by_publisher
        self.edited_by_newspark = edited_by_newspark

    def serialize(self):
        return {
            'article_link': self.article_link,
            'article_title': self.article_title,
            'publisher_id': self.publisher_id,
            'widget_status': self.widget_status,
            'date_published': self.date_published,
            'edited_by_publisher': self.edited_by_publisher,
            'edited_by_newspark': self.edited_by_newspark,
        }

    def get_project_ids(self):
        return [self.project_id1, self.project_id2, self.project_id3, self.project_id4,
                self.project_id5, self.project_id6]


class Donation(db.Model):
    __tablename__ = 'donations'

    donation_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    organization_id = db.Column(db.String, db.ForeignKey('organizations.email'))
    project_id = db.Column(db.Integer, db.ForeignKey('projects.project_id'), nullable=True)
    fund_name = db.Column(db.String(), db.ForeignKey('funds.fund_name'), nullable=True)
    donation_date_time = db.Column(db.DateTime, nullable=False)
    donor_name = db.Column(db.String())
    donor_email = db.Column(db.String())
    amount_donated = db.Column(db.Float(), nullable=False)
    newspaper_id = db.Column(db.String(), db.ForeignKey('publishers.publisher_name'), nullable=False)
    newspaper_article_title = db.Column(db.String(), nullable=False)
    newspaper_article_link = db.Column(db.String(), db.ForeignKey('articles.article_link'))

    def __init__(self, organization_id, project_id, fund_name, donation_date_time, donor_name, donor_email, amount_donated, \
                 newspaper_id, newspaper_article_title, newspaper_article_link):
        self.project_id = project_id
        self.fund_name = fund_name
        self.organization_id = organization_id
        self.donation_date_time = donation_date_time
        self.donor_name = donor_name
        self.donor_email = donor_email
        self.amount_donated = amount_donated
        self.newspaper_id = newspaper_id
        self.newspaper_article_title = newspaper_article_title
        self.newspaper_article_link = newspaper_article_link

    def serialize(self):
        return {
            'donation_id': self.donation_id,
            'project_id': self.project_id,
            'organization_id': self.organization_id,
            'donation_date_time': self.donation_date_time,
            'donor_name': self.donor_name,
            'donor_email': self.donor_email,
            'amount_donated': self.amount_donated,
            'newspaper_id': self.newspaper_id,
            'newspaper_article_title': self.newspaper_article_title,
            'newspaper_article_link': self.newspaper_article_link
        }


class Fund(db.Model):
    __tablename__ = 'funds'

    fund_name = db.Column(db.String(), primary_key=True)
    fund_topic = db.Column(db.String(), nullable=True)
    fund_description = db.Column(db.String(), nullable=True)
    fund_picture_link = db.Column(db.String(), nullable=False)
    total_amount_raised = db.Column(db.Float(), nullable=False)

    def __init__(self, fund_name, fund_topic, fund_description, fund_picture_link, total_amount_raised):
        self.fund_name = fund_name
        self.fund_topic = fund_topic
        self.fund_description = fund_description
        self.fund_picture_link = fund_picture_link
        self.total_amount_raised = total_amount_raised

    def serialize(self):
        return {
            'fund_name': self.fund_name,
            'fund_topic': self.fund_topic,
            'fund_description': self.fund_description,
            'fund_picture_link': self.fund_picture_link,
        }


class Funding(db.Model):
    __tablename__ = 'funding'

    fund_id = db.Column(db.String(), db.ForeignKey('funds.fund_name'), primary_key=True)
    organization_id = db.Column(db.String(), db.ForeignKey('organizations.email'), primary_key=True)

    def __init__(self, fund_id, organization_id):
        self.fund_id = fund_id
        self.organization_id = organization_id
