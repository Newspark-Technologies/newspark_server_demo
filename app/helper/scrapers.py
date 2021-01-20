from bs4 import BeautifulSoup
import requests
import datetime
import urllib3


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def indiana_scraper(url):
    info = {"title": "", "date": "", "content": ""}

    response = requests.get(url, verify=False)
    html = response.text
    soup = BeautifulSoup(html, "lxml")

    title = soup.find('div', {'class': 'col-md-12 article-header'}).find('h1')
    info["title"] = title.getText()

    # date = soup.find('div', {'class': 'row navbar-sub-brand'}).find('div')
    # info["date"] = date.getText().strip()

    article_date = soup.find('span', {'class': 'text-secondary'}).getText().strip()

    try:
        if 'hour' in article_date or 'minute' in article_date:
            date_time_obj = datetime.datetime.now()

        else:
            date_info = article_date.split(' ')
            day = date_info[2].replace(',', '')
            date_time_str = f'{date_info[1]} {day} {date_info[3]} {date_info[4]}{date_info[5]}'
            date_time_obj = datetime.datetime.strptime(date_time_str, '%b %d %Y %I:%M%p')

    except:
        date_time_obj = None

    # print(date_time_obj)
    info['date'] = date_time_obj

    content = soup.find('div', {'class': 'col-md-9 article-content content-col'})
    children = content.findChildren('p', recurisve=False)

    text = ""
    for child in children:
        text += (child.getText().lstrip().rstrip())
        text += " "

    info['content'] = text

    return info


def get_article_text(link):
    response = requests.get(link, verify=False)
    soup = BeautifulSoup(response.text, "lxml")

    if 'cnn' in link:
        elements = soup.find_all("div", {"class": 'zn-body__paragraph'})

    # other newspapers
    else:
        elements = soup.findAll('p')

    texts = [element.text.strip() for element in elements]
    article = " ".join(texts)

    return article


def emory_scraper(url):
    response = requests.get(url, verify=False)
    html = response.text
    soup = BeautifulSoup(html, "lxml")

    article_title = soup.find('h1', {'class': 'entry-title'}).getText()
    elements = soup.findAll('span', attrs={'style': 'font-weight: 400;'})
    article_text = ''.join(e.getText() for e in elements)

    info = {"title": article_title.lower(), "content": article_text.lower()}

    return info