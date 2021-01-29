#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Authors:   Michael E. Rose <michael.ernst.rose@gmail.com>
#            Kaan Uçtum
"""Describes the frequency of different multi-affiliation combinations
over time via graphs and tables.
"""

from configparser import ConfigParser

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from numpy import nan

from _105_aggregate_shares import read_source_files
from _110_rank_affiliations import format_time_axis
from _910_analyze_multiaff_shares import add_figure_letter

SOURCE_FOLDER = "./100_source_articles/"
OUTPUT_FOLDER = "./990_output/"
# Combinations occurring less than x% will be grouped as Other
THRESHOLD_ALL = 0.5  # As share of all author-publications
THRESHOLD_MA = 3  # As share of author-publications with multiple affiliations

matplotlib.use('Agg')
config = ConfigParser()
config.optionxform = str
config.read("./definitions.cfg")
asjc_map = {int(k): v for k, v in dict(config["field names"]).items()}
config.read("./graphs.cfg")
_colors = dict(config["Combinations"])
plt.rcParams['font.family'] = config["styles"]["font"]
sns.set(style=config["styles"]["style"], font=config["styles"]["font"])
pd.plotting.register_matplotlib_converters()


def aggregate_shares(df):
    """Compute share types by year and field."""
    return (df.groupby(["Year", "types", "field"]).size()
              .reset_index()
              .rename(columns={0: "count"}))


def clean_types(type_str):
    """Reduce multiple combinations of the same type to a dual combination."""
    names = {"univ": "Univ.", "resi": "Res. Inst.", "comp": "Company",
             "hosp": "Hospital", "govt": "Gov.", "ngov": "Non-Gov.",
             "?": "Unknown"}
    if "-" not in type_str:
        return names.get(type_str, type_str)
    types = {names.get(t, t) for t in set(type_str.split("-"))}
    if len(types) == 1:
        t = types.pop()
        if t == "Unknown":
            return "Other"
        return f"{t}-{t}"
    else:
        types = sorted(types, reverse=True)
        if types[0] == "Unknown":
            types.pop(0)
            types.append("Unknown")
        return "-".join(types)


def collapse_rare_combinations(df, thres):
    """Replace rare combinations with 'Other' except when it' common once."""
    common_combs = set(df[df["share"] >= thres]["types"].unique())
    keep = df["types"].isin(common_combs)
    rare = df["share"] < thres
    df.loc[rare & ~keep, "types"] = "Other"
    return df


def custom_pivot(df):
    """Compute shares, rename rare combinations and pivot DataFrame."""
    # Compute shares
    df = df.groupby(["Year", "types"])["count"].sum().reset_index()
    totals = df.groupby("Year")["count"].transform('sum')
    df["share"] = df["count"]/totals*100
    # Collapse rare combinations except those used
    df = collapse_rare_combinations(df, thres=THRESHOLD_MA)
    # Pivot
    df = df.groupby(["types", "Year"])["share"].sum().reset_index()
    df["Year"] = pd.to_datetime(df["Year"], format='%Y')
    return df.pivot(index='Year', columns='types', values='share')


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


def make_comparison_barplot(solo, multi, fname, figsize=(12, 15)):
    """Plot two panels, one with multi-affiliation affiliation types and one
    with solo-affiliation affilation types.
    """
    fig, axes = plt.subplots(2, 1, figsize=figsize, sharex=True)
    color = [_colors.get(c, "black") for c in multi.columns]
    multi.plot.bar(stacked=True, ax=axes[0], color=color)
    solo.plot.bar(stacked=True, ax=axes[1], rot=0, colormap="gist_gray",
                  edgecolor="black")
    # Aesthetics
    for idx, ax in enumerate(axes):
        ax.set_ylabel("Share in all author-article observations (in %)")
        ax.legend(title="")
        add_figure_letter(ax, idx)
    axes[0].legend(ncol=3)
    axes[1].set_xlabel("")
    # Save
    fig.savefig(fname, bbox_inches="tight")
    plt.close(fig)


def make_shares_table(multi, fname, byvar):
    """Create table with shares by `byvar` and save as latex file."""
    # Compute averages
    aggs = {"multiaff": max, "n": "count"}
    df = grouping_with_shares(multi, byvar, "types", aggs)
    df = (df.pivot(columns=byvar, values="share", index="types")
            .fillna(0))
    # Aggregate types that are always small
    small_values = df < THRESHOLD_MA
    small_combs = small_values.sum(axis=1) == df.shape[1]
    repl = {i: "Other" for i in df.index[small_combs]}
    df = df.reset_index("types")
    df["types"] = df["types"].replace(repl)
    df = df.groupby("types").sum()
    # Set small values to NaN
    df[df < THRESHOLD_MA] = nan
    # Maybe fields
    if byvar == "field":
        df.columns = [asjc_map.get(c, c) for c in df.columns]
    df = df[sorted(df.columns)]
    # Order rows and columns
    df = df.sort_values(df.columns[0], ascending=False).T
    order = list(df.columns)
    order.remove("Other")
    order.append("Other")
    # Write out
    df[order].to_latex(fname, index_names=False, na_rep=f"<{THRESHOLD_MA}",
                       float_format="%.1f")


