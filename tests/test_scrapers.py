import sys
sys.path.append("../")
from app.helper.scrapers import indiana_scraper

url = 'https://www.idsnews.com/article/2020/06/iu-professors-voice-concerns-about-fall-semester-plan'
print(indiana_scraper(url))

