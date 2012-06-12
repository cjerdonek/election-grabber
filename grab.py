# encoding: utf-8
#
# Copyright (C) 2012 Chris Jerdonek. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# * The names of the copyright holders may not be used to endorse or promote
#   products derived from this software without specific prior written
#   permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import csv
import os
import urllib

from bs4 import BeautifulSoup


URL_FORMAT = "http://vote.sos.ca.gov/returns/%s/district/%s/"
WEB_DATA_DIR = 'web_data'

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


def make_dir(dir_path):
    """
    Create a directory if it doesn't already exist.

    """
    if not os.path.exists(dir_path):
        os.mkdir(dir_path)


def get_data_dir(label):
    return os.path.join(WEB_DATA_DIR, label)


def get_data_path(label, _id):
    data_dir = get_data_dir(label)
    return os.path.join(data_dir, "%s.html" % _id)


def make_url(label, _id):
    return URL_FORMAT % (label, _id)


def download_url(url, path):
    print("Writing %s to:\n  %s" % (url, path))
    f = urllib.urlopen(url)
    b = f.read()
    with open(path, 'wb') as f:
        f.write(b)


def download_data(label, ids):
    """
    Arguments:

      url_format: a format string for an URL whose sole format parameter
        is an id in ids.

    """
    data_dir = get_data_dir(label)
    make_dir(data_dir)

    for _id in ids:
        url = make_url(label, _id)
        path = get_data_path(label, _id)
        download_url(url, path)


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
    path = get_data_path(label, _id)

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
        writer = csv.writer(f, lineterminator='\n')
        for row in rows:
            writer.writerow(row)


def create_row(label, _id):
    name, candidates = parse(label, _id)
    url = make_url(label, _id)
    candidate_count = len(candidates)
    total = sum([candidate.percent for candidate in candidates])

    if candidate_count > 3:
        exhausted = sum([candidate.percent for candidate in candidates[3:]])
    else:
        exhausted = 0

    miss = candidates[1].percent - candidates[2].percent if candidate_count > 2 else 100

    uncertain = 1 if exhausted > miss else 0

    row = [name, url, candidate_count, total, exhausted, miss, uncertain]


    for candidate in candidates:
        row.append(candidate.percent)

    return row


def main(should_download=False):
    make_dir(WEB_DATA_DIR)

    rows = []
    rows.append(['name', 'url', 'candidates', 'total', 'exhausted', 'miss', 'uncertain', 'percents*'])

    for election_type in ELECTION_TYPES:
        label, ids = election_type

        if should_download:
            download_data(label, ids)

        for _id in ids:
            row = create_row(label, _id)
            rows.append(row)

    write_csv("California Primary 2012-06-05.csv", rows)


if __name__=='__main__':
    main()
