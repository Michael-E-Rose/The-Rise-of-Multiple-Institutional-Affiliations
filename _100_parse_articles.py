#!/usr/bin/env python3
# Author:   Michael E. Rose <michael.ernst.rose@gmail.com>
"""Parses all articles published in our journals of interest to write
field-wise lists of articles with multiaffiliations for specific countries.
"""

from configparser import ConfigParser
from glob import glob
from math import ceil
from os.path import basename, splitext

import pandas as pd
from pybliometrics.scopus import ContentAffiliationRetrieval, ScopusSearch
from pybliometrics.scopus.exception import ScopusException

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
PUB_TYPES = {'ar', 're', 'no', 'cp', 'ip', 'sh'}
CHUNK_SIZE = 1300000  # Limit files to this number of lines

# Countries we look at
_country_whitelist = set(pd.read_csv(COUNTRY_WHITELIST)['country'])
# Blacklisted affiliation pairings
df = pd.read_csv(AFFILIATION_BLACKLIST, index_col=0)
df.index = df.index.astype(str)
df['children'] = df['children'].str.split(', ').apply(set)
_affiliation_blacklist = df['children'].to_dict()
# Definitions
config = ConfigParser()
config.optionxform = str
config.read("./definitions.cfg")
_aff_map = dict(config["org types"])
_country_map = dict(config["country names"])
# Auxiliary containers
_aff_countries = pd.read_csv(CORRECTION_FILE, dtype=object)
_aff_countries = _aff_countries.set_index("scopus_id")["country"].to_dict()
_aff_types = {}
_aff_missing_countries = set()


def count_pages(s):
    """Attempt to compute the number of pages of an article."""
    try:
        parts = s.split("-")
        return int(parts[1]) - int(parts[0])
    except (AttributeError, IndexError, ValueError):
        return None


def get_affiliations(pub):
    """Return nested list of affiliation IDs for org-profile affiliations.

    Filter those pairs, where one member is a university system profile and
    the other member a member of that system.
    """
    affs = []
    nonorg = []
    for auth_affs in [aff.split("-") for aff in pub.author_afids.split(";")]:
        # Filter missing profiles
        org = [a for a in auth_affs if a]
        nonorg.extend([a for a in auth_affs if a.startswith('1')])
        # Filter university systems if their children are present too
        intersection = set(org).intersection(_affiliation_blacklist.keys())
        for parent in intersection:
            children = _affiliation_blacklist[parent]
            if children.intersection(auth_affs):
                org.remove(parent)
        affs.append(org)
    return affs, len(nonorg)


def get_country(aff_id, refresh=350):
    """Get country of an affiliation."""
    try:
        country = _aff_countries[aff_id]
    except KeyError:
        try:
            aff = ContentAffiliationRetrieval(aff_id, refresh=refresh)
            country = aff.country or "Unknown"
        except ScopusException:
            country = "Unknown"
        if aff_id.startswith("6") and country == "Unknown":
            _aff_missing_countries.add(aff_id)
        country = _country_map.get(country, country)
        _aff_countries[aff_id] = country
    return country


def get_type(aff_ids, refresh=350):
    """Return types of affiliations recorded by Scopus."""
    out = []
    for aff_id in aff_ids:
        # Use parsed information or load new information
        try:
            aff_type = _aff_types[aff_id]
        except KeyError:
            if aff_id.startswith("1"):
                aff_type = "?"
            else:
                try:
                    aff = ContentAffiliationRetrieval(aff_id, refresh=refresh)
                    aff_type = aff.org_type.split("|")[0]
                    aff_type = _aff_map.get(aff_type, aff_type)
                except (AttributeError, ScopusException):
                    aff_type = "?"
            _aff_types[aff_id] = aff_type
        out.append(aff_type)
    return tuple(sorted(out, reverse=True))


def panel_write_or_add(fname, value, field, year):
    """Write DataFrame with information on yearly counts to a file that might
    already exist.
    """
    try:
        dat = pd.read_csv(fname, index_col=0)
    except FileNotFoundError:
        dat = pd.DataFrame()
    dat.loc[year, field] = value
    dat = dat[sorted(dat.columns)].sort_index()
    dat.to_csv(fname, index_label="year")


