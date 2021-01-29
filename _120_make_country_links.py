#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Authors:   Michael E. Rose <michael.ernst.rose@gmail.com>
"""Creates matrices showing country linkages."""

from collections import defaultdict
from glob import glob

import pandas as pd

from _100_parse_articles import START, END

SOURCE_FOLDER = "./100_source_articles/"
TARGET_FOLDER = "./120_country_matrices/"
COUNTRY_WHITELIST = "./098_country_whitelist/oecd_others.csv"


def read_ma_source_file(f):
    """Read MA observations of source files."""
    cols = ['affiliations', 'countries', "author"]
    df = pd.read_csv(f, encoding="utf8", usecols=cols)
    df["ma"] = (df["affiliations"].str.find(";") != -1).astype("uint8")
    df = (df.drop("affiliations", axis=1)
            .sort_values("ma", ascending=False))
    return df.drop_duplicates("author")


def main():
    whitelist = set(pd.read_csv(COUNTRY_WHITELIST)['country'])
    foreign_share = pd.DataFrame()
    print(">>> Now working on")
    for year in range(START, END+1):
        print(f"... {year}")
        # Read files for current year and deduplicate
        files = glob(f"{SOURCE_FOLDER}*{year}*.csv")
        df = pd.concat([read_ma_source_file(f) for f in files])
        df = (df.sort_values("ma", ascending=False)
                .drop_duplicates("author")
                .drop("ma", axis=1))

        # Count combinations
        counts = (df["countries"].value_counts().to_frame(name="frequency")
                    .reset_index().rename(columns={"index": "countries"}))
        del df
        counts["countries"] = counts["countries"].str.split("-")

        # Build matrix from counts
        matrix = defaultdict(lambda: defaultdict(lambda: 0))
        for i, row in counts.iterrows():
            try:
                source, target = row["countries"][:2]
            except ValueError:
                continue  # Only one country given
            if target not in whitelist:
                target = "Other"
            matrix[source][target] += row["frequency"]

        # Write out
        matrix = pd.DataFrame(matrix)
        matrix = matrix[sorted(matrix.columns)].sort_index()
        matrix.round(3).to_csv(f"{TARGET_FOLDER}{year}.csv", encoding="utf8")

        # Compute foreign affiliation intensity
        total = matrix.sum(axis=0)
        matrix = matrix.drop("Other")
        foreign_share[year] = 1 - matrix.values.diagonal()/total

    # Write out
    foreign_share.to_csv(TARGET_FOLDER + "foreign-share.csv", encoding="utf8",
                         index_label="country")


if __name__ == '__main__':
    main()
