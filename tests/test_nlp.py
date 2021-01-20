import unittest
import sys

sys.path.append("../")
from app.helper.nlp import *
from app.helper.get_article_text import get_article_text
from app import dynamodb


table_name = "global_giving_projects"
charities_df = create_df_from_db(dynamodb, table_name)
result_count = 6


class TestConvertNationalities(unittest.TestCase):

    def test_all_norp(self):
        entities = [("American", "NORP"), ("Chinese", "NORP"), ("British", "NORP")]
        result = convert_nationalities(entities)
        self.assertEqual(result, ["United States", "China", "Great Britain"])

    def test_some_norp(self):
        entities = [("American", "NORP"), ("Chinese", ""), ("British", "NORP")]
        result = convert_nationalities(entities)
        self.assertEqual(result, ["United States", "Chinese", "Great Britain"])


class TestConvertToCountries(unittest.TestCase):

    def test_the(self):
        loc_dict_items = {("The United States", 4), ("United States", 4)}
        result = convert_to_countries(loc_dict_items)
        self.assertEqual(result, [("United States", 8)])

    def test_abbrev(self):
        loc_dict_items = {("US", 4), ("U.S.", 4), ("N.Y.", 4), ("USA", 4)}
        result = convert_to_countries(loc_dict_items)
        self.assertEqual(result, [("United States", 16)])

    def test_unknown(self):
        loc_dict_items = {("South Korea", 4)}
        result = convert_to_countries(loc_dict_items)
        self.assertEqual(result, [("South Korea", 4)])

    def test_pycountry(self):
        loc_dict_items = {("New York", 4), ("London", 4), ("Great Britain", 4)}
        result = convert_to_countries(loc_dict_items)
        self.assertEqual(set(result), {("United Kingdom", 8), ("United States", 4)})


class TestGetCountries(unittest.TestCase):

    def test_get_countries(self):
        link = "https://www.nytimes.com/2020/04/22/business/china-coronavirus-propaganda.html"
        article_text = get_article_text(link)
        result = get_countries(article_text)
        countries = [i[0] for i in result]
        self.assertEqual(set(countries), {"China", "United States"})


class TestGetCharities(unittest.TestCase):

    def test_no_countries(self):
        country_dict = {}
        result = get_charities(country_dict=country_dict, amount=result_count, charities_df=charities_df)
        self.assertEqual(result.shape[0], result_count)

    def test_countries_one(self):
        country_dict = {"United States": 8}
        result = get_charities(country_dict=country_dict, amount=result_count, charities_df=charities_df)
        self.assertEqual(result.shape[0], result_count)

    def test_countries_two(self):
        country_dict = {"United States": 4, "China": 4}
        result = get_charities(country_dict=country_dict, amount=result_count, charities_df=charities_df)
        self.assertEqual(result.shape[0], result_count)


class TestFullJson(unittest.TestCase):

    def test_full_json(self):
        link = "https://www.nytimes.com/2020/04/22/business/china-coronavirus-propaganda.html"
        article_text = get_article_text(link)
        result = full_json(article_text, dynamodb, result_count)
        self.assertEqual(len(result), result_count)


if __name__ == '__main__':
    unittest.main()
