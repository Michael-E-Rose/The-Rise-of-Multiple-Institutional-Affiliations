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
from math import ceil
from os.path import basename, splitext

import pandas as pd
from pybliometrics.scopus import ContentAffiliationRetrieval, ScopusSearch
from pybliometrics.scopus.exception import ScopusException

from _002_sample_journals import write_panel


SOURCE_FOLDER = "./002_journal_samples/"
CORRECTION_FILE = "./095_affiliation_correction/countries.csv"
AFFILIATION_BLACKLIST = "./097_affiliation_blacklist/blacklist.csv"
COUNTRY_WHITELIST = "./098_country_whitelist/oecd_others.csv"
COUNTRYCOMB_FOLDER = "./100_country_combinations/"
ARTICLES_FOLDER = "./100_source_articles/"
META_FOLDER = "./100_meta_counts/"
OUTPUT_FOLDER = "./990_output/"

START = 1996  # The first year of our data
END = 2019  # The last year of our data
DOCUMENT_TYPES = set(['ar', 're', 'no', 'cp', 'ip', 'sh'])
CHUNK_SIZE = 1300000  # Limit files to this number of lines

# Countries we look at
_country_whitelist = set(pd.read_csv(COUNTRY_WHITELIST)['country'])
# Blacklisted affiliation pairings
df = pd.read_csv(AFFILIATION_BLACKLIST, index_col=0)
df.index = df.index.astype(str)
df['children'] = df['children'].str.split(', ').apply(set)
_affiliation_blacklist = df['children'].to_dict()
# Auxiliary containers
_aff_countries = pd.read_csv(CORRECTION_FILE, dtype=object)
_aff_countries = _aff_countries.set_index("scopus_id")["country"].to_dict()
_aff_types = {}
_aff_missing_countries = set()
_aff_missing_types = set()
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


def get_country(aff_id, refresh=200):
    """Get country of an affiliation."""
    try:
        country = _aff_countries[aff_id]
    except KeyError:
        try:
            aff = ContentAffiliationRetrieval(aff_id, refresh=refresh)
            country = aff.country or None
        except ScopusException:
            country = None
        if not country:
            _aff_missing_countries.add(aff_id)
        country = _country_map.get(country, country)
        _aff_countries[aff_id] = country
    return country


def get_type(aff_ids, refresh=200):
    """Return types of affiliations recorded by Scopus."""
    out = []
    for aff_id in aff_ids:
        # Use parsed information or load new information
        try:
            aff_type = _aff_types[aff_id]
        except KeyError:
            try:
                aff = ContentAffiliationRetrieval(aff_id, refresh=refresh)
                aff_type = aff.org_type.split("|")[0]
            except (AttributeError, ScopusException):
                aff_type = None
            aff_type = _aff_map.get(aff_type, aff_type)
            _aff_types[aff_id] = aff_type
        if not aff_type:
            _aff_missing_types.add(aff_id)
            continue
        out.append(aff_type)
    return tuple(sorted(out, reverse=True))


def panel_write_or_add(fname, value, field, year):
    """Write DataFrame with information on yearly counts to a file that might
    already exist.
    """
    try:
        df = pd.read_csv(fname, index_col=0)
    except FileNotFoundError:
        df = pd.DataFrame()
    df.loc[year, field] = value
    df = df[sorted(df.columns)]
    df = df.sort_index()
    df.to_csv(fname, index_label="year")


