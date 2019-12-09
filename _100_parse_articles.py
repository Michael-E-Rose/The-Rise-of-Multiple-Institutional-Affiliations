#!/usr/bin/env python3
# Author:   Michael E. Rose <michael.ernst.rose@gmail.com>
"""Parses all articles published in our journals of interest to gather
information on:
    1. Field-wise lists of articles with multiaffiliations for specific
       countries
    2. Field-year-wise counts of affiliation country combinations
"""

from collections import Counter, defaultdict
from configparser import ConfigParser
from glob import glob
from itertools import combinations
from json import JSONDecodeError
from math import ceil
from os.path import basename, splitext

import pandas as pd
from pybliometrics.scopus import ContentAffiliationRetrieval, ScopusSearch
from pybliometrics.scopus.exception import ScopusException

from _002_sample_journals import write_panel


SOURCE_FOLDER = "./002_journal_samples/"
AFFILIATION_BLACKLIST = "./097_affiliation_blacklist/blacklist.csv"
COUNTRY_WHITELIST = "./098_country_whitelist/oecd_others.csv"
COUNTRYCOMB_FOLDER = "./100_country_combinations/"
ARTICLES_FOLDER = "./100_source_articles/"
META_FOLDER = "./100_meta_counts/"
OUTPUT_FOLDER = "./990_output/"

START = 1996  # The first year of our data
END = 2018  # The last year of our data
DOCUMENT_TYPES = set(['ar'])
CHUNK_SIZE = 1500000  # To keep file sizes small

# Countries we look at
_country_whitelist = set(pd.read_csv(COUNTRY_WHITELIST)['country'])
# Blacklisted affiliation pairings
df = pd.read_csv(AFFILIATION_BLACKLIST, index_col=0)
df.index = df.index.astype(str)
df['children'] = df['children'].str.split(', ').apply(set)
_affiliation_blacklist = df['children'].to_dict()
# Auxiliary containers
_aff_countries = {}
_aff_types = {}
# Definitions
config = ConfigParser()
config.optionxform = str
config.read("./definitions.cfg")
_aff_map = dict(config["org types"])
_country_map = dict(config["country names"])


def count_pages(s):
    """Attempt to compute the number of pages of an article."""
    try:
        parts = s.split("-")
        return int(parts[1]) - int(parts[0])
    except (AttributeError, IndexError, ValueError):
        return None


def get_articles(journals, year, refresh=False):
    """Get list of published articles from a set of journals."""
    res = []
    for source_id in journals:
        q = "SOURCE-ID({}) AND PUBYEAR IS {}".format(source_id, year)
        new = query(q, refresh=refresh)
        res.extend(new or [])
    return [p for p in res if p.subtype and p.subtype in DOCUMENT_TYPES]


def get_affiliations(doc):
    """Return nested list of affiliation IDs for org-profile affiliations.

    Filter those pairs, where one member is a university system profile and
    the other member a member of that system.
    """
    affs = []
    nonorg = []
    for auth_affs in [aff.split("-") for aff in doc.author_afids.split(";")]:
        # Filter non-org profiles
        org = [a for a in auth_affs if a.startswith('6')]
        nonorg.extend([a for a in auth_affs if a.startswith('1')])
        # Filter university systems if their children are present too
        intersection = set(org).intersection(_affiliation_blacklist.keys())
        for parent in intersection:
            children = _affiliation_blacklist[parent]
            if children.intersection(auth_affs):
                org.remove(parent)
        affs.append(org)
    return affs, len(nonorg)


def get_country(aff):
    """Get country of an affiliation."""
    try:
        return _aff_countries[aff]
    except KeyError:
        try:
            country = ContentAffiliationRetrieval(aff).country
        except ScopusException:
            country = None
        if not country:
            country = ""
        country = _country_map.get(country, country)
        _aff_countries[aff] = country
        return country


def get_type(aff_ids):
    """Return types of affiliations recorded by Scopus."""
    out = []
    for aff_id in aff_ids:
        # Use parsed information or load new information
        try:
            aff_type = _aff_types[aff_id]
        except KeyError:
            try:
                aff_type = ContentAffiliationRetrieval(aff_id).org_type
                aff_type = aff_type.split("|")[0]
            except ScopusException as e:
                aff_type = None
            aff_type = _aff_map.get(aff_type, aff_type)
            _aff_types[aff_id] = aff_type
        if not aff_type:
            print(aff_id)
            continue
        out.append(aff_type)
    return tuple(sorted(out, reverse=True))


def panel_write_or_add(fname, data, field):
    """Write DataFrame with information on yearly counts to a file that might
    already exist.
    """
    try:
        df = pd.read_csv(fname, index_col=0)
        df.index = df.index.astype(str)
    except FileNotFoundError:
        df = pd.DataFrame()
    df[field] = pd.Series(data)
    df.index.name = "year"
    df = df[sorted(df.columns)]
    df.to_csv(fname)


def query(q, refresh=False):
    """Wrapper function for query of a journal-year combination."""
    try:
        s = ScopusSearch(q, refresh=refresh)
    except JSONDecodeError:
        s = ScopusSearch(q, refresh=True)
    n = s.get_results_size()
    try:
        return s.results
    except KeyError:
        if n < 6000:
            return robust_query(q, refresh=True)
        else:
            res = []
            for i in range(0, 10):
                q_1 = q + " AND EID(*{})".format(i)
                res.extend(robust_query(q_1))
            return res


