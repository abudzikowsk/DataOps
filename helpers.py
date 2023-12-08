from typing import Optional

import pandas as pd
from lxml import objectify
import re


def is_valid_email(email: str) -> bool:
    pattern = r'^[^@]+@[^@]+\.[^@]{1,4}$'
    return re.match(pattern, email) is not None


def login_user(login: str, password: str, cleaned_users: pd.DataFrame, is_admin_permission: bool = False) -> Optional[pd.DataFrame]:
    user = cleaned_users.loc[(cleaned_users['email'] == login) | (cleaned_users['telephone_number'] == login)]
    if user.empty:
        print("Invalid login")
        return None

    if user['password'].item() != password:
        print("Invalid login")
        return None

    if is_admin_permission:
        if user['role'].item() != 'admin':
            print("Invalid login")
            return None

    return user


def xml_to_df(xml_str):

    root = objectify.fromstring(xml_str)
    data = []
    for user in root.iterchildren():
        user_data = {tag: user.find(tag).text for tag in ('firstname', 'telephone_number', 'email', 'password', 'role', 'created_at')}
        user_data['children'] = [{'name': child.find('name').text, 'age': int(child.find('age').text)} for child in user.children.iterchildren()] if hasattr(user, 'children') else None
        data.append(user_data)

    return pd.DataFrame(data)


def parse_children(children_str):
    if pd.isnull(children_str) or children_str == '':
        return None
    children = children_str.split(',')
    parsed_children = [{'name': child.split(' ')[0], 'age': int(child.split(' ')[1].strip('()'))} for child in children]
    return parsed_children


def load_users() -> pd.DataFrame:
    with open('./data/users_2.xml', 'r') as user_2:
        users_1 = xml_to_df(user_2.read())

    users_2 = pd.read_json("./data/a/users.json")

    with open('./data/a/b/users_1.xml', 'r') as user_1:
        users_3 = xml_to_df(user_1.read())

    users_4 = pd.read_csv("./data/a/b/users_1.csv", delimiter=';')
    users_4['children'] = users_4['children'].apply(parse_children)

    users_5 = pd.read_csv("./data/a/c/users_2.csv", delimiter=';')
    users_5['children'] = users_5['children'].apply(parse_children)

    users = pd.concat([users_1, users_2, users_3, users_4, users_5])

    return users


def clean_users(users: pd.DataFrame) -> pd.DataFrame:
    cleaned_users = users[users['email'].apply(is_valid_email)]
    cleaned_users = cleaned_users[cleaned_users['telephone_number'].notnull() & cleaned_users['telephone_number'].str.strip().ne('')]
    cleaned_users = cleaned_users.drop_duplicates(subset=['email', 'telephone_number'], keep='first')
    cleaned_users['telephone_number'] = cleaned_users['telephone_number'].str.replace('\D+', '', regex=True)
    cleaned_users['telephone_number'] = cleaned_users['telephone_number'].apply(lambda x:  x[-9:] if len(x) > 9 else x)

    pd.set_option('display.max_rows', None)
    return cleaned_users
