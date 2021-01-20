import unittest
import sys
import io
from werkzeug.datastructures import FileStorage

sys.path.append("../")
from app import application, db
from flask_jwt_extended import (
    jwt_required, create_access_token,
    get_jwt_identity, decode_token
)
from app.helper.misc import *
from app.models import *
from app import redis, db, s3

test_app = application.test_client()


def auth_token_helper(username):
    password = 'password'

    response = test_app.post(
        '/login',
        data=dict(
            email=username,
            password=password)
    )

    headers = {'Authorization': 'Bearer {}'.format(response.get_json()['access_token'])}
    return headers


class unittestCharity(unittest.TestCase):
    """ Runs unit tests on all routes in charity.py blueprint """

    def test_login1(self):
        """ log into existing profile """
        user = Organization.query.first()
        username = user.email
        password = 'password'

        response = test_app.post(
            '/login',
            data=dict(
                email=username,
                password=password)
        )

        result = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue('access_token' in result)

    def test_login2(self):
        user = Organization.query.first()
        username = user.email
        password = 'password1'

        response = test_app.post(
            '/login',
            data=dict(
                email=username,
                password=password)
        )

        result = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(result, "Invalid Password")

    def test_login3(self):
        user = Organization.query.first()
        username = user.email + 'a'
        password = 'password1'

        response = test_app.post(
            '/login',
            data=dict(
                email=username,
                password=password)
        )

        result = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(result, "Invalid Email")

    # def test_forgotPassword1(self):
    #     user = Organization.query.first()
    #     username = user.email
    #
    #     response = test_app.post(
    #         '/forgot_password',
    #         data=dict(
    #             email=username)
    #     )
    #
    #     self.assertEqual(response.status_code, 200)
    #     self.assertEqual(response.get_json(), "Success")
    #
    # def test_forgotPassword2(self):
    #     user = Organization.query.first()
    #     username = user.email + 'a'
    #
    #     response = test_app.post(
    #         '/forgot_password',
    #         data=dict(
    #             email=username)
    #     )
    #
    #     self.assertEqual(response.status_code, 200)
    #     self.assertEqual(response.get_json(), "No Account Found")
    #
    def test_registerOrganization1(self):
        """ register new profile """
        email = "test135@duke.edu"

        response = test_app.post(
            '/register_organization',
            data=dict(
                email=email,
                password="password",
                phone_number="9173634115",
                organization_website="newspark.us",
                organization_name="newspark",
                organization_description="an online donation platform",
                organization_street_address="21 East 90th St.",
                organization_city="New York",
                organization_state="New York",
                organization_country="United States",
                organization_type="nonprofit",
                year_established=2000
            )
        )

        self.assertEqual(response.status_code, 200)

        # Check if the database actual contains the new info
        exists = db.session.query(db.exists().where(Organization.email == email)).scalar()
        self.assertEqual(exists, True)

        # Delete entry from database
        db.session.delete(Organization.query.filter_by(email=email).first())
        db.session.commit()

    def test_registerOrganization2(self):
        """ register new profile """
        email = Organization.query.first().email

        response = test_app.post(
            '/register_organization',
            data=dict(
                email=email,
                password="password",
                phone_number="9173634115",
                organization_website="newspark.us",
                organization_name="newspark",
                organization_description="an online donation platform",
                organization_street_address="21 East 90th St.",
                organization_city="New York",
                organization_state="New York",
                organization_country="United States",
                organization_type="nonprofit",
                year_established=2000
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), "Account Exists")

    def test_getOrganization(self):
        user = Organization.query.first()
        headers = auth_token_helper(user.email)

        response = test_app.get(
            '/get_organization',
            headers=headers
        )

        result = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(result['organization'], user.serialize())

    def test_editOrganization(self):
        user = Organization.query.first()
        headers = auth_token_helper(user.email)

        response = test_app.post(
            '/edit_organization',
            headers=headers,
            data=dict(
                password="password",
                phone_number="9146469258",
                organization_website="newspark.us",
                organization_name="newspark",
                organization_description="an online donation platform",
                organization_street_address="21 East 90th St.",
                organization_city="New York",
                organization_state="New York",
                organization_country="United States",
                organization_type="nonprofit",
                year_established=2000
            )
        )

        result = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(result, "Success")

        # Check if new user is actually edited
        edit_user = Organization.query.filter_by(email=user.email).first()
        self.assertEqual(edit_user.phone_number, "9146469258")
        self.assertEqual(edit_user.organization_website, "newspark.us")

    def test_getProjects(self):
        user = Organization.query.first()
        headers = auth_token_helper(user.email)

        response = test_app.get(
            '/get_projects',
            headers=headers
        )

        result = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(result['organization_name'], user.organization_name)

    def test_addProject(self):
        user = Organization.query.first()
        headers = auth_token_helper(user.email)

        data = dict(
            project_name="Donate to newspark",
            project_description="We need money",
            project_goal=5000,
            project_city="New York",
            project_state="New York",
            project_country="United States",
            newspaper_id="Indiana Daily Student",
            project_short_description="YADDA YADDA YADDA"
        )

        my_file = FileStorage(
            stream=open('karthik_headshot.jpg', "rb"),
            filename="karthik.jpg",
            content_type="jpeg",
        )

        data['project_picture_link'] = my_file

        response = test_app.post(
            '/add_project',
            headers=headers,
            data=data,
            content_type='multipart/form-data'
        )

        result = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(result, "Success")

        # Make sure the correct project was added
        new_project = Project.query.filter_by(project_name="Donate to newspark").first()
        self.assertEqual(new_project.project_name, "Donate to newspark")
        self.assertEqual(new_project.project_goal, 5000)
        self.assertEqual(new_project.newspaper_id, "Indiana Daily Student")
        self.assertEqual(new_project.project_city, "New York")

        # Delete the current project
        db.session.delete(new_project)
        db.session.commit()

    def test_editProject(self):
        user = Organization.query.first()
        headers = auth_token_helper(user.email)
        project = Project.query.filter_by(organization_id=user.email).first()
        project_data = project.serialize()

        # Check if the cache was updated properly
        sql_query = '''select article_link from articles where
                       project_id1={} or project_id2={} or project_id3={}
                       or project_id4={} or project_id5={} or project_id6={};'''.format(project.project_id,
                                                                                        project.project_id,
                                                                                        project.project_id,
                                                                                        project.project_id,
                                                                                        project.project_id,
                                                                                        project.project_id)
        conn = db.engine.connect().connection
        df = pd.read_sql(sql_query, conn)
        conn.close()
        unique_articles = list(df['article_link'].unique())

        data = dict(
            project_id=project.project_id,
            project_name="Diff Donate",
            project_description="We need money",
            project_goal=10000,
            project_city="Briarcliff Manor",
            project_state="New York",
            project_country="United States",
            newspaper_id="The Emory Wheel",
            project_short_description="YADDA YADDA YADDA"
        )

        my_file = FileStorage(
            stream=open('karthik_headshot.jpg', "rb"),
            filename="karthik.jpg",
            content_type="jpeg",
        )

        data['project_picture_link'] = my_file

        response = test_app.post(
            '/edit_project',
            headers=headers,
            data=data,
            content_type='multipart/form-data'
        )

        result = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(result, "Success")

        # Make sure the correct project was edited
        new_project = Project.query.filter_by(project_name="Diff Donate").first()
        self.assertEqual(new_project.project_name, "Diff Donate")
        self.assertEqual(new_project.project_goal, 10000)
        self.assertEqual(new_project.newspaper_id, "The Emory Wheel")
        self.assertEqual(new_project.project_city, "Briarcliff Manor")

        # Check the redis cache
        for i in unique_articles:
            self.assertFalse(redis.exists(i))

        # Change Project Back
        project.project_name = project_data['project_name']
        project.project_description = project_data['project_description']
        project.project_goal = project_data['project_goal']
        project.project_city = project_data['project_city']
        project.project_state = project_data['project_state']
        project.project_country = project_data['project_country']
        project.newspaper_id = project_data['newspaper_id']
        db.session.commit()

    def test_deleteProject(self):
        user = Organization.query.first()
        headers = auth_token_helper(user.email)
        project = Project.query.filter_by(organization_id=user.email).first()
        project_data = project.serialize()

        response = test_app.post(
            '/delete_project',
            headers=headers,
            data=dict(
                project_id=project_data['project_id']
            )
        )

        result = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(result, "Deleted")

        # Check if it actually deleted
        new_project = Project.query.filter_by(project_id=project_data['project_id']).first()
        self.assertEqual(new_project.removed, True)

        # Change it back
        new_project.removed = False
        db.session.commit()

    def test_getPaymentLogs(self):
        user = Organization.query.first()
        headers = auth_token_helper(user.email)

        response = test_app.get(
            '/get_payment_logs',
            headers=headers
        )

        result = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual('payment_logs' in result, True)
        self.assertEqual("total_donated_this_week" in result, True)
        self.assertEqual("initiative_totals" in result, True)
        self.assertEqual("total_donated" in result, True)
        self.assertEqual("total_goal" in result, True)

    def test_getPaymentCSV(self):
        user = Organization.query.first()
        headers = auth_token_helper(user.email)

        response = test_app.get(
            '/get_payment_csv',
            headers=headers
        )

        result = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual('url' in result, True)

    def test_getPublisherCounts(self):
        user = Organization.query.first()
        headers = auth_token_helper(user.email)

        response = test_app.get(
            '/get_publisher_counts',
            headers=headers
        )

        result = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual('counts' in result, True)
        self.assertEqual('newspaper_names' in result, True)

    def test_contactUs(self):
        """ register new profile """
        user = Organization.query.first()
        headers = auth_token_helper(user.email)

        response = test_app.post(
            '/contact_us',
            headers=headers,
            data=dict(
                first_name='Karthik',
                last_name='Rao',
                email='karthik6d@gmail.com',
                body='whatever',
                is_publisher=False,
                primary_id="Indiana Daily Student"
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), "DONE")

    def test_edit_payment_info(self):
        user = Organization.query.first()
        headers = auth_token_helper(user.email)

        response = test_app.post(
            '/edit_payment_info_charity',
            headers=headers,
            data=dict(
                accountHolder='Alex',
                bankBranchAddress='some location',
                bankName='citibank',
                accountType='checking',
                bankRoutingNumber="1",
                bankAccountNumber="123"
            )
        )

        self.assertEqual(response.status_code, 200)
        bucket = 'newspark-payment'
        file_name = 'charity/routers.json'
        payment_data = json.load(s3.get_object(Bucket=bucket, Key=file_name)['Body'])

        accounts = payment_data['accounts']
        primary_ids = [accounts[i]['primary_id'] for i in range(len(accounts))]
        self.assertIn(user.email, primary_ids)


if __name__ == '__main__':
    unittest.main()
