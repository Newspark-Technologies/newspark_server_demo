from app import s3
import os
import json


def clear_s3_buckets(clear_payment, clear_articles, clear_matching):
    if clear_payment:
        s3.put_object(Bucket='newspark-payment', Key='routers.json', Body=json.dumps({}))
        print("cleared payment")

    if clear_articles:
        s3.put_object(Bucket='newspark-matching-data', Key='articles.json', Body=json.dumps({}))
        print("cleared articles")

    if clear_matching:
        s3.put_object(Bucket='newspark-matching-data', Key='matching.json', Body=json.dumps({}))
        print("cleared matching")

    return None


if __name__ == '__main__':
    clear_s3_buckets(clear_payment=True,
                     clear_articles=True,
                     clear_matching=True)
