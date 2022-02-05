#!/usr/bin/python3

# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with
# this program. If not, see <https://www.gnu.org/licenses/>.

from configparser import ConfigParser, SectionProxy
from praw import Reddit
import re

REDDIT_URL = "https://www.reddit.com"
CONFIG_FILE = "filterednew.ini"
DEFAULT_LIMIT = 10
DEFAULT_KEEP = 20
DEFAULT_IGNORE_CASE = True


def subreddit(sub: str, config: SectionProxy, reddit: Reddit):
    limit = config.getint("Limit", DEFAULT_LIMIT)
    keep = config.getint("Keep", DEFAULT_KEEP)
    ignore_case = config.getboolean("IgnoreCase", DEFAULT_IGNORE_CASE)

    flags = re.IGNORECASE if ignore_case else 0
    regex = re.compile(config.get("Regex", ""), flags)
    regex_title = re.compile(config.get("RegexTitle", ""), flags)
    regex_body = re.compile(config.get("RegexBody", ""), flags)
    regex_url = re.compile(config.get("RegexUrl", ""), flags)

    for submission in reddit.subreddit(sub).new(limit=limit):
        title = submission.title
        is_self = submission.is_self
        selftext = submission.selftext
        url = submission.url
        permalink = submission.permalink
        content = selftext if is_self else url

        if not regex.search(title) and not regex.search(content):
            continue
        if not regex_title.search(title):
            continue
        if is_self and not regex_body.search(selftext):
            continue
        if not is_self and not regex_url.search(url):
            continue

        print(title)
        print("@", REDDIT_URL + permalink)
        print()


def main():
    reddit = Reddit()

    config = ConfigParser()
    config.read(CONFIG_FILE)
    for section in config.sections():
        subreddit(section, config[section], reddit)


if __name__ == "__main__":
    main()
