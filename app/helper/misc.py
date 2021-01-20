from app import db
import hashlib
import os
import json
import pandas as pd
import inspect


def secure_password(password):
    salt = os.urandom(32)  # 32 bytes
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)  # 64 bytes
    return salt, key


def get_available_projects():
    # select projects that are not removed and are from verified charities
    sql_query = '''select project_id, project_name
                            from projects, organizations
                            where projects.organization_id=organizations.email
                            and projects.removed=FALSE
                            and projects.newspaper_id='Indiana Daily Student'
                            and organizations.verified=TRUE
                            and organizations.organization_type='Non-profit';'''

    conn = db.engine.connect().connection
    projects_df = pd.read_sql(sql_query, conn)
    conn.close()

    return projects_df


def get_projects_from_article(article_url, num_ids):
    projects = ['project_id1', 'project_id2', 'project_id3', 'project_id4', 'project_id5', 'project_id6'][:num_ids]
    project_info_list = []
    for p in projects:
        sql_query = '''select *
                                    from articles, projects, organizations
                                    where articles.article_link='{}'
                                    and articles.{}=projects.project_id
                                    and projects.organization_id=organizations.email
                                    '''.format(article_url, p)

        conn = db.engine.connect().connection
        df = pd.read_sql(sql_query, conn)
        conn.close()
        df.drop(projects + ['password', 'salt'], axis=1, inplace=True)

        project_info = list(df.T.to_dict().values())
        if len(project_info) != 0:
            project_info_list.append(project_info[0])

    return project_info_list


def save_article_data(s3_client, article_link, article_title, article_date_time, article_text):
    bucket = 'newspark-matching-data'
    # bad_chars = ['.', ',', '/']
    # new_article_link = str(filter(lambda i: i not in bad_chars, article_link))
    file_name = 'article-data/{}.json'.format(article_link)

    # calling_file_name = inspect.stack()[-1].filename.split("/")[-1]
    # file_path = f'downloads/{file_name}'
    # if 'test' in calling_file_name:
    #     file_path = f'../downloads/{file_name}'
    #
    # s3_client.download_file(Bucket=bucket, Key=file_name, Filename=file_path)

    article_date_time = str(article_date_time)  # cannot store datetime in json
    article_row = {"article_link": article_link, "article_title": article_title,
                   "article_date_time": article_date_time, "article_text": article_text}

    # s3object = s3_client.get_object(Bucket=bucket, Key=file_name)
    s3_client.put_object(Bucket=bucket, Key=file_name, Body=json.dumps(article_row))

    # # file is empty
    # if os.stat(file_path).st_size == 0:
    #     data = {"articles": [article_row]}
    #     with open(file_path, 'w') as json_file:
    #         json.dump(data, json_file, indent=4)

    # with open(file_path, 'r') as json_file:
    #     data = json.load(json_file)
    #     articles = data['articles']
    #     articles.append(article_row)
    #
    # with open(file_path, 'w') as json_file:
    #     json.dump({'articles': articles}, json_file, indent=4)

    # s3_client.upload_file(Filename=file_path, Bucket=bucket, Key=file_name)
    # os.remove(file_path)

    return None


def update_recommendations(s3_client, article_link, ids, other_ids):
    bucket = 'newspark-matching-data'
    # bad_chars = ['.', ',', '/']
    # new_article_link = str(filter(lambda i: i not in bad_chars, article_link))
    file_name = 'labeled-data/{}.json'.format(article_link)

    # calling_file_name = inspect.stack()[-1].filename.split("/")[-1]
    # file_path = f'downloads/{file_name}'
    # if 'test' in calling_file_name:
    #     file_path = f'../downloads/{file_name}'
    #
    # s3_client.download_file(Bucket=bucket, Key=file_name, Filename=file_path)

    # # file is empty
    # if os.stat(file_path).st_size == 0:
    #     data = {"articles": [{"article_link": article_link, "recommended_projects": ids,
    #                           "other_projects": other_ids}]}
    #     with open(file_path, 'w') as json_file:
    #         json.dump(data, json_file, indent=4)
    #
    # else:
    #     found = False
    #     with open(file_path, 'r') as json_file:
    #         data = json.load(json_file)
    #         articles = data['articles']
    #         # print(len(articles))
    #         for i, article in enumerate(articles):
    #             # found matching article link
    #             if article['article_link'] == article_link:
    #                 articles[i]['recommended_projects'] = ids
    #                 articles[i]['other_projects'] = other_ids
    #                 found = True
    #                 # print("found")
    #                 break
    #
    #         if not found:
    #             # print("not found")
    #             articles.append({"article_link": article_link, "recommended_projects": ids,
    #                              "other_projects": other_ids})
    #
    #     with open(file_path, 'w') as json_file:
    #         json.dump({'articles': articles}, json_file, indent=4)
    #
    # s3_client.upload_file(Filename=file_path, Bucket=bucket, Key=file_name)
    # os.remove(file_path)

    data = {"articles": [{"article_link": article_link, "recommended_projects": ids,
                          "other_projects": other_ids}]}
    s3_client.put_object(Bucket=bucket, Key=file_name, Body=json.dumps(data))

    return None


def save_payment_info(s3_client, full_name, bank_branch_address, bank_name, account_type, bank_routing_number,
                      bank_account_number, publisher_charity, primary_id):
    bucket = 'newspark-payment'
    file_name = f'{publisher_charity}/routers.json'

    payment_data = json.load(s3_client.get_object(Bucket=bucket, Key=file_name)['Body'])

    row = {
            'full_name': full_name,
            'bank_branch_address': bank_branch_address,
            'bank_name': bank_name,
            'account_type': account_type,
            'bank_routing_number': bank_routing_number,
            'bank_account_number': bank_account_number,
            'primary_id': primary_id
    }

    # file is empty
    if not payment_data:
        payment_data = {'accounts': [row]}
    else:
        found = False
        accounts = payment_data['accounts']
        for i, account in enumerate(accounts):
            if accounts[i]['primary_id'] == primary_id:
                accounts[i] = row
                found = True
                break

        if not found:
            payment_data['accounts'].append(row)

    s3_client.put_object(Bucket=bucket, Key=file_name, Body=json.dumps(payment_data))

    return None