def robust_query(q, refresh=False):
    """Wrapper function for individual ScopusSearch query."""
    try:
        return ScopusSearch(q, refresh=refresh).results
    except KeyError:
        return ScopusSearch(q, refresh=True).results


def write_combinations(d, fname):
    """Turn dictionary with tuple-keys into DataFrame listing the occurrences
    and save file.
    """
    combs = Counter(d).items()
    df = pd.DataFrame(combs).groupby(0).sum().reset_index()
    df = pd.concat([df[0].apply(pd.Series), df[1]], axis=1)
    df.columns = list(df.columns[:-1]) + ["count"]
    df.sort_values("count", ascending=False).to_csv(fname, index=False)


def main():
    # Parse each field individually
    for f in glob(SOURCE_FOLDER + "*.csv"):
        asjc = splitext(basename(f))[0]
        if asjc == 'journal-counts':
            continue
        source_ids = pd.read_csv(f)['Sourceid'].tolist()
        print(">>> Now working on field {}...".format(asjc))
        country_shares = defaultdict(
                lambda: {'total': set(), 'with multiaff': set(),
                         'with foreign multiaff': set()})
        au_unique = defaultdict(lambda: None)
        au_unique["all"] = set()
        p_unique = defaultdict(lambda: None)
        use_unique = defaultdict(lambda: None)
        p_nonorg = defaultdict(lambda: 0)
        obs_nonorg = defaultdict(lambda: 0)
        docs = []
        for year in range(START, END+1):
            # Get articles
            res = get_articles(source_ids, year)
            total = len(res)
            # Filter articles with missing author or affiliation information
            res = [p for p in res if p.author_afids and p.author_ids]
            print("...{}: {:,} ({:,}) articles ".format(year, total, len(res)))
            # Containers
            country_combinations = defaultdict(lambda: defaultdict(lambda: 0))
            # Parse information document-wise
            for p in res:
                authors = p.author_ids.split(";")
                affs, nonorg = get_affiliations(p)
                if nonorg:  # At least one author-affiliation obs not useful
                    p_nonorg[year] += 1
                # Parse information author-wise
                for auth, aff in zip(authors, affs):
                    if auth in ("1", "8"):  # Anonymous author or group
                        continue
                    if not aff:  # Author has non-org affiliation
                        obs_nonorg[year] += 1
                        continue
                    countries = [get_country(a) for a in aff]
                    first_country = countries[0]  # Country of first affiliation
                    if first_country not in _country_whitelist:
                        continue
                    country_shares[("all", year)]["total"].add(auth)
                    country_shares[(first_country, year)]["total"].add(auth)
                    types = "-".join(get_type(aff))
                    multiaff = int(len(aff) > 1) or None
                    if multiaff:
                        country_shares[("all", year)]["with multiaff"].add(auth)
                        country_shares[(first_country, year)]["with multiaff"].add(auth)
                        for comb in combinations(sorted(countries), 2):
                            country_combinations[comb[0]][comb[1]] += 1
                    foreign_aff = int(len(set(countries)) > 1) or None
                    if foreign_aff:
                        country_shares[("all", year)]["with foreign multiaff"].add(auth)
                        country_shares[(first_country, year)]["with foreign multiaff"].add(auth)
                    new = [p.eid, p.source_id, year, auth, p.author_count,
                           first_country, types, multiaff, foreign_aff]
                    docs.append(new)

            # Combinations of countries of multiaffs
            fname = "{}{}_{}.csv".format(COUNTRYCOMB_FOLDER, asjc, year)
            write_panel(country_combinations, fname, sort=True)
            # Statistics
            year = str(year)
            p_unique[year] = total
            use_unique[year] = len(res)
            au_unique[year] = len(country_shares[("all", int(year))]["total"])
            au_unique["all"].update(country_shares[("all", int(year))]["total"])

        # Write out information on articles in chunks
        cols = ["eid", "source_id", "year", "author", "author_count",
                "country", "inst_types", "multiaff", "foreign_multiaff"]
        out = pd.DataFrame(docs, columns=cols)[cols]
        n_chunks = ceil(out.shape[0]/CHUNK_SIZE)
        for chunk in range(n_chunks):
            fname = "{}articles_{}-{}.csv".format(ARTICLES_FOLDER, asjc, chunk)
            start = (chunk)*CHUNK_SIZE
            end = (chunk+1)*CHUNK_SIZE
            out.iloc[start:end].set_index("eid").to_csv(fname)

        # Statistics
        au_unique["all"] = len(au_unique["all"])
        combs = [("unique_papers", p_unique), ("unique_papers-useful", use_unique),
                 ("unique_authors", au_unique), ("nonorg_papers", p_nonorg),
                 ("nonorg_obs", obs_nonorg)]
        for stub, data in combs:
            fname = "{}num_{}.csv".format(META_FOLDER, stub)
            panel_write_or_add(fname, data, asjc)


if __name__ == '__main__':
    main()
