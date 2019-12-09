#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Authors:   Michael E. Rose <michael.ernst.rose@gmail.com>
#            Kaan Uçtum
"""Analyzes and plots shares of authors with multiple affiliations or with
foreign MA in various aggregations following the s bar-notation.
"""

from configparser import ConfigParser
from glob import glob
from math import ceil

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

SOURCE_FOLDER = "./100_source_articles/"
JOURNAL_FOLDER = "./002_journal_samples/"
TARGET_FILE = "./105_multiaff_shares/shares.csv"
OUTPUT_FOLDER = "./990_output/"

pd.plotting.register_matplotlib_converters()

config = ConfigParser()
config.optionxform = str
config.read("./graphs.cfg")
_colors = dict(config["colors"])
_colors["World"] = _colors["Rest of World"]
plt.rcParams['font.family'] = config["styles"]["font"]
sns.set(style=config["styles"]["style"], font=config["styles"]["font"])
config.read("./definitions.cfg")
_asjc_map = dict(config["field names"])
_groups = dict(config["country groups"])

COUNTRIES_U = ["United States", "Russia", "China", "Israel", "Canada",
               "Europe", "World"]
COUNTRIES_L = ["Germany", "France", "Italy", "United Kingdom", "Spain",
               "Scandinavia w/o Norway", "Norway", "Netherlands", "Switzerland",
               "Belgium"]


def aggregate(df):
    """Aggregate DataFrame as preparation and clean column names."""
    aggs = {"multiaff": ["size", sum], "foreign_multiaff": [sum]}
    df = df.groupby(["country", "field", "year"]).agg(aggs).reset_index()
    df.columns = ["country", "field", "year", "total", "multiaff", "foreignaff"]
    df["field"] = df["field"].replace(_asjc_map)
    return df


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


def make_comparison_lineplot(bycountry, byfield, byquality, fname,
                             figsize=(9, 9), x="year",
                             y="Share of authors with multiple affiliations (in %)"):
    """Make graph with three panels:
    1. Share of MA authors by field
    2. Share of MA authors by journal octile
    3. Share of MA authors for selected countries
    4. Share of MA authors for European countries
    """
    byfield_var = "field"
    byquality_var = "Journal quality group"
    bycountry_var = "group"
    # Start plot
    fig, axes = plt.subplots(2, 2, figsize=figsize, sharex=True, sharey=True)
    fig.tight_layout()
    # Linestyles
    _linestyle = {c: "" for c in bycountry["country"].unique()}
    _linestyle["Europe"] = (5, 1)  # long dashes
    _linestyle["Scandinavia w/o Norway"] = (3, 1)  # short dashes
    _linestyle["World"] = (1, 1)  # dots
    # Plot panels
    sns.lineplot(x=x, y=y, hue=byfield_var, data=byfield, ax=axes[0, 0],
                 style=None, ci=None)
    sns.lineplot(x=x, y=y, data=byquality, style=byquality_var, ax=axes[0, 1],
                 ci=None)
    for idx, country_list in enumerate((COUNTRIES_U, COUNTRIES_L)):
        mask = bycountry["country"].isin(country_list)
        bycountry.loc[mask, bycountry_var] = bycountry["country"]
        subset = bycountry[bycountry[bycountry_var].isin(country_list)]
        if idx == 0:  # Add world average
            world = bycountry.copy()
            world[bycountry_var] = "World"
            subset = subset.append(world, sort=False)
        sns.lineplot(x=x, y=y, data=subset, ax=axes[1, idx], style=bycountry_var,
                     hue=bycountry_var, palette=_colors, dashes=_linestyle)
    # Format legend
    for axarray in axes:
        for ax in axarray:
            handles, labels = ax.get_legend_handles_labels()
            if labels[0] != byquality_var:
                title = None
            else:
                title = labels[0]
                order = [0, 4, 2, 3, 1]
                handles = [handles[i] for i in order]
                labels = [labels[i] for i in order]
            ncols = 1
            if "Medicine" in labels:  # Two-column legend
                ncols = 2
            ax.legend(handles=handles[1:], labels=labels[1:], loc="upper left",
                      ncol=ncols, title=title)
    # Aesthetics
    axes[1, 0].set_ylim(top=ceil(bycountry[y].max()), bottom=0)
    format_time_axis(axes[1, 0], subset[x].min(), subset[x].max())
    format_time_axis(axes[1, 1], subset[x].min(), subset[x].max())
    # Save
    fig.savefig(fname, bbox_inches="tight")
    plt.close(fig)


def matrix_lineplot(df, fname, col="country", x="year",
                    y="Share of authors with multiple affiliations (in %)"):
    """Create and save lineplots in a matrix."""
    # Plot
    g = sns.FacetGrid(df, col=col, col_wrap=5, aspect=1.25)
    g.map(sns.lineplot, x, y, ci=None)
    _min = df[x].min()
    _max = df[x].max()
    for ax in g.axes.flat:
        # Extract country from title
        title = ax.get_title()
        country = title.split("= ")[-1]
        ax.set_title(country)
        # Aesthetics
        format_time_axis(ax, _min, _max)
        ax.set_ylim(bottom=0)
    # Save
    plt.savefig(fname, bbox_inches="tight", width=20)
    plt.close()


