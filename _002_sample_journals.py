#!/usr/bin/env python3
# Author:   Michael E. Rose <michael.ernst.rose@gmail.com>
"""Selects journals with sufficient coverage from the top four octiles
for each field.
"""

from configparser import ConfigParser
from collections import Counter
from glob import glob
from os.path import basename, splitext
from statistics import mean

import pandas as pd

SOURCE_FOLDER = "./000_journal_rankings/"
JOURNAL_FILE = "./001_journal_coverage/Scopus.csv"
TARGET_FOLDER = "./002_journal_samples/"
OUTPUT_FOLDER = "./990_output/"

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
    df = pd.read_csv(fname, sep=";", usecols=["Sourceid", "Title", "SJR"])
    df["field"] = field
    return df.dropna()


def write_stats(stat_dct):
    """Write out textfiles as "filename: content" pair."""
    for key, cont in stat_dct.items():
        fname = f"{OUTPUT_FOLDER}/Statistics/{key}.txt"
        with open(fname, "w") as out:
            out.write(f"{int(cont):,}")


def main():
    # Get list of journals with sparse coverage
    cols = ["Source ID", "discontinued"]
    years = [str(y) for y in range(1996, 2020)]
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
    used = []
    for field in journals["field"].unique():
        df = journals.loc[journals["field"] == field].copy()
        new = {"Total": df.shape[0]}
        print(f">>> Field {field}: {df.shape[0]} journals")
        # Drop journals with too little coverage
        df = df[~df["Sourceid"].isin(drops)]
        useful.update(df["Sourceid"])
        new[f"Coverage > {MIN_COVERAGE} years"] = df.shape[0]
        # Use top four octiles
        df['SJR'] = df['SJR'].str.replace(',', '.').astype(float)
        idx = df.shape[0]-1
        df.iloc[idx, df.columns.get_loc('SJR')] = df['SJR'].iloc[idx]*0.99
        df['octile'] = pd.qcut(df['SJR'], 8, labels=False, duplicates="drop")
        df['octile'] += 1
        out = df[df['octile'] > 4].copy()
        used.extend(out["Sourceid"])
        # Write out
        fname = TARGET_FOLDER + field + ".csv"
        out = out.sort_values(['octile', 'Sourceid'], ascending=[False, True])
        out.to_csv(fname, index=False, encoding="utf8")
        new["Used"] = out.shape[0]
        counts[field] = new.copy()

    # Journal analysis
    journal_fields = Counter(used).values()
    print(f">>> {len(journal_fields):,} different journals w/ "
          f"{mean(journal_fields):.2f} fields on average of which "
          f"{sum([x > 1 for x in journal_fields]):,} belong to more "
          f"than one field (max {max(journal_fields):,} fields)")
    out = pd.DataFrame(counts).round(3)
    out.to_csv(TARGET_FOLDER + "journal-counts.csv")
    stats["N_of_journals_useful"] = len(useful)
    stats["N_of_journals_used"] = len(journal_fields)
    write_stats(stats)


if __name__ == '__main__':
    main()
