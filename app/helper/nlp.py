from collections import Counter
import pandas as pd
import pycountry
import en_core_web_sm
import inspect
import warnings
import numpy as np
from multiprocessing import Pool

warnings.filterwarnings("ignore")
nlp = en_core_web_sm.load()


def remove_stop_words(text):
    doc = nlp(text.lower())
    result = [token.text for token in doc if token.text not in nlp.Defaults.stop_words]
    return " ".join(result)


def sim(text):
    doc2 = nlp(remove_stop_words(text))
    return doc1.similarity(doc2)


def get_similarities(df):
    return df.apply(lambda row: sim(row['project_name']), axis=1)


def full_json_with_matching(projects_df, title, charity_amount, num_of_processes=2):
    global doc1
    doc1 = nlp(remove_stop_words(title))

    projects_df.set_index('project_id', drop=True, inplace=True)
    df_split = np.array_split(projects_df, num_of_processes)  # partition df
    pool = Pool(num_of_processes)
    sim_df = pd.concat(pool.map(get_similarities, df_split))
    pool.close()
    pool.join()

    top_ids = sim_df.nlargest(charity_amount).index

    return [int(i) for i in top_ids]
