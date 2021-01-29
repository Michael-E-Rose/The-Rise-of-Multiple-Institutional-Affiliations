#!/usr/bin/env python3
# Author:   Michael E. Rose <Michael.Ernst.Rose@gmail.com>
"""Ranks affiliations by occurrence and plots most frequent ones."""

from collections import Counter
from configparser import ConfigParser
from glob import glob
from itertools import combinations
from random import sample

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from pybliometrics.scopus import ContentAffiliationRetrieval
from pybliometrics.scopus.exception import Scopus404Error

from _100_parse_articles import START, END
from _105_aggregate_shares import print_progress

SOURCE_FOLDER = "./100_source_articles/"
TARGET_FOLDER = "./110_affiliation_rankings/"
OUTPUT_FOLDER = "./990_output/"

RANK_CUTOFF = 4  # Number of highest ranked affiliations for plot

matplotlib.use('Agg')
config = ConfigParser()
config.optionxform = str
config.read("./graphs.cfg")
plt.rcParams['font.family'] = config["styles"]["font"]
sns.set(style=config["styles"]["style"], font=config["styles"]["font"])


def format_time_axis(ax, _min, _max, labels=False, length=4):
    """Format axis with years such that the axis displays the end points."""
    from numpy import arange, append, ceil
    # Set endpoints
    ax.set_xlim(_min, _max)
    # Set locations
    start, end = ax.get_xlim()
    step = int(ceil((end-start)/length))
    ticks = arange(start, end, step)
    ticks = append(ticks, end)
    ticks = [int(n) for n in ticks]
    ax.xaxis.set_ticks(ticks)
    # Set labels
    if labels:
        labels = arange(_min.year, _max.year, step)
        labels = append(labels, _max.year)
        ax.set_xticklabels(labels)
    # Aesthetics
    ax.set_xlabel("")


def read_ma_source_file(f):
    """Read MA observations of source files."""
    cols = ['affiliations', "eid", "author"]
    df = pd.read_csv(f, encoding="utf8", usecols=cols)
    df["affiliations"] = df["affiliations"].str.split(";")
    return df[df["affiliations"].str.len() > 1]


def select_and_write(counted):
    """Select yearly top occurrences and write out ranking files."""
    top = set()
    for year, data in counted.items():
        df = pd.DataFrame.from_dict(data, orient="index")
        df.columns = ["occurrence"]
        df = df.sort_values("occurrence", ascending=False)
        top.update(df.head(RANK_CUTOFF).index)
        if isinstance(df.iloc[0].name, tuple):
            label = "pair"
            df.index = pd.MultiIndex.from_tuples(df.index)
            rename = {"level_0": "aff_id1", "level_1": "aff_id2"}
            df = (df.reset_index().rename(columns=rename)
                    .set_index(list(rename.values())))
        else:
            label = "indiv"
            df.index.name = "aff_id"
        fname = f"{TARGET_FOLDER}{label}_{year}.csv"
        df.to_csv(fname)
    return top


def main():
    # Count affiliations
    indiv_counts = {}
    pair_counts = {}
    totals = pd.Series(dtype="uint64", name="n_obs")
    print(">>> Counting affiliations from source files year-wise...")
    years = range(START, END+1)
    print_progress(0, len(years))
    for i, year in enumerate(years):
        # Read files by year
        files = glob(f"{SOURCE_FOLDER}*{year}*.csv")
        df = pd.concat([read_ma_source_file(f) for f in files])
        dup_cols = ["eid", "author"]
        df = df.drop_duplicates(subset=dup_cols).drop(dup_cols, axis=1)
        totals.loc[year] = df.shape[0]
        indiv_counts[year] = Counter([a for sl in df["affiliations"] for a in sl])
        pairs = [combinations(sl, 2) for sl in df["affiliations"]]
        pair_counts[year] = Counter([tuple(sorted(p)) for sl in pairs for p in sl])
        print_progress(i+1, len(years))
        del df

    # Write yearly rankings
    print(">>> Writing yearly rankings...")
    tops_indiv = select_and_write(indiv_counts)
    tops_pairs = select_and_write(pair_counts)
    for aff1, aff2 in tops_pairs:
        name1 = ContentAffiliationRetrieval(aff1).affiliation_name
        name2 = ContentAffiliationRetrieval(aff2).affiliation_name
        print(name1, "--", name2)

    # Collect data for plotting
    print(f">>> Plotting {len(tops_indiv)} affiliations")
    df = pd.DataFrame()
    all_afids = set()
    for year, data in indiv_counts.items():
        new = pd.DataFrame.from_dict(data, orient="index")
        all_afids.update(new.index)
        new["year"] = year
        df = df.append(new.reindex(tops_indiv))
    info = {aff_id: ContentAffiliationRetrieval(aff_id).affiliation_name
            for aff_id in tops_indiv}
    df["affiliation"] = pd.Series(info)
    df = (df.rename(columns={0: "occurrence"})
            .merge(totals, left_on="year", right_index=True))
    df["occurrence_norm"] = df["occurrence"]/df["n_obs"]*100

    # Make plot
    fig, ax = plt.subplots(figsize=(9, 9))
    sns.lineplot(x="year", y="occurrence_norm", hue="affiliation",
                 data=df, ax=ax, style=None, palette="colorblind")
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles=handles[1:], labels=labels[1:])
    ylabel = "Share of affiliation's occurrence in multiple "\
             "affiliations author-article observations"
    ax.set(ylabel=ylabel)
    ax.set_ylim(bottom=0)
    format_time_axis(ax, df["year"].min(), df["year"].max())
    fname = OUTPUT_FOLDER + "Figures/top-affs.pdf"
    fig.savefig(fname, bbox_inches="tight")
    plt.close(fig)

    # Count affiliations by type
    nonorg_afids = {a for a in all_afids if a.startswith("1")}
    n_nonorg = len(nonorg_afids)
    print(f">>> {len(all_afids) - n_nonorg:,} org affiliation IDs")
    print(f">>> {n_nonorg:,} org affiliation IDs")

    # Randomly analyze some nonorg affiliation IDs
    print(">>> Random non-org affiliation names")
    for aff_id in sample(tuple(nonorg_afids), 100):
        try:
            aff = ContentAffiliationRetrieval(aff_id, refresh=20)
            print(aff.affiliation_name)
        except Scopus404Error:
            print("doesn't exist")


if __name__ == '__main__':
    main()
