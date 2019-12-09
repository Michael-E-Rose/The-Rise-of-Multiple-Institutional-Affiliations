#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Authors:   Michael E. Rose <michael.ernst.rose@gmail.com>
#            Kaan Uçtum
"""Describes the frequency of different multi-affiliation combinations
over time via graphs and tables.
"""

from configparser import ConfigParser

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from _218_analyze_solo_papers import format_time_axis, read_source_files

SOURCE_FOLDER = "./100_source_articles/"
OUTPUT_FOLDER = "./990_output/"
# Combinations occuring less than x% will be grouped as Other
THRESHOLD_ALL = 0.1  # As share of all author-publications
THRESHOLD_MA = 3  # As share of author-publications with multiple affiliations

config = ConfigParser()
config.optionxform = str
config.read("./definitions.cfg")
asjc_map = dict(config["field names"])
config.read("./graphs.cfg")
plt.rcParams['font.family'] = config["styles"]["font"]
sns.set(style=config["styles"]["style"], font=config["styles"]["font"])
pd.plotting.register_matplotlib_converters()

_type_names = {"univ": "Univ.", "resi": "Res. Inst.", "comp": "Company",
               "hosp": "Hospital", "govt": "Governmental",
               "ngov": "Non-Gov."}


def clean_inst_types(type_str):
    """Reduce multiple combinations of the same type to a dual combination."""
    if "-" not in type_str:
        return type_str
    types = set(type_str.split("-"))
    if len(types) == 1:
        t = types.pop()
        return "{}-{}".format(t, t)
    else:
        return "-".join(sorted(types, reverse=True))


def custom_formatter(x, na_rep="<{}".format(THRESHOLD_MA)):
    """Format number if it's not NaN, `na_rep` otherwise."""
    from math import isnan
    if isnan(x):
        return na_rep
    else:
        return '%.1f' % x


def grouping_with_shares(df, first, other, aggs):
    """Group DataFrame by `first` and `other`, compute aggregations by multiaff
    and compute shares by group.
    """
    total = df[first].value_counts()
    out = df.groupby([first, other], as_index=False)["multiaff"].agg(aggs)
    out = out.set_index(first)
    out["total"] = total
    out["share"] = out["n"]/out["total"]*100
    return out.reset_index()


def make_comparison_barplot(solo, multi, fname, figsize=(15, 10)):
    """Plot two panels, one with multi-affiliation affiliation types and one
    with solo-affiliation affilation types.
    """
    fig, axes = plt.subplots(2, 1, figsize=figsize, sharex=True)
    multi.plot.bar(stacked=True, ax=axes[0])
    solo.plot.bar(stacked=True, ax=axes[1], rot=0, colormap="gist_gray",
                  edgecolor="black")
    # Aesthetics
    for ax in axes:
        ax.set_ylabel("Share in all author-article observations (in %)")
        ax.legend(title="")
    axes[0].legend(ncol=3)
    axes[1].set_xlabel("")
    # Save
    fig.savefig(fname, bbox_inches="tight")
    plt.close(fig)


def make_barplot(multi, fname, figsize=(12, 8)):
    """Make barplot of affiliation type combinations."""
    fig, ax = plt.subplots(figsize=figsize)
    multi.index = multi.index.astype(str)
    multi.plot.bar(stacked=True, ax=ax, rot=0)
    # Aesthetics
    ax.set(xlabel="", ylabel="Share in all author-article observations (in %)",
           ylim=(0, 13))
    ax.legend(ncol=2)
    # Save
    fig.savefig(fname, bbox_inches="tight")
    plt.close(fig)


def make_growth_table(df, fname):
    """Create and write out Latex-formated table on MA shares."""
    def compute_growth(s):
        """Compute overall growth rate."""
        return round((s[2018]-s[1996])/s[1996] * 100, 1)
    df.columns = [asjc_map.get(c, c) for c in df.columns]
    means = df.mean(axis=0)
    df.loc["Overall Growth"] = df.apply(compute_growth, axis=0)
    df.loc["Average"] = means
    df.round(1).to_latex(fname)


def prepare_subset(df):
    """Compute shares, drop rare combinations and pivot DataFrame."""
    # Compute shares
    df = df.groupby(["Year", "inst_types"])["count"].sum().reset_index()
    totals = df.groupby("Year")["count"].transform('sum')
    df["share"] = df["count"]/totals*100
    # Combine rare combinations
    df.loc[df["share"] < THRESHOLD_MA, "inst_types"] = "Other"
    # Pivot
    df = df.groupby(["inst_types", "Year"])["share"].sum().reset_index()
    df["Year"] = pd.to_datetime(df["Year"], format='%Y')
    return df.pivot(index='Year', columns='inst_types', values='share')