def print_progress(iteration, total, length=50):
    """Print terminal progress bar."""
    share = iteration / float(total)
    filled_len = int(length * iteration // total)
    bar = "█" * filled_len + "-" * (length - filled_len)
    print(f"\rProgress: |{bar}| {share:.2%} complete", end="\r")
    if iteration == total:
        print()


def robust_query(q, refresh=False, fields=("eid", "coverDate")):
    """Wrapper function for individual ScopusSearch query."""
    try:
        s = ScopusSearch(q, refresh=refresh, integrity_fields=fields)
        res = s.results
    except (AttributeError, KeyError):
        res = ScopusSearch(q, refresh=True).results
    return res or []


def main():
    order = ["eid", "source_id", "author", "author_count", "affiliations",
             "countries", "types"]
    # Parse each field individually
    for f in glob(SOURCE_FOLDER + "[0-9][0-9].csv"):
        asjc = splitext(basename(f))[0]
        source_ids = pd.read_csv(f)['Sourceid'].tolist()
        n_sources = len(source_ids)
        print(f">>> Working on field {asjc} using up to {n_sources:,} sources...")
        for year in range(START, END+1):
            # Containers
            n_pubs = 0
            n_articles = 0
            n_useful = 0
            n_used = 0
            n_nonorgp = 0
            docs = []
            print(f"... processing publications for {year}...")
            print_progress(0, n_sources)
            for i, source_id in enumerate(source_ids):
                # Download publications and filter
                q = f"SOURCE-ID({source_id}) AND PUBYEAR IS {year}"
                pubs = robust_query(q, refresh=600)
                n_pubs += len(pubs)
                pubs = [p for p in pubs if p.subtype and p.subtype in PUB_TYPES]
                n_articles += len(pubs)
                pubs = [p for p in pubs if p.author_afids and p.author_ids]
                n_useful += len(pubs)
                # Parse information document-wise
                print_progress(i+1, n_sources)
                for pub in pubs:
                    valid = False
                    auths = pub.author_ids.split(";")
                    affs, nonorg = get_affiliations(pub)
                    if nonorg:  # At least one author-affiliation obs not useful
                        n_nonorgp += 1
                    # Parse information author-wise
                    for auth, auth_affs in zip(auths, affs):
                        if len(auth) == 1 or not auth_affs:
                            continue
                        # Country-information
                        countries = [get_country(a) for a in auth_affs]
                        first_country = countries[0]
                        if first_country not in _country_whitelist or not countries:
                            continue
                        # Finalize
                        new = [pub.eid, source_id, auth, pub.author_count,
                               ";".join(auth_affs), "-".join(countries),
                               "-".join(get_type(auth_affs))]
                        docs.append(new)
                        valid = True
                    if valid:
                        n_used += 1

            # Write documents in chunks
            docs = pd.DataFrame(docs, columns=order)[order].set_index("eid")
            n_chunks = ceil(docs.shape[0]/CHUNK_SIZE)
            for chunk in range(n_chunks):
                fname = f"{ARTICLES_FOLDER}articles_{asjc}-{year}_{chunk}.csv"
                start = chunk*CHUNK_SIZE
                end = (chunk+1)*CHUNK_SIZE
                docs.iloc[start:end].to_csv(fname)
            del docs
            # Statistics
            combs = [("nonorg_papers", n_nonorgp), ("publications", n_pubs),
                     ("articles", n_articles), ("useful", n_useful), ("used", n_used)]
            for stub, data in combs:
                fname = f"{META_FOLDER}num_{stub}.csv"
                panel_write_or_add(fname, data, asjc, year)

    # Maintenance
    if _aff_missing_countries:
        print(f">>> {len(_aff_missing_countries)} aff profiles w/o country: "
              f"{', '.join(sorted(_aff_missing_countries))}")


if __name__ == '__main__':
    main()
