import unittest
import sys
sys.path.append("../")
from app import application, db
from app.models import *
import itertools
import operator
from app import redis

test_app = application.test_client()


def auth_token_helper(username):
    response = test_app.post(
        '/owner_login',
        data=dict(
            username=username,
            password='password')
    )

    headers = {'Authorization': 'Bearer {}'.format(response.get_json()['access_token'])}
    return headers


class unittestNewspaper(unittest.TestCase):
    """ Runs unit tests on all routes in newspaper.py blueprint """

    def test_login_correct_password(self):
        """ log into existing profile """
        owner = Owner.query.all()[1]
        username = owner.username
        password = 'password'

        response = test_app.post(
            '/owner_login',
            data=dict(
                username=username,
                password=password)
        )

        result = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertTrue('access_token' in result)

    def test_login_failed_password(self):
        owner = Owner.query.all()[1]
        username = owner.username
        password = 'password1'

        response = test_app.post(
            '/owner_login',
            data=dict(
                username=username,
                password=password)
        )

        result = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(result, "Invalid Password")

    def test_login_failed_username(self):
        username = 'fake_username'
        password = 'password'

        response = test_app.post(
            '/owner_login',
            data=dict(
                username=username,
                password=password)
        )

        result = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(result, "Invalid Username")

    def test_get_donations_from_publishers(self):
        owner = Owner.query.all()[1]
        headers = auth_token_helper(owner.username)

        response = test_app.get(
            '/get_donations_from_publishers',
            headers=headers
        )

        result = response.get_json()
        values = result['cumulative_donations']['values']
        pairs = zip(values, values[1:])
        monotone_increasing = all(itertools.starmap(operator.le, pairs))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(monotone_increasing)

    def test_get_donations_from_publishers_csv(self):
        owner = Owner.query.all()[1]
        headers = auth_token_helper(owner.username)

        response = test_app.get(
            '/get_donations_from_publisher_csv',
            headers=headers
        )

        result = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue('url' in result)

    def test_change_widget_status(self):
        owner = Owner.query.all()[1]
        headers = auth_token_helper(owner.username)

        publisher_name = Owning.query.filter_by(owner_id=owner.username).first().publisher_id
        article = Article.query.filter_by(publisher_id=publisher_name).first()
        article_link = article.article_link
        status_before = article.widget_status

        response = test_app.post(
            '/change_widget_status',
            headers=headers,
            data=dict(
                article_link=article_link
            )
        )

        article = Article.query.filter_by(article_link=article_link).first()
        status_after = article.widget_status

        result = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(result, 'Success')
        self.assertEqual(status_before, not status_after)

        # Change widget status back
        article.widget_status = not status_after
        db.session.commit()

    def test_change_widget_status_failed_article(self):
        owner = Owner.query.all()[1]
        headers = auth_token_helper(owner.username)
        article_link = 'fake_article'

        response = test_app.post(
            '/change_widget_status',
            headers=headers,
            data=dict(
                article_link=article_link
            )
        )

        result = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(result, "Article Not Found")

    # todo: check the json object
    def test_get_articles(self):
        owner = Owner.query.all()[1]
        headers = auth_token_helper(owner.username)

        publisher_name = Owning.query.filter_by(owner_id=owner.username).first().publisher_id
        article = Article.query.filter_by(publisher_id=publisher_name).first()
        article_link = article.article_link

        response = test_app.get(
            '/get_articles',
            headers=headers
        )

        result = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertTrue('articles' in result)
        self.assertTrue('admin_account' in result)

        # Check if certain key is in each article
        for i in result['articles']:
            self.assertTrue('revenue' in i)

    def test_get_relevant_projects(self):
        owner = Owner.query.all()[1]
        headers = auth_token_helper(owner.username)

        publisher_name = Owning.query.filter_by(owner_id=owner.username).first().publisher_id
        article = Article.query.filter_by(publisher_id=publisher_name).first()
        article_link = article.article_link

        response = test_app.post(
            '/get_relevant_projects',
            headers=headers,
            data=dict(
                article_link=article_link
            )
        )

        result = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(result['project_info']), 6)

    def test_get_relevant_projects_when_article_belongs_to_other_publisher(self):
        owner = Owner.query.all()[1]
        headers = auth_token_helper(owner.username)
        other_owner = Owner.query.all()[2]
        # print(owner.username, other_owner.username)

        other_publisher_name = Owning.query.filter_by(owner_id=other_owner.username).first().publisher_id
        other_article = Article.query.filter_by(publisher_id=other_publisher_name).first()
        other_article_link = other_article.article_link

        response = test_app.post(
            '/get_relevant_projects',
            headers=headers,
            data=dict(
                article_link=other_article_link
            )
        )

        result = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(result, 'Article does not exist.')

    def test_get_article_info(self):
        owner = Owner.query.all()[1]
        headers = auth_token_helper(owner.username)

        publisher_name = Owning.query.filter_by(owner_id=owner.username).first().publisher_id
        article = Article.query.filter_by(publisher_id=publisher_name).first()
        article_link = article.article_link

        response = test_app.post(
            '/get_article_info',
            headers=headers,
            data=dict(
                article_link=article_link
            )
        )

        result = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(result['article_info']['article_link'], article_link)

    def test_add_project_to_article(self):
        owner = Owner.query.all()[1]
        headers = auth_token_helper(owner.username)

        publisher_name = Owning.query.filter_by(owner_id=owner.username).first().publisher_id
        article = Article.query.filter_by(publisher_id=publisher_name).first()
        article_link = article.article_link
        old_ids = [article.project_id1, article.project_id2, article.project_id3, article.project_id4,
                   article.project_id5, article.project_id6]

        project_id = article.project_id1  # assumes project id is not None
        article.project_id1 = None
        db.session.commit()

        response = test_app.post(
            '/add_project_to_article',
            headers=headers,
            data=dict(
                article_link=article_link,
                project_id=project_id
            )
        )

        updated_article = Article.query.filter_by(article_link=article_link).first()
        ids = [updated_article.project_id1, updated_article.project_id2, updated_article.project_id3,
               updated_article.project_id4, updated_article.project_id5, updated_article.project_id6]

        result = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(result, 'Success')
        self.assertTrue(project_id in ids)
        self.assertTrue(redis.exists(article_link))

        # Revert back to original state
        updated_article.project_id1 = old_ids[0]
        updated_article.project_id2 = old_ids[1]
        updated_article.project_id3 = old_ids[2]
        updated_article.project_id4 = old_ids[3]
        updated_article.project_id5 = old_ids[4]
        updated_article.project_id6 = old_ids[5]
        redis.delete(article_link)
        db.session.commit()

    def test_remove_project_from_article(self):
        owner = Owner.query.all()[1]
        headers = auth_token_helper(owner.username)

        publisher_name = Owning.query.filter_by(owner_id=owner.username).first().publisher_id
        article = Article.query.filter_by(publisher_id=publisher_name).first()
        article_link = article.article_link
        old_ids = [article.project_id1, article.project_id2, article.project_id3, article.project_id4,
                   article.project_id5, article.project_id6]

        project_id = article.project_id1  # assumes project id is not None

        response = test_app.post(
            '/remove_project_from_article',
            headers=headers,
            data=dict(
                article_link=article_link,
                project_id=project_id
            )
        )

        updated_article = Article.query.filter_by(article_link=article_link).first()
        ids = [updated_article.project_id1, updated_article.project_id2, updated_article.project_id3,
               updated_article.project_id4, updated_article.project_id5, updated_article.project_id6]

        result = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(result, 'Success')
        self.assertTrue(project_id not in ids)
        self.assertTrue(redis.exists(article_link))

        updated_article.project_id1 = old_ids[0]
        updated_article.project_id2 = old_ids[1]
        updated_article.project_id3 = old_ids[2]
        updated_article.project_id4 = old_ids[3]
        updated_article.project_id5 = old_ids[4]
        updated_article.project_id6 = old_ids[5]
        redis.delete(article_link)
        db.session.commit()

    # def test_get_projects_for_publisher(self):
    #     owner = Owner.query.all()[1]
    #     owning = Owning.query.filter_by(owner_id=owner.username).first()
    #     headers = auth_token_helper(owner.username)
    #     publisher_name = owning.publisher_id
    #
    #     response = test_app.post(
    #         '/test_get_projects_for_publisher',
    #         headers=headers,
    #         data=dict(
    #             publisher_name=publisher_name,
    #         )
    #     )
    #
    #     result = response.get_json()
    #     self.assertEqual(response.status_code, 200)
    #     self.assertTrue('project_info' in result)
    #
    #     # Todo: could add tests to make sure the data is correct

if __name__ == '__main__':
    unittest.main()