def sort_df(df, year=2018, ascending=False):
    """Sort a DataFrame by a specific row."""
    order = list(df.T.sort_values(year, ascending=ascending).index)
    df.columns = pd.CategoricalIndex(df.columns.values, ordered=True,
                                     categories=order)
    return df.sort_index(axis=1)


def main():
    # Read in
    cols = ["year", "inst_types", "multiaff", "author"]
    df = read_source_files(cols, drop_duplicates=False)
    df["multiaff"] = df["multiaff"].fillna(0)
    df = (df.sort_values("multiaff", ascending=False)
            .drop_duplicates(subset=["author", "year"]))
    df["inst_types"] = df["inst_types"].apply(clean_inst_types)
    df = df.rename(columns={"year": "Year"})

    # Temporary correction
    mask = (df["inst_types"] == "resi") & (df["multiaff"] == 1)
    df.loc[mask, "inst_types"] = "univ-resi"

    # Table on combination percentages by field and year
    total = df.groupby(["field", "Year"])["author"].count()
    df_field = df.groupby(["field", "Year"])["multiaff"].sum().to_frame()
    df_field["share"] = (df_field["multiaff"]/total)*100
    df_field = (df_field.reset_index()
                        .drop("multiaff", axis=1)
                        .pivot(columns="field", values="share", index="Year"))
    fname = OUTPUT_FOLDER + "/Tables/multiaff_share-ma_fields-field.tex"
    make_growth_table(df_field, fname)

    # Table on averaged MA combination percentages by field and type
    multi = df[df["multiaff"] == 1].copy()
    aggs = {"multiaff": max, "n": "count"}
    df_type = grouping_with_shares(multi, 'field', "inst_types", aggs)
    df_type = (df_type.pivot(columns="field", values="share", index="inst_types")
                      .sort_values("12")
                      .fillna(0).round(1))
    small_values = df_type < THRESHOLD_MA
    small_combs = small_values.sum(axis=1) == df_type.shape[1]
    combs_always_small = df_type.index[small_combs]
    repl = {i: "Other" for i in combs_always_small}
    df_type = df_type.reset_index("inst_types")
    df_type["inst_types"] = df_type["inst_types"].replace(repl)
    df_type = (df_type.groupby("inst_types").sum()
                      .astype(str)
                      .where(~small_values, other="<3"))
    df_type = df_type.reindex(index=df_type.index[::-1])
    df_type.columns = [asjc_map.get(c, c) for c in df_type.columns]
    for val, repl in _type_names.items():
        df_type.index = df_type.index.str.replace(val, repl)
    fname = OUTPUT_FOLDER + "/Tables/multiaff_share-ma_combinations-field.tex"
    df_type.to_latex(fname, index_names=False)

    # Affiliation type combination plots
    df_comb = grouping_with_shares(df.copy(), "Year", 'inst_types', aggs)
    df_comb.loc[df_comb["share"] < THRESHOLD_ALL, "inst_types"] = "Other"
    df_comb = (df_comb.groupby(["Year", "inst_types", "multiaff"])
                      .sum().reset_index())
    df_comb["share"] = df_comb["n"]/df_comb["total"]*100
    df_comb = df_comb.sort_values("share")
    for val, repl in _type_names.items():
        df_comb["inst_types"] = df_comb["inst_types"].str.replace(val, repl)
    comb_multi = df_comb[df_comb["multiaff"] == 1]
    pivot_kwds = {"columns": "inst_types", "values": "share", "index": "Year"}
    comb_multi = sort_df(comb_multi.pivot(**pivot_kwds))
    fname = OUTPUT_FOLDER + "Figures/combinations_share-total_bars.pdf"
    make_barplot(comb_multi, fname)
    comb_solo = df_comb[df_comb["multiaff"] == 0]
    comb_solo = sort_df(comb_solo.pivot(**pivot_kwds))
    fname = OUTPUT_FOLDER + "Figures/combinations_share-total_bars-comparison.pdf"
    make_comparison_barplot(comb_solo, comb_multi, fname)

    # Table for affiliation type combinations
    df_ma = (multi.drop("multiaff", axis=1).copy()
                  .groupby(["Year", "inst_types", "field"]).size()
                  .reset_index()
                  .rename(columns={0: "count"}))
    for val, repl in _type_names.items():
        df_ma["inst_types"] = df_ma["inst_types"].str.replace(val, repl)
    df_ma = df_ma.groupby(["Year", "inst_types"])["count"].sum().reset_index()
    df_ma = prepare_subset(df_ma)
    df_ma.index = df_ma.reset_index()["Year"].dt.year
    order = list(df_ma.T.sort_values(2018, ascending=False).index)
    order.remove("Other")
    order.append("Other")
    df_ma.columns.name = ""
    fname = OUTPUT_FOLDER + "Tables/multiaff_share-ma_combinations-year.tex"
    df_ma[order].to_latex(fname, float_format=custom_formatter)


if __name__ == '__main__':
    main()
