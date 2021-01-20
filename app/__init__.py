from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import (
    JWTManager, verify_jwt_in_request, create_access_token,
    get_jwt_claims
)
from flask_mail import Mail, Message
import boto3
from functools import wraps
import pandas as pd
import warnings
import redis

warnings.filterwarnings("ignore")

# Set up App
application = Flask(__name__, instance_relative_config=True)

application.config.from_pyfile('config_prod.py')
application.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize CORS on APP
CORS(application)

# Initialize Databases
db = SQLAlchemy(application)

# Initialize JWT
jwt = JWTManager(application)

# Initialize Redis
redis = redis.Redis(host=application.config['REDIS_HOST'],
                    port=application.config['REDIS_PORT'],
                    password=application.config['REDIS_PASSWORD'])


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt_claims()
        if claims['roles'] != 'publisher':
            return jsonify(msg='Publishers only!'), 403
        else:
            return fn(*args, **kwargs)

    return wrapper


@jwt.user_claims_loader
def add_claims_to_access_token(identity):
    if '@' in identity:
        return {'roles': 'charity'}
    else:
        return {'roles': 'publisher'}


# Initialize Mail Server
mail = Mail(application)

# Initialize s3 bucket
s3 = boto3.client('s3',
                  aws_access_key_id=application.config['AWS_ACCESS_KEY_ID'],
                  aws_secret_access_key=application.config['AWS_SECRET_ACCESS_KEY'])

# Get the Blueprints for every view
from .views.charity import charity_blueprint
from .views.widget import widget_blueprint
from .views.newspaper import publisher_blueprint
from .views.blm_extension import blm_extension_blueprint
from .views.crowd_funding import crowd_funding_blueprint
from .views.newsletter import newsletter_blueprint
from .views.funds import funds_blueprint

application.register_blueprint(charity_blueprint)
application.register_blueprint(widget_blueprint)
application.register_blueprint(publisher_blueprint)
application.register_blueprint(blm_extension_blueprint)
application.register_blueprint(crowd_funding_blueprint)
application.register_blueprint(newsletter_blueprint)
application.register_blueprint(funds_blueprint)


# Define a Cron JOB for sending an email automatically for charities who haven't made a project
def sensor(app):
    """ Send email reminding charities to add projects every other day. """

    sql_query = '''select organizations.email, organizations.organization_name
                    from organizations
                    where organizations.email not in (
                        select projects.organization_id from projects group by projects.organization_id);'''

    conn = db.engine.connect().connection
    df = pd.read_sql(sql_query, conn)
    emails = list(df['email'])
    organization_names = list(df['organization_name'])

    for i, email in enumerate(emails):
        with app.app_context():
            msg = Message()
            msg.subject = "Reminder to Add a Campaign"
            msg.body = 'Hi {},\n\nWe are so excited that you have decided to raise funds via Newspark! ' \
                       'The next step after signing up is to create a campaign, ' \
                       'which will be advertised on one of our partnering newspapers. ' \
                       'You can create a campaign by going to your Campaigns page on the charity interface at charity.newspark.us.\n\n ' \
                       'Best regards,\nNewspark team'.format(organization_names[i])
            msg.recipients = [email]
            msg.sender = 'founders@newspark.us'
            mail.send(msg)

    return "success"

# cron = BackgroundScheduler(daemon=True)
# cron.add_job(sensor, 'interval', args=[application], days=2)
# cron.start()
