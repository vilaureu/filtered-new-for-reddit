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

from atomicwrites import atomic_write
from collections import defaultdict
from configparser import ConfigParser, SectionProxy
import json
from praw import Reddit
import re
from typing import List, Iterator

REDDIT_URL = "https://www.reddit.com"
CONFIG_FILE = "filterednew.ini"
LOG_FILE = "filterednew.log"
DEFAULT_LIMIT = 10
DEFAULT_KEEP = 20
DEFAULT_IGNORE_CASE = True


def yield_dedup(a: List, b: List) -> Iterator:
    """Yield contents from a which are not in b and then yield from b."""
    for x in a:
        if x not in b:
            yield x
    yield from b


def subreddit(sub: str, config: SectionProxy, reddit: Reddit, log: List[str]) \
        -> Iterator[str]:
    """Process a subreddit by retrieving and filtering submissions.

    :param sub: name of the subreddit
    :param config: configuration file section describing the subreddit
    :param reddit: reddit API object
    :param log: previous submission ids from the log file
    :yield: the processed submission ids
    """
    limit = config.getint("Limit", DEFAULT_LIMIT)
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
        sid = submission.id
        content = selftext if is_self else url

        yield sid
        if sid in log:
            continue

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
    """
    Connect to the reddit API, read the config file and process the subreddits.
    """
    reddit = Reddit()

    config = ConfigParser()
    config.read(CONFIG_FILE)

    try:
        with open(LOG_FILE, "r") as f:
            log = json.load(f)
    except IOError:
        log = {}
    log = defaultdict(list, log)
    log_new = {}

    for section in config.sections():
        new_posts = subreddit(section, config[section], reddit, log[section])
        new_posts = list(new_posts)
        new_posts.reverse()
        log_new[section] = list(yield_dedup(log[section], new_posts))

        keep = config[section].getint("Keep", DEFAULT_KEEP)
        log_new[section] = log_new[section][-keep:]

    with atomic_write(LOG_FILE, overwrite=True) as f:
        json.dump(log_new, f)


if __name__ == "__main__":
    main()
