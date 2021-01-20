import unittest
import sys

sys.path.append("../")
from app import app, dynamodb


test_app = app.test_client()
result_count = 6


def register(article_url):
    return test_app.post(
        '/get_corona_charities',
        data=dict(article_url=article_url),
        follow_redirects=True
    )


class TestGetCoronaCharities(unittest.TestCase):
    def test_nyt(self):
        article_url = "https://www.nytimes.com/2020/04/26/world/europe/uk-us-coronavirus-briefings-trump-johnson.html"
        response = register(article_url)
        result = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(result), result_count)

    def test_cnn(self):
        article_url = "https://www.cnn.com/2020/04/26/politics/trump-briefings-media-blame-disinfectant-comments/index.html"
        response = register(article_url)
        result = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(result), result_count)

    def test_usa_today(self):
        article_url = "https://www.usatoday.com/story/news/health/2020/04/26/coronavirus-symptoms-cdc-adds-six-new-symptoms-covid-19/3029438001/"
        response = register(article_url)
        result = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(result), result_count)

    def test_indiana(self):
        article_url = "https://www.idsnews.com/article/2020/04/iupui-start-coronavirus-testing-saturday-study-indiana-state-health-department-covid-19"
        response = register(article_url)
        result = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(result), result_count)

    def test_not_corona(self):
        article_url = "https://www.nytimes.com/2019/10/10/world/americas/amazon-fires-brazil-cattle.html"
        response = register(article_url)
        result = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(result), 0)


class TestGetCharityInfo(unittest.TestCase):

    def test_get_charity_info(self):
        email = "alex.rubin@duke.edu"
        response = test_app.post(
            '/get_charity_info',
            data=dict(fname="Alex",
                      lname="Rubin",
                      email=email,
                      charity_name="newspark",
                      charity_link="https://newspark.us",
                      project_name="newspark launch",
                      project_description="blah blah",
                      project_country="United States",
                      project_goal="$1,000,000",
                      project_raised="$0"),
            follow_redirects=True
        )
        self.assertEqual(response.status_code, 200)

        current_db = dynamodb.Table('newspark_projects')

        response = current_db.get_item(
            Key={
                'email': email
            }
        )

        self.assertTrue('Item' in response)  # project added to the database

        # delete project from database
        current_db.delete_item(
            Key={
                'email': email
            }
        )

if __name__ == '__main__':
    unittest.main()
