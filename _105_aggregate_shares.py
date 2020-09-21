#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Authors:   Michael E. Rose <michael.ernst.rose@gmail.com>
"""Analyzes and plots shares of authors with multiple affiliations in
various aggregations following the s bar-notation.
"""

from configparser import ConfigParser
from glob import glob

import pandas as pd

from _002_sample_journals import write_stats
from _100_parse_articles import print_progress

SOURCE_FOLDER = "./100_source_articles/"
JOURNAL_FOLDER = "./002_journal_samples/"
TARGET_FOLDER = "./105_multiaff_shares/"
OUTPUT_FOLDER = "./990_output/"

config = ConfigParser()
config.optionxform = str
config.read("./definitions.cfg")
_asjc_map = dict(config["field names"])
_groups = dict(config["country groups"])


def aggregate(df, columns, aggs={"multiaff": ["size", sum], "foreignaff": sum}):
    """Compute multiaff share for unique observations via groupby."""
    df = (df.drop_duplicates(["author", "year"] + columns)
            .groupby(["year"] + columns).agg(aggs)
            .reset_index())
    df.columns = [''.join(col) for col in df.columns]
    df["multiaffshare"] = df["multiaffsum"]/df["multiaffsize"]*100
    df["foreignaffshare"] = df["foreignaffsum"]/df["multiaffsum"]*100
    return df.drop(["multiaffsum", "foreignaffsum"], axis=1)


def make_shares_table(df, fname, col_map=None, byvar="multiaff", precision=1,
                      means=False, growth=False):
    """Create and write out Latex-formated table on shares by
    field over time.
    """
    grouped = df.groupby(["field", "year"])[byvar]
    totals = grouped.count()
    temp = grouped.sum().to_frame()
    temp["share"] = (temp[byvar]/totals)*100
    temp = (temp.reset_index()
                .drop(byvar, axis=1)
                .pivot(columns="field", values="share", index="year"))
    overall = df.groupby(["year"])[byvar].agg(["sum", "count"])
    temp["All"] = overall["sum"]/overall["count"]*100
    temp.columns = [col_map.get(c, c) for c in temp.columns]
    if means:
        means = temp.mean(axis=0)
        temp.loc["\\midrule Yearly Average"] = means
    if growth:
        def compute_growth(s):
            """Compute overall growth rate."""
            years = [y for y in s.index if isinstance(y, int)]
            _max = max(years)
            _min = min(years)
            return (s[_max]-s[_min])/s[_min] * 100
        temp.loc["Overall Growth"] = temp.apply(compute_growth, axis=0)
    temp.index.name = "Year"
    temp.round(1).to_latex(fname, escape=False)


def read_source_files(cols, drop_duplicates=None, **pd_kwds):
    """Read files from SOURCE_FOLDER."""
    from glob import glob
    from os.path import basename
    df = pd.DataFrame()
    files = list(glob(SOURCE_FOLDER + "*.csv"))
    total = len(files)
    print(">>> Reading files...")
    print_progress(0, total)
    for idx, f in enumerate(files):
        new = pd.read_csv(f, usecols=cols, **pd_kwds)
        if drop_duplicates:
            new = new.drop_duplicates(subset=drop_duplicates)
        field = basename(f).split("_")[1].split("-")[0]
        new["field"] = field
        df = df.append(new)
        print_progress(idx+1, total)
    print(">>> Continuing operation...")
    return df


