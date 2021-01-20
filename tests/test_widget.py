import unittest
import sys
sys.path.append("../")
from app import application, db
from app.models import *
from app import redis

test_app = application.test_client()
num_choices = application.config['NUM_CHOICES']


class unittestWidget(unittest.TestCase):
    """ Runs unit tests on all routes in widget.py blueprint """

    def test_getCharities1(self):
        """ log into existing profile """
        article = 'https://www.idsnews.com/article/2020/06/wildlife-to-look-for-in-monroe-county'
        curr_article = Article.query.filter_by(article_link=article).first()
        if curr_article is not None:
            db.session.delete(curr_article)
            db.session.commit()

        response1 = test_app.post(
            '/get_charities',
            data=dict(
                article_link=article,
                article_title='',
                article_date='',
                articel_text='',
            )
        )

        result1 = response1.get_json()
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(len(result1), num_choices)
        self.assertTrue(redis.exists(article))

        response2 = test_app.post(
            '/get_charities',
            data=dict(
                article_link=article,
                article_title='',
                article_date='',
                article_text='',
            )
        )

        result2 = response2.get_json()
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(len(result1), num_choices)
        self.assertEqual(result1, result2)
        self.assertTrue(redis.exists(article))

        # Delete the article and then make sure the results are the same again
        curr_article = Article.query.filter_by(article_link=article).first()
        redis.delete(curr_article.article_link)
        db.session.delete(curr_article)
        db.session.commit()

    def test_getCharities2(self):
        article = 'https://www.idsnews.com/article/2020/06/former-iu-mens-soccer-all-american-ken-snow-dies-at-50'
        curr_article = Article.query.filter_by(article_link=article).first()
        if curr_article is not None:
            db.session.delete(curr_article)
            db.session.commit()

        response1 = test_app.post(
            '/get_charities',
            data=dict(
                article_link=article,
                article_title='blah blah',
                article_date='Jun 29 2020',
                article_text='here is some text',
            )
        )

        result1 = response1.get_json()
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(len(result1), num_choices)
        self.assertTrue(redis.exists(article))

        response2 = test_app.post(
            '/get_charities',
            data=dict(
                article_link=article,
                article_title='blah bah',
                article_date='Jun 23 2020',
                article_text='here is some text',
            )
        )

        result2 = response2.get_json()
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(len(result1), num_choices)
        self.assertEqual(result1, result2)
        self.assertTrue(redis.exists(article))

        # Delete the article and then make sure the results are the same again
        curr_article = Article.query.filter_by(article_link=article).first()
        redis.delete(curr_article.article_link)
        db.session.delete(curr_article)
        db.session.commit()

    def test_pay1(self):
        donation = 20
        stripe_fee = float(29 * donation + 300) / 971
        amount_charged = donation+stripe_fee

        response = test_app.post(
            '/pay',
            data=dict(
                amount=amount_charged
            )
        )

        result = response.get_json()
        self.assertEqual(response.status_code, 200)
        # self.assertEqual(result['amount'], donation)

    def test_pay2(self):
        donation = 50
        stripe_fee = float(29 * donation + 300) / 971
        amount_charged = donation+stripe_fee

        response = test_app.post(
            '/pay',
            data=dict(
                amount=amount_charged
            )
        )

        result = response.get_json()
        self.assertEqual(response.status_code, 200)
        # self.assertEqual(result['amount'], correct_amount)

    def test_pay3(self):
        donation = 33
        stripe_fee = float(29 * donation + 300) / 971
        amount_charged = donation+stripe_fee

        response = test_app.post(
            '/pay',
            data=dict(
                amount=amount_charged
            )
        )

        result = response.get_json()
        self.assertEqual(response.status_code, 200)
        # self.assertEqual(result['amount'], correct_amount)

    def test_updateDB1(self):
        project = Project.query.first()
        organization = Organization.query.filter_by(email=project.organization_id).first()
        article = Article.query.first()
        publisher = Publisher.query.filter_by(publisher_name=article.publisher_id).first()

        # Original Values
        org_funds_raised = organization.total_amount_raised
        proj_funds_raised = project.funds_available
        proj_project_raised = project.project_raised
        pub_comission_raised = publisher.commissions_raised
        pub_comission_available = publisher.commissions_available

        # Input Variables
        organization_id = project.organization_id
        project_id = project.project_id
        name = 'Karthik Rao'
        email = 'karthik6d@gmail.com'
        article_link = article.article_link
        amount = 50.0

        amount_to_charity = amount*.92
        amount_to_publisher = amount*.04

        response = test_app.post(
            '/update_db_after_payment',
            data=dict(
                organization_id=organization_id,
                project_id=project_id,
                name=name,
                email=email,
                article_link=article_link,
                amount=amount
            )
        )

        result = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(result, "Success")

        # Checking DB Inserts
        organization = Organization.query.filter_by(email=organization_id).first()
        project = Project.query.filter_by(project_id=project_id).first()
        article = Article.query.filter_by(article_link=article_link).first()
        publisher = Publisher.query.filter_by(publisher_name=article.publisher_id).first()
        donation = Donation.query.filter_by(donor_name=name, donor_email=email,
                                            project_id=project_id,
                                            newspaper_article_link=article_link).first()

        self.assertEqual(organization.total_amount_raised, org_funds_raised+amount_to_charity)
        self.assertEqual(project.funds_available, proj_funds_raised+amount_to_charity)
        self.assertEqual(project.project_raised, proj_project_raised+amount_to_charity)
        self.assertEqual(publisher.commissions_available, pub_comission_available+amount_to_publisher)
        self.assertEqual(publisher.commissions_raised, pub_comission_raised+amount_to_publisher)
        self.assertEqual(donation.newspaper_article_title, article.article_title)

        # Clear DB
        db.session.delete(donation)
        organization.total_amount_raised -= amount_to_charity
        project.funds_available -= amount_to_charity
        project.project_raised -= amount_to_charity
        publisher.commissions_available -= amount_to_publisher
        publisher.commissions_raised -= amount_to_publisher

        db.session.commit()


if __name__ == '__main__':
    unittest.main()
