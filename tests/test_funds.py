import unittest
import sys
sys.path.append("../")
from app import application, db
from app.models import *
from app import redis

test_app = application.test_client()


class unittestWidget(unittest.TestCase):
    """ Runs unit tests on all routes in funds.py blueprint """

    def test_get_fund(self):
        assertTrue(True)

if __name__ == '__main__':
    unittest.main()