def print_progress(iteration, total, length=50):
    """Print terminal progress bar."""
    share = iteration / float(total)
    filled_len = int(length * iteration // total)
    bar = "█" * filled_len + "-" * (length - filled_len)
    print(f"\rProgress: |{bar}| {share:.2%} complete", end="\r")
    if iteration == total:
        print()


def robust_query(q, refresh=False, fields=["eid", "coverDate"]):
    """Wrapper function for individual ScopusSearch query."""
    try:
        s = ScopusSearch(q, refresh=refresh,
                         integrity_fields=fields)
        res = s.results
    except (AttributeError, KeyError):
        res = ScopusSearch(q, refresh=True).results
    return res or []


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
    order = ["eid", "source_id", "year", "author", "author_count", "affiliations",
             "country", "inst_types", "multiaff", "foreign_multiaff"]
    # Parse each field individually
    for f in glob(SOURCE_FOLDER + "*.csv"):
        asjc = splitext(basename(f))[0]
        if asjc == 'journal-counts':
            continue
        source_ids = pd.read_csv(f)['Sourceid'].tolist()
        n_sources = len(source_ids)
        print(f">>> Working on field {asjc} using up to {n_sources} sources...")
        for year in range(START, END+1):
            # Containers
            n_pubs = 0
            n_useful = 0
            n_nonorgp = 0
            n_nonorgo = 0
            country_combinations = defaultdict(lambda: defaultdict(lambda: 0))
            docs = []
            print(f"... processing publications for {year}...")
            print_progress(0, n_sources)
            for i, source_id in enumerate(source_ids):
                q = f"SOURCE-ID({source_id}) AND PUBYEAR IS {year}"
                pubs = robust_query(q, refresh=600)
                pubs = [p for p in pubs if p.subtype and
                        p.subtype in DOCUMENT_TYPES]
                n_pubs += len(pubs)
                pubs = [p for p in pubs if p.author_afids and p.author_ids]
                n_useful += len(pubs)
                # Parse information document-wise
                print_progress(i+1, n_sources)
                for i, pub in enumerate(pubs):
                    authors = pub.author_ids.split(";")
                    affs, nonorg = get_affiliations(pub)
                    if nonorg:  # At least one author-affiliation obs not useful
                        n_nonorgp += 1
                    # Parse information author-wise
                    for auth, auth_affs in zip(authors, affs):
                        if auth in ("1", "8"):  # Anonymous author or group
                            continue
                        if not auth_affs:  # Author has non-org affiliation
                            n_nonorgo += 1
                            continue
                        # Country-information
                        countries = [get_country(a) for a in auth_affs]
                        first_country = countries[0]  # Country of first affiliation
                        if first_country not in _country_whitelist:
                            continue
                        countries = list(filter(None, countries))
                        if not countries:
                            continue
                        foreign_aff = int(len(set(countries)) > 1) or None
                        # Type-information
                        types = "-".join(get_type(auth_affs))
                        multiaff = int(len(auth_affs) > 1) or None
                        if multiaff:
                            for comb in combinations(sorted(countries), 2):
                                country_combinations[comb[0]][comb[1]] += 1
                        # Finalize
                        new = [pub.eid, source_id, year, auth, pub.author_count,
                               ";".join(auth_affs), first_country, types,
                               multiaff, foreign_aff]
                        docs.append(new)

            # Write documents in chunks
            docs = pd.DataFrame(docs, columns=order)[order].set_index("eid")
            n_chunks = ceil(docs.shape[0]/CHUNK_SIZE)
            for chunk in range(n_chunks):
                if n_chunks == 1:
                    fname = f"{ARTICLES_FOLDER}articles_{asjc}-{year}.csv"
                else:
                    fname = f"{ARTICLES_FOLDER}articles_{asjc}-{year}_{chunk}.csv"
                start = (chunk)*CHUNK_SIZE
                end = (chunk+1)*CHUNK_SIZE
                docs.iloc[start:end].to_csv(fname)
            del docs
            # Combinations of countries of multiaffs
            fname = f"{COUNTRYCOMB_FOLDER}{asjc}_{year}.csv"
            write_panel(country_combinations, fname, sort=True)
            # Statistics
            combs = [("unique_papers", n_pubs), ("nonorg_papers", n_nonorgp),
                     ("nonorg_obs", n_nonorgo), ("unique_papers-useful", n_useful)]
            for stub, data in combs:
                fname = f"{META_FOLDER}num_{stub}.csv"
                panel_write_or_add(fname, data, asjc, year)

    print(f">>> {len(_aff_missing_countries)} aff profiles w/o country: "
          f"{', '.join(sorted(_aff_missing_countries))}")
    print(f">>> {len(_aff_missing_types)} aff profiles w/o type: "
          f"{', '.join(sorted(_aff_missing_types))}")


if __name__ == '__main__':
    main()
