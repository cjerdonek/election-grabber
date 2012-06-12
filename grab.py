import csv
import os
import urllib

from bs4 import BeautifulSoup

URL_FORMAT = "http://vote.sos.ca.gov/returns/%s/district/%s/"

ELECTION_TYPES = [
    ("us-congress", range(1, 54)),
    ("state-assembly", range(1, 81)),
    ("state-senate", range(1, 40, 2)),
]

class Candidate(object):

    def __init__(self, name, party, percent):
        self.name = name
        self.party = party
        self.percent = percent

    def __str__(self):
        return "%s (%s, %s%%)" % (self.name, self.party, self.percent)

def make_path(label, _id):
    return os.path.join(label, "%s.html" % _id)


def make_url(label, _id):
    return URL_FORMAT % (label, _id)


def download_url(url, path):
    print("Writing %s to:\n  %s" % (url, path))
    f = urllib.urlopen(url)
    b = f.read()
    with open(path, 'wb') as f:
        f.write(b)


def download_urls(label, ids, url_format):
    """
    Arguments:

      url_format: a format string for an URL whose sole format parameter
        is an id in ids.

    """
    target_dir = label

    if not os.path.exists(target_dir):
        os.mkdir(target_dir)

    for _id in ids:
        url = url_format % (label, _id)
        path = make_path(label, _id)
        download_url(url, path)


def download_all():
    congress_ids = range(1, 54)
    state_assembly_ids = range(1, 81)
    state_senate_ids = range(1, 40, 2)

    url_format = "http://vote.sos.ca.gov/returns/%s/district/%s/"

    download_urls("us-congress", congress_ids, url_format)
    download_urls("state-assembly", state_assembly_ids, url_format)
    download_urls("state-senate", state_senate_ids, url_format)


def parse_title(soup):
    tag = soup.find_all('h1')[1]  # the second h1
    s = tag.string.split("-")[0].strip()
    return s

def parse_name(row):
    tag = row.find("td", {"class": "candName"})
    return tag.contents[0]

def parse_party(row):
    party_string = "Party Preference: "
    s = str(row)
    index = s.find(party_string)
    party_index = index + len(party_string)
    party = s[party_index:party_index + 3]
    return party

def parse_percent(row):
    tag = row.find("span", {"class": "bar"})
    return float(tag.string[:-1])

def parse_candidate(row):
    name = parse_name(row)
    party = parse_party(row)
    percent = parse_percent(row)

    candidate = Candidate(name, party, percent)

    return candidate

def parse_candidates(soup):
    """
    Return a list of the candidates sorted by percent vote.

    """
    results_table = soup.find("table", {"class": "resultsTable"})
    rows = results_table.find_all("tr")
    candidates = []
    for row in rows[1:]:
        candidate = parse_candidate(row)
        candidates.append(candidate)

    key = lambda cand: -1 * cand.percent
    candidates = sorted(candidates, key=key)
    return candidates


def parse(label, _id):
    path = make_path(label, _id)

    with open(path) as f:
        soup = BeautifulSoup(f)

    title = parse_title(soup)
    candidates = parse_candidates(soup)

    return title, candidates


def write_csv(path, rows):
    """
    election name, url, candidate count, total percent, percents

    """
    with open(path, "wb") as f:
        writer = csv.writer(f)
        for row in rows:
            writer.writerow(row)


def create_row(label, _id):
    name, candidates = parse(label, _id)
    url = make_url(label, _id)
    candidate_count = len(candidates)
    total = sum([candidate.percent for candidate in candidates])
    miss = candidates[1].percent - candidates[2].percent if candidate_count > 2 else 100

    row = [name, url, candidate_count, total, miss]


    for candidate in candidates:
        row.append(candidate.percent)

    return row


def main():
    rows = []
    rows.append(['name', 'url', 'candidates', 'total', 'miss', 'percents'])

    for election_type in ELECTION_TYPES:
        label, ids = election_type
        for _id in ids:
            row = create_row(label, _id)
            rows.append(row)

    write_csv("California Primary 2012-06-05.csv", rows)


if __name__=='__main__':
    main()