def main():
    # Read articles list
    cols = ["author_count", "country", "multiaff", "foreign_multiaff", "year",
            "source_id", "eid", "author"]
    dtypes = {"author_count": "uint8", "multiaff": "float32", "year": "uint16",
              "author": "uint64", "foreign_multiaff": "float32"}
    df = read_source_files(cols, dtype=dtypes)
    stats = {"N_of_authors_unique": df["author"].nunique()}
    df = df.rename(columns={"foreign_multiaff": "foreignaff"})
    for col in ("multiaff", "foreignaff"):
        df[col] = df[col].fillna(0).astype("uint32")
    df = df.sort_values("multiaff", ascending=False)
    df["country"] = df["country"].astype("category")
    df["source_id"] = df["source_id"].fillna(method="ffill").astype("uint64")

    # Create table on share of MA articles by field over time
    temp = df.sort_values("multiaff", ascending=False).drop_duplicates("eid")
    fname = OUTPUT_FOLDER + "Tables/multiaff_articles_share-field.tex"
    make_shares_table(temp, fname, col_map=_asjc_map)
    del temp

    # Create table on share of MA authors by field and year
    fname = OUTPUT_FOLDER + "/Tables/multiaff_authors_share-field.tex"
    make_shares_table(df, fname, col_map=_asjc_map, means=True, growth=True)

    # Read journal quality files
    jour_files = [f for f in glob(JOURNAL_FOLDER + "*.csv") if "counts" not in f]
    jour = pd.concat([pd.read_csv(f, usecols=["Sourceid", "octile"]) for f in
                      jour_files])
    jour = (jour.sort_values("octile", ascending=False)
                .drop_duplicates(["Sourceid"]))
    quality = (df.merge(jour, "inner", left_on="source_id", right_on="Sourceid")
                 .drop(["field", "Sourceid", "source_id", "country"], axis=1))

    # Compute share of articles w/ MA authors
    paper = (quality.groupby(["year", "eid"])["author_count", "multiaff"].max()
                    .reset_index().drop("eid", axis=1))
    df = df.drop("author_count", axis=1)
    quality = quality.drop(["eid", "author_count"], axis=1)
    corr = paper[["author_count", "multiaff"]].corr().iloc[1, 0]
    print(">>> Correlation group size and MA author incidence: {:.2}".format(corr))
    ma_share = paper["multiaff"].sum()/paper.shape[0]
    print(">>> Share articles with MA author(s): {:.2%}".format(ma_share))
    totals = paper["year"].value_counts()
    totals.name = "total"
    counts = (paper.groupby("year")[["multiaff"]].sum()
                   .merge(totals, "left", left_index=True,
                          right_index=True))
    counts["multiaff_share"] = counts["multiaff"]/counts["total"]*100
    print(counts["multiaff_share"].round(4))
    yearly = (df.groupby(["year", "field", "eid"])["multiaff"].max()
                .reset_index())
    yearly = (yearly.groupby(["year", "field"])["multiaff"].agg(["sum", "size"])
                    .reset_index())
    yearly["share"] = yearly["sum"]/yearly["size"]*100
    out = yearly.pivot(index='year', columns='field', values='share')
    out.columns = [_asjc_map[c] for c in out.columns]
    out["total"] = counts["multiaff_share"]
    del counts
    out.round(2).to_csv("ma_paper_shares.csv")

    # Observation is author-country-year
    bycountry = aggregate(df, ["country"])
    bycountry.to_csv(TARGET_FOLDER + "bycountry.csv", index=False)
    stats["N_of_authorcountryyear"] = bycountry["multiaffsize"].sum()
    del bycountry

    # Observation is author-countryfield-year
    df["field"] = df["field"].replace(_asjc_map)
    bycountryfield = aggregate(df, ["country", "field"])
    bycountryfield.to_csv(TARGET_FOLDER + "bycountryfield.csv", index=False)
    stats["N_of_authorcountryfieldyear"] = bycountryfield["multiaffsize"].sum()
    del bycountryfield

    # Prepare author-octile-year
    quality = quality.sort_values(["octile", "multiaff"], ascending=False)
    byquality = aggregate(quality, ["octile"])
    del quality
    oct_labels = {8: "Top octile", 7: "Second octile", 6: "Third octile",
                  5: "Fourth octile"}
    byquality["octile"] = byquality["octile"].replace(oct_labels)
    byquality = byquality.rename(columns={"octile": "Journal quality group"})
    byquality.to_csv(TARGET_FOLDER + "byquality.csv", index=False)
    stats["N_of_authoroctileyear"] = byquality["multiaffsize"].sum()
    del byquality

    # Observation is author-field-year
    byfield = aggregate(df, ["field"])
    byfield = byfield.sort_values("field")
    byfield.to_csv(TARGET_FOLDER + "byfield.csv", index=False)
    stats["N_of_authorfieldyear"] = byfield["multiaffsize"].sum()
    del byfield

    # Write statistics
    print(">>> No. of observations:", stats)
    write_stats(stats)


if __name__ == '__main__':
    main()
