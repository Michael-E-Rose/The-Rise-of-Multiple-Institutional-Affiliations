#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Authors:   Michael E. Rose <michael.ernst.rose@gmail.com>
"""Analyzes and plots shares of authors with multiple affiliations in
various aggregations following the s bar-notation.
"""

from configparser import ConfigParser

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from _910_plot_multiaff_shares import add_figure_letter, format_time_axis

COUNTRY_WHITELIST = "./098_country_whitelist/oecd_others.csv"
SOURCE_FOLDER = "./105_multiaff_shares/"
OUTPUT_FOLDER = "./990_output/"

config = ConfigParser()
config.optionxform = str
config.read("./graphs.cfg")
_colors = dict(config["Countries"])
_colors["ExIn countries"] = "red"
_selected = ["China", "France", "Germany", "Russia"]
plt.rcParams['font.family'] = config["styles"]["font"]
sns.set(style=config["styles"]["style"], font=config["styles"]["font"])


def make_stackedgroup_lineplot(dfs, hues, fname, y="multiaffshare", x="year",
                               ylabel=None, figsize=(12, 12)):
    """Create and save single lineplot with error bands from two groups,
    whose lines are colored by hue.
    """
    # Plot
    fig, axes = plt.subplots(len(dfs), 1, figsize=figsize, sharex=True)
    for idx, (dat, hue) in enumerate(zip(dfs, hues)):
        _col = {c: _colors.get(c, "black") for c in dat[hue].unique()}
        sns.lineplot(x=x, y=y, hue=hue, data=dat, style=hue,
                     palette=_col, ax=axes[idx])
    # Aesthetics
    for i, ax in enumerate(axes):
        ax.set(xlabel="", ylabel=ylabel)
        ax.set_ylim(bottom=0)
        add_figure_letter(ax, i)
        handles, labels = ax.get_legend_handles_labels()
        ax.legend(handles=handles[1:], labels=labels[1:], loc="upper left")
    format_time_axis(axes[-1], dfs[-1][x].min(), dfs[-1][x].max(), length=6)
    # Save
    plt.savefig(fname, bbox_inches="tight")
    plt.close()


def main():
    # Create long country-year information indicating group membership
    country = pd.read_csv(COUNTRY_WHITELIST, usecols=["country", "EI"])
    exins =  country.dropna().set_index("country")["EI"].to_dict()
    years = sorted(range(1996, 2020))
    countries = sorted(country["country"])
    dummy = pd.DataFrame({"country": sorted(countries*len(years)),
                          "year": years*len(countries)})
    dummy = (dummy.sort_values(["country", "year"])
                  .merge(country, "left", left_on=["country", "year"],
                         right_on=["country", "EI"]))
    ei_label = "Excellence Initiative"
    dummy[ei_label] = dummy["country"].isin(exins.keys())*1
    _labels = {0: "Control group", 1: "ExIn countries"}
    dummy[ei_label] = dummy[ei_label].replace(_labels)

    # Add ExIn onset year to country name
    dummy["label"] = dummy["country"]
    for c, y in exins.items():
        label = f"{c} ({int(y)})"
        dummy["label"] = dummy["label"].replace(c, label)
        try:
            _selected.remove(c)
            _selected.append(label)
            _colors[label] = _colors[c]
        except ValueError:
            continue

    # Read share counts
    aggs = ("country", "countryfield")
    files = {agg: pd.read_csv(f"{SOURCE_FOLDER}by{agg}.csv") for agg in aggs}

    # Make plots of shares by group by aggregation
    ma_label = "Share of authors w/ multiple affiliations (in %)"
    for label, data in files.items():
        df = data.copy().merge(dummy, "left", on=["country", "year"])
        df = df.sort_values(ei_label)
        mask_selected = (df["label"].isin(_selected)) | (df[ei_label] == "Control group")
        selected = df[mask_selected].copy()
        selected.loc[df[ei_label] == "Control group", "label"] = "Control group"
        selected[ei_label] = selected[ei_label].fillna("Control group")
        fname = f"{OUTPUT_FOLDER}Figures/multiaff_groups-{label}.pdf"
        make_stackedgroup_lineplot([selected, df],  hues=["label", ei_label],
                                   fname=fname, ylabel=ma_label)


if __name__ == '__main__':
    main()
