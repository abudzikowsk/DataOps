from collections import Counter
from typing import Annotated

import pandas as pd
import typer
from pandas.core.common import flatten

from helpers import load_users, clean_users, login_user

app = typer.Typer()


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


if __name__ == "__main__":
    app()