def make_simple_lineplot(df, fname, hue, x="year", size=(10, 5),
                         y="Share of authors with multiple affiliations (in %)"):
    """Create and save simple lineplot with different hue."""
    # Plot
    fig, ax = plt.subplots(figsize=size)
    if hue:
        df = df.sort_values(hue)
    sns.lineplot(x=x, y=y, hue=hue, data=df, ax=ax, style=None, ci=None)
    # Aesthetics
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles=handles[1:], labels=labels[1:], ncol=2)
    format_time_axis(ax, df[x].min(), df[x].max())
    ax.set_ylim(bottom=0)
    # Save
    fig.savefig(fname, bbox_inches="tight")
    plt.close(fig)


def read_source_files(cols, drop_duplicates=True):
    """Read files from SOURCE_FOLDER."""
    from glob import glob
    from os.path import basename
    df = pd.DataFrame()
    for f in glob(SOURCE_FOLDER + "*.csv"):
        new = pd.read_csv(f, usecols=cols)
        if drop_duplicates:
            new = new.drop_duplicates(subset="eid")
        field = basename(f).split("_")[1].split("-")[0]
        new["field"] = field
        df = df.append(new)
    return df


def main():
    # Read articles list
    cols = ["author_count", "country", "multiaff", "foreign_multiaff", "year",
            "source_id", "eid"]
    df = read_source_files(cols, drop_duplicates=False)
    for col in ("multiaff", "foreign_multiaff"):
        df[col] = df[col].fillna(0)

    # Read journal quality files
    jour_files = [f for f in glob(JOURNAL_FOLDER + "*.csv") if not "counts" in f]
    jour = pd.concat([pd.read_csv(f, usecols=["Sourceid", "octile"]) for f in
                      jour_files])
    jour = (jour.sort_values("octile", ascending=False)
                .drop_duplicates(["Sourceid"]))
    quality = df.merge(jour, "inner", left_on="source_id", right_on="Sourceid")
    quality = (quality.drop(["field", "Sourceid", "source_id"], axis=1)
                      .drop_duplicates("eid")
                      .rename(columns={"foreign_multiaff": "foreignaff"}))

    # Compute share of articles w/ MA authors
    paper = quality.groupby(["year", "eid"])["author_count", "multiaff", "foreignaff"].max()
    paper = paper.reset_index().drop("eid", axis=1)
    corr = paper[["author_count", "multiaff"]].corr().iloc[1, 0]
    print(">>> Correlation group size and MA author incidence: {:.2}".format(corr))
    ma_share = paper["multiaff"].sum()/paper.shape[0]
    print(">>> Share articles with MA author(s): {:.2f}".format(ma_share*100))
    totals = paper["year"].value_counts()
    totals.name = "total"
    counts = (paper.groupby("year")["multiaff", "foreignaff"].sum()
                   .merge(totals, "left", left_index=True, right_index=True))
    counts["multiaff_share"] = counts["multiaff"]/counts["total"]
    counts["foreignaff_share"] = counts["foreignaff"]/counts["multiaff"]
    print(counts[["multiaff_share", "foreignaff_share"]].round(4)*100)

    # Compute share of MA authors by year-field-country
    df = aggregate(df.drop("author_count", axis=1))
    df.to_csv(TARGET_FILE, index=False)

    # Plots for share of author-field-year with Multiaff and Foreignaff
    quality["total"] = 1
    octiles = {8: "Top octile", 7: "Second octile", 6: "Third octile",
               5: "Fourth octile"}
    quality["octile"] = quality["octile"].replace(octiles)
    quality = (quality.drop(["eid", "author_count", "country"], axis=1)
                      .rename(columns={"octile": "Journal quality group"})
                      .groupby(["year", "Journal quality group"]))
    path = OUTPUT_FOLDER + "Figures/"
    for nom, denom in zip(("multiaff", "foreignaff"), ("total", "multiaff")):
        byquality = quality[nom, denom].sum().reset_index()
        share = byquality[nom]/byquality[denom]*100
        byquality["Share of authors with multiple affiliations (in %)"] = share
        # Observation is country-field combination
        share = df[nom]/df[denom]*100
        df["Share of authors with multiple affiliations (in %)"] = share
        fname = "{}{}_share_fields-countryfield.pdf".format(path, nom)
        make_simple_lineplot(df, hue="field", fname=fname)
        fname = "{}{}_share_countriesmatrix-countryfield.pdf".format(path, nom)
        matrix_lineplot(df, fname=fname)
        # Observation is field
        byfield = (df.groupby(["field", "year"]).sum()
                     .reset_index().sort_values("field"))
        share = byfield[nom]/byfield[denom]*100
        byfield["Share of authors with multiple affiliations (in %)"] = share
        fname = "{}{}_share_fields-field.pdf".format(path, nom)
        make_simple_lineplot(byfield, hue="field", fname=fname)
        # Observation is country
        bycountry = df.groupby(["country", "year"]).sum().reset_index()
        share = bycountry[nom]/bycountry[denom]*100
        bycountry["Share of authors with multiple affiliations (in %)"] = share
        fname = "{}{}_share_countriesmatrix-country.pdf".format(path, nom)
        matrix_lineplot(bycountry, fname=fname)
        fname = "{}{}_share_countries-country.pdf".format(path, nom)
        make_simple_lineplot(bycountry, hue=None, fname=fname)
        # Combination of country and field
        fname = "{}{}_share_global.pdf".format(path, nom)
        bycountry["group"] = bycountry["country"].replace(_groups)
        bycountry = bycountry.sort_values(["group", "country"])
        make_comparison_lineplot(bycountry, byfield, byquality, fname)


if __name__ == '__main__':
    main()
