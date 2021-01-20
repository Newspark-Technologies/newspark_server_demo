# import cProfile
# from app.helper.nlp import full_json
# from app.helper.get_article_text import get_article_text
#
# def main():
#     article_url = "https://www.nytimes.com/2020/04/08/world/coronavirus-live-news-updates.html?action=click&module=Spotlight&pgtype=Homepage"
#     article_name = 'Coronavirus ravaging the nation'
#
#     article = get_article_text(article_url)
#     terms = ['corona', 'covid']
#     corona_flag = False
#
#     for term in terms:
#         if (term in article_name.lower()) or (term in article.lower()):
#             corona_flag = True
#             break
#
#     complete = full_json(article)
#
#     return None
#
# if __name__ == '__main__':
#     main()
import sys

sys.path.append("../")
from app import app, dynamodb
test_app = app.test_client()
import line_profiler
profile = line_profiler.LineProfiler()

@profile
def test_get_charities():
    url = 'https://www.idsnews.com/article/2020/06/board-of-public-safety-discusses-bloomington-police-departments-strengths-weaknesses'
    test_app.post(
        '/get_charities',
        data=dict(
            article_link=url
        )
    )

    return None