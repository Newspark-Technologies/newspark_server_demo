from app.models import *
import ahocorasick
import _pickle as cPickle


def create_automation():
    """ Creates a trie for Aho–Corasick algorithm from tags and stores in pickle file. """

    corona_tags = ['corona', 'covid', 'pandemic', 'remote', 'virus', 'social distancing', 'quarantine']
    race_tags = ['blm', 'black lives matter', 'racis', 'protests', 'civil rights', 'immigration']

    auto = ahocorasick.Automaton()

    for tag in corona_tags:
        auto.add_word(tag, ('corona', tag))

    for tag in race_tags:
        auto.add_word(tag, ('race', tag))

    auto.make_automaton()

    with open('tags.pickle', 'wb') as output_file:
        cPickle.dump(auto, output_file)

    return None


def get_best_fund(article_text):
    """ Runs Aho–Corasick algorithm to search tags in an article's text. """

    with open('app/helper/tags.pickle', 'rb') as input_file:
        auto = cPickle.load(input_file)

    corona_count = 0
    race_count = 0
    for end_ind, found in auto.iter(article_text):
        group = found[0]
        if group == 'corona':
            corona_count += 1
        else:
            race_count += 1

    if race_count == 0 and corona_count == 0:
        return Fund.query.filter_by(fund_name='Local Community Fund').first()

    elif corona_count > race_count:
        return Fund.query.filter_by(fund_name='Coronavirus Relief Fund').first()

    else:
        return Fund.query.filter_by(fund_name='Racial Justice Fund').first()


if __name__ == "__main__":
    create_automation()
