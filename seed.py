from collections import namedtuple
import pprint

import requests

REPO_URL = 'https://api.github.com/repos/scrapy/scrapy'

user_data = ['company', 'created_at', 'followers', 'hireable', 'languages',
             'location', 'login', 'public_repos']

User = namedtuple('User', user_data)


def dump_to_file(filename, user_list):
    """
    :type filename: str
    :type user_list: list[User]
    :rtype: None
    """
    with open(filename + '.csv', 'a') as csv_file:
        for user_datum in user_data:
            csv_file.write('|'.join(user_datum))


def process_user(user_url):
    """
    :type user_url: str
    :rytpe: User tuple[str]
    Given the url to query the API for the user, return a namedtuple of info
    """
    user_resp = requests.get(user_url).json()
    # Get top-level fields
    company = user_resp['company']
    created_at = user_resp['created_at']
    followers = user_resp['followers']
    hireable = user_resp['hireable']
    location = user_resp['location']
    login = user_resp['login']
    public_repos = user_resp['public_repos']
    # Iterate through repos to find max of 5 languages per user
    repos_url = user_resp['repos_url']
    repos_resp = requests.get(repos_url)
    user_langs = set([])
    for repo_data in repos_resp.json():
        if repo_data.get('language'):
            user_langs.add(repo_data['language'])
            if len(user_langs) > 4:
                break

    languages = '' if not user_langs else ','.join(user_langs)

    return User(company, created_at, followers, hireable,
                languages, location, login, public_repos)


def process_contributors(contrib_json):
    """
    :type contrib_json: dict[str]
    :rtype: list[User]
    """
    all_contributors = []
    for contrib in contrib_json:
        user_tuple = process_user(contrib['url'])
        all_contributors.append(user_tuple)

    return all_contributors


def process_forks(fork_json):
    """
    :type fork_json: dict[str]
    :rtype: list[User]
    """
    all_fork_users = []
    for fork in fork_json:
        user_url = fork_json.get('owner').get('url')
        if user_url:
            user_tuple = process_user(user_url)
            all_fork_users.append(user_tuple)

    return all_fork_users


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Query Github API for data')
    parser.add_argument('--contributors', action='store_true',
                        help='optionally gather contributor data')
    parser.add_argument('--forks', action='store_true',
                        help='optionally gather fork data')
    args = parser.parse_args()

    repo_resp = requests.get(REPO_URL).json()

    #TODO: implement exception handling for 403 rate limiting responses
    #TODO: or authenticate requests
    if args.contributors:
        print("Processing contributors")
        contributors_url = repo_resp['contributors_url']
        contrib_resp = requests.get(contributors_url)
        contributors = process_contributors(contrib_resp)
        dump_to_file('contributors', contributors)

    if args.forks:
        print("Processing forks")
        forks_url = repo_resp['forks_url']
        forks_resp = requests.get(forks_url)
        forks = process_forks(forks_resp)
        dump_to_file('forks', forks)
