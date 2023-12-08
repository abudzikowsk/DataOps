from collections import Counter
from typing import Annotated, Optional

import pandas as pd
import re
import typer
from lxml import objectify
from pandas.core.common import flatten


app = typer.Typer()


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


@app.command()
def print_all_accounts(
        login: Annotated[str, typer.Option(help="Login name")],
        password: Annotated[str, typer.Option(help="Password")]
):
    users = load_users()
    cleaned_users = clean_users(users)

    logged_in_user = login_user(login, password, cleaned_users, is_admin_permission=True)
    if logged_in_user is None:
        return

    print(len(cleaned_users))


@app.command()
def print_oldest_account(
        login: Annotated[str, typer.Option(help="Login name")],
        password: Annotated[str, typer.Option(help="Password")]
):
    users = load_users()
    cleaned_users = clean_users(users)

    logged_in_user = login_user(login, password, cleaned_users, is_admin_permission=True)
    if logged_in_user is None:
        return

    cleaned_users['created_at'] = pd.to_datetime(cleaned_users['created_at'])
    oldest_account = cleaned_users.sort_values('created_at').iloc[0]

    print(f"name: {oldest_account['firstname']}")
    print(f"email_address: {oldest_account['email']}")
    print(f"created_at: {oldest_account['created_at']}")


@app.command()
def group_by_age(
        login: Annotated[str, typer.Option(help="Login name")],
        password: Annotated[str, typer.Option(help="Password")]
):
    users = load_users()
    cleaned_users = clean_users(users)

    logged_in_user = login_user(login, password, cleaned_users, is_admin_permission=True)
    if logged_in_user is None:
        return

    ages = cleaned_users['children'].dropna().apply(lambda row: [child['age'] for child in row] if isinstance(row, list) else None)
    ages = list(map(int, flatten(ages)))
    age_counts = Counter(ages)

    sorted_ages = age_counts.most_common()
    sorted_ages.reverse()

    for age, count in sorted_ages:
        print(f'age: {age}, count: {count}')


@app.command()
def print_children(
        login: Annotated[str, typer.Option(help="Login name")],
        password: Annotated[str, typer.Option(help="Password")]
):
    users = load_users()
    cleaned_users = clean_users(users)

    logged_in_user = login_user(login, password, cleaned_users)
    if logged_in_user is None:
        return

    for children in logged_in_user['children']:
        for child in children:
            name = child['name']
            age = child['age']
            print(f"{name}, {age}")


@app.command()
def find_similar_children_by_age(
        login: Annotated[str, typer.Option(help="Login name")],
        password: Annotated[str, typer.Option(help="Password")]
):
    users = load_users()
    cleaned_users = clean_users(users)

    logged_in_user = login_user(login, password, cleaned_users)
    if logged_in_user is None:
        return

    current_user_children = logged_in_user['children']
    ages_to_search_for = []
    for children in current_user_children:
        for child in children:
            ages_to_search_for.append(int(child['age']))

    users_with_similar_children = []
    for user in cleaned_users.itertuples():
        if user.children is not None:
            for children in user.children:
                if children['age'] in ages_to_search_for:
                    users_with_similar_children.append(user)

    for user in users_with_similar_children:
        output = []
        output.append(f"{user.firstname}, {user.telephone_number}: ")
        for children in user.children:
            output.append(f"{children['name']}, {children['age']}; ")
        print("".join(output))


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


if __name__ == "__main__":
    app()
