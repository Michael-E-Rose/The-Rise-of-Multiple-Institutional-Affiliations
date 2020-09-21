#!/usr/bin/env python3
# Author:   Michael E. Rose <Michael.Ernst.Rose@gmail.com>
"""Ranks affiliations by occurrence and plots most frequent ones."""

from collections import defaultdict, Counter
from configparser import ConfigParser
from glob import glob
from itertools import combinations

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from pybliometrics.scopus import ContentAffiliationRetrieval

from _105_aggregate_shares import print_progress
from _910_plot_multiaff_shares import format_time_axis

SOURCE_FOLDER = "./100_source_articles/"
TARGET_FOLDER = "./110_affiliation_rankings/"
OUTPUT_FOLDER = "./990_output/"

RANK_CUTOFF = 4  # Number of highest ranked affiliations for plot

config = ConfigParser()
config.optionxform = str
config.read("./graphs.cfg")
plt.rcParams['font.family'] = config["styles"]["font"]
sns.set(style=config["styles"]["style"], font=config["styles"]["font"])


def select_and_write(counted):
    """Select yearly top occurrences and write out ranking files."""
    top = set()
    for year, data in counted.items():
        df = pd.DataFrame.from_dict(data, orient="index")
        df.columns = ["occurrence"]
        df = df.sort_values("occurrence", ascending=False)
        top.update(df.head(RANK_CUTOFF).index)
        label = "indiv"
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
    indiv_counts = defaultdict(lambda: Counter())
    pair_counts = defaultdict(lambda: Counter())
    totals = pd.Series(dtype="uint64")
    files = glob(SOURCE_FOLDER + '*.csv')
    total = len(files)
    print(">>> Reading source files...")
    print_progress(0, total)
    cols = ["year", "affiliations", "multiaff"]
    for idx, f in enumerate(files):
        # Read file
        data = pd.read_csv(f, usecols=cols)
        data = data.dropna().drop("multiaff", axis=1)
        totals = totals.append(data["year"].value_counts())
        data["affiliations"] = data["affiliations"].str.split(";")
        for y in data["year"].unique():
            subset = data[data["year"] == y]
            solo = [a for sl in subset["affiliations"] for a in sl]
            indiv_counts[y].update(Counter(solo))
            pairs = [combinations(sl, 2) for sl in subset["affiliations"]]
            c = Counter([tuple(sorted(p)) for sl in pairs for p in sl])
            pair_counts[y].update(c)
        print_progress(idx+1, total)
    totals.name = "n_obs"
    totals.index.name = "year"
    n_obs = totals.reset_index().groupby("year").sum()
    del totals

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
    for year, data in indiv_counts.items():
        new = pd.DataFrame.from_dict(data, orient="index")
        new["year"] = year
        df = df.append(new.reindex(tops_indiv))
    info = {aff_id: ContentAffiliationRetrieval(aff_id).affiliation_name
            for aff_id in tops_indiv}
    df["affiliation"] = pd.Series(info)
    df = (df.rename(columns={0: "occurrence"})
            .merge(n_obs, left_on="year", right_index=True))
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


if __name__ == '__main__':
    main()
