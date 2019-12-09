#!/usr/bin/env python3
# Author:   Michael E. Rose <michael.ernst.rose@gmail.com>
"""Draws X journals at random from the top four octiles for each field."""

from configparser import ConfigParser
from glob import glob
from math import ceil
from os.path import basename, splitext

import pandas as pd

SOURCE_FOLDER = "./000_journal_rankings/"
JOURNAL_FILE = "./001_journal_coverage/Scopus.csv"
TARGET_FOLDER = "./002_journal_samples/"
OUTPUT_FOLDER = "./990_output/"

SHARE_JOURNALS = 0.2  # Share of journals to draw from
MIN_COVERAGE = 5  # Minimum number of years to be covered in our time period
# Fields to include
config = ConfigParser()
config.optionxform = str
config.read("./definitions.cfg")
_fields = dict(config["field names"]).keys()


def read_file(fname):
    """Read journal files whose field is among our fields of interest."""
    field = splitext(basename(fname))[0]
    if field not in _fields:
        return pd.DataFrame()
    df = pd.read_csv(fname, sep=";", usecols=["Sourceid", "Title", "SJR"]).dropna()
    df["field"] = field
    return df


def write_panel(d, fname, digits=3, sort=False):
    """Convert a one-level nested dict into a DataFrame and save it."""
    df = pd.DataFrame(d).round(digits)
    if sort:
        df = df[sorted(df.columns)]
    df.to_csv(fname)


def write_stats(stat_dct):
    """Write out textfiles as "filename: content" pair."""
    for key, cont in stat_dct.items():
        fname = "{}/Statistics/{}.txt".format(OUTPUT_FOLDER, key)
        with open(fname, "w") as out:
            out.write("{:,}".format(int(cont)))


def main():
    # Get list of journals with sparse coverage
    cols = ["Source ID", "discontinued"]
    years = [str(y) for y in range(1997, 2019)]
    cols.extend(years)
    journals = pd.read_csv(JOURNAL_FILE, index_col=0, usecols=cols)
    journals["coverage"] = journals[years].fillna(0).sum(axis=1)
    drops = set(journals[journals["coverage"] <= MIN_COVERAGE].index)

    # Sample journals
    journals = pd.concat([read_file(f) for f in
                          sorted(glob(SOURCE_FOLDER + "*.csv"))])
    stats = {"N_of_journals_unique": journals["Sourceid"].nunique()}
    counts = {}
    useful = set()
    used = set()
    for field in journals["field"].unique():
        df = journals[journals["field"] == field]
        new = {"Total": df.shape[0]}
        num_journals = int(ceil(SHARE_JOURNALS*df.shape[0]/4))
        print(">>> Field {}: {} journals".format(field, num_journals*4))
        # Drop journals with too little coverage
        df = df[~df["Sourceid"].isin(drops)]
        useful.update(df["Sourceid"])
        new["Coverage > {} years".format(MIN_COVERAGE)] = df.shape[0]
        # Sample within octiles
        df['SJR'] = df['SJR'].str.replace(',', '.').astype(float)
        df['SJR'].iloc[df.shape[0]-1] = df['SJR'].iloc[df.shape[0]-1]*0.99
        df['octile'] = pd.qcut(df['SJR'], 8, labels=False, duplicates="drop")
        df['octile'] += 1
        out = pd.DataFrame()
        max_oct = df['octile'].max()
        for i in range(max_oct-3, max_oct+1):
            subset = df[df["octile"] == i]
            out = pd.concat([out, subset.sample(num_journals, random_state=0)])
        used.update(out["Sourceid"])
        # Write out
        fname = TARGET_FOLDER + field + ".csv"
        out = out.sort_values(['octile', 'Sourceid'], ascending=[False, True])
        out.to_csv(fname, index=False)
        new["Used"] = out.shape[0]
        counts[field] = new

    # Journal counts
    write_panel(counts, TARGET_FOLDER + "journal-counts.csv")
    stats["N_of_journals_useful"] = len(useful)
    stats["N_of_journals_used"] = len(used)
    write_stats(stats)


if __name__ == '__main__':
    main()