def make_stacked_area_plot(df, fname, figsize=(20, 13)):
    """Make stacked area plot with co-affil shares over time and
    save as file.
    """
    color = [_colors.get(c, "black") for c in df.columns]
    fig, ax = plt.subplots(figsize=figsize)
    df.plot(kind="area", stacked=True, ax=ax, color=color)
    # Format legend
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(reversed(handles), reversed(labels), loc='upper right')
    # Aesthetics
    format_time_axis(ax, df.index.min(), df.index.max(), labels=True)
    ax.set(xlabel="", ylabel="Share of co-affiliation types")
    plt.margins(0, 0)
    fig.savefig(fname, bbox_inches="tight")
    plt.close(fig)


def sort_df(df, col=2019, ascending=False):
    """Sort a DataFrame by a specific column."""
    order = list(df.T.sort_values(col, ascending=ascending).index)
    df.columns = pd.CategoricalIndex(df.columns.values, ordered=True,
                                     categories=order)
    return df.sort_index(axis=1)


def main():
    # Read in
    df = read_source_files(["types", "author"], verbose=False)
    df["multiaff"] = (df["types"].str.find("-") > -1).astype("uint32")
    df = (df.sort_values("multiaff", ascending=False)
            .drop_duplicates(subset=["author", "field", "year"])
            .rename(columns={"year": "Year"}))
    df["types"] = df["types"].apply(clean_types)
    multi = df[df["multiaff"] == 1].copy()

    # Table on shares of particular MA combinations
    print(">>> Average type combinations by field as well as year")
    fname = OUTPUT_FOLDER + "/Tables/combs_share-field.tex"
    make_shares_table(multi, fname, byvar="field")
    fname = OUTPUT_FOLDER + "/Tables/combs_share-year.tex"
    make_shares_table(multi, fname, byvar="Year")
    multi = multi.drop("multiaff", axis=1)

    # Stacked area plots for affiliation type combinations by field
    print(">>> Plot affiliation type combinations by field")
    df_ma = aggregate_shares(multi)
    for field in df_ma["field"].unique():
        subset = custom_pivot(df_ma[df_ma["field"] == field])
        fname = f"{OUTPUT_FOLDER}Figures/combs_share-fields-{field}.pdf"
        make_stacked_area_plot(subset, fname=fname)

    # Stacked area plots for affiliation type combinations globally
    df_ma = aggregate_shares(multi.drop_duplicates(["author", "Year"]))
    del multi
    df_ma = df_ma.groupby(["Year", "types"])["count"].sum().reset_index()
    df_ma = custom_pivot(df_ma)
    fname = OUTPUT_FOLDER + "Figures/combs_share-fields-all.pdf"
    make_stacked_area_plot(df_ma, fname=fname)

    # Barplots for affiliation type combination for solo and MA obs
    print(">>> Plot affiliation type combinations by year")
    aggs = {"multiaff": max, "n": "count"}
    df_comb = grouping_with_shares(df, "Year", 'types', aggs)
    del df
    df_comb = collapse_rare_combinations(df_comb, thres=THRESHOLD_ALL)
    df_comb = (df_comb.groupby(["Year", "types", "multiaff"])
                      .sum().reset_index()
                      .sort_values("share"))
    comb_multi = df_comb[df_comb["multiaff"] == 1]
    pivot_kwds = {"columns": "types", "values": "share", "index": "Year"}
    comb_multi = sort_df(comb_multi.pivot(**pivot_kwds))
    comb_solo = df_comb[df_comb["multiaff"] == 0]
    comb_solo = sort_df(comb_solo.pivot(**pivot_kwds))
    fname = OUTPUT_FOLDER + "Figures/afftype_share-all_comparison.pdf"
    make_comparison_barplot(comb_solo, comb_multi, fname)

    # Table corresponding to above graph
    df_joint = comb_solo.T.append(comb_multi.T)
    fname = OUTPUT_FOLDER + "Tables/afftype_share-all_comparison.tex"
    df_joint.to_latex(fname, float_format="%.1f", index_names=False)


if __name__ == '__main__':
    main()
