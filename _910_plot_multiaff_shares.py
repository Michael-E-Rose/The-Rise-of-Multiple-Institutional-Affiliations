#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Authors:   Michael E. Rose <michael.ernst.rose@gmail.com>
#            Kaan Uçtum
"""Analyzes and plots shares of authors with multiple affiliations in
various aggregations following the s bar-notation.
"""

from configparser import ConfigParser
from math import ceil

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

COUNTRY_FILE = "./098_country_whitelist/oecd_others.csv"
SOURCE_FOLDER = "./105_multiaff_shares/"
OUTPUT_FOLDER = "./990_output/"

config = ConfigParser()
config.optionxform = str
config.read("./graphs.cfg")
_colors = dict(config["Countries"])
_colors["World"] = _colors["Rest of World"]
plt.rcParams['font.family'] = config["styles"]["font"]
sns.set(style=config["styles"]["style"], font=config["styles"]["font"])
config.read("./definitions.cfg")
_groups = dict(config["country groups"])
_exins = pd.read_csv(COUNTRY_FILE, index_col=0)["EI"].dropna().to_dict()

COUNTRIES_U = ["United States", "Russia", "China", "Israel", "Canada",
               "Europe", "World"]
COUNTRIES_L = ["Germany", "France", "Italy", "United Kingdom", "Spain",
               "Scandinavia w/o Norway", "Norway", "Netherlands",
               "Switzerland", "Belgium"]


def add_figure_letter(ax, n):
    """Add letter as plot label for multiplot figures."""
    from string import ascii_uppercase
    letter = ascii_uppercase[n]
    ax.text(-0.08, 1, letter, transform=ax.transAxes, size=20, weight='bold')


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


def make_comparison_lineplot(bycountry, byfield, byquality, y, ylabel, fname,
                             figsize=(9, 9), x="year"):
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
    _quality_order = ["Top octile", "Second octile", "Third octile",
                      "Fourth octile"]
    # Plot panels
    sns.lineplot(x=x, y=y, hue=byfield_var, data=byfield, ax=axes[0, 0],
                 style=None, ci=None)
    sns.lineplot(x=x, y=y, data=byquality, style=byquality_var,
                 ax=axes[0, 1], ci=None, style_order=_quality_order)
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
    for idx1, axarray in enumerate(axes):
        for idx2, ax in enumerate(axarray):
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
            ax.legend(handles=handles[1:], labels=labels[1:],
                      loc="upper left", ncol=ncols, title=title)
            add_figure_letter(ax, (idx1*2)+idx2)
    # Aesthetics
    axes[1, 0].set_ylim(top=ceil(bycountry[y].max()), bottom=0)
    format_time_axis(axes[1, 0], subset[x].min(), subset[x].max())
    format_time_axis(axes[1, 1], subset[x].min(), subset[x].max())
    axes[0, 0].set(ylabel=ylabel)
    axes[1, 0].set(ylabel=ylabel)
    # Save
    fig.savefig(fname, bbox_inches="tight")
    plt.close(fig)


def make_matrix_lineplot(df, y, fname, col="country", x="year", ylabel="Share (in %)"):
    """Create and save lineplots in a matrix."""
    # Plot
    g = sns.FacetGrid(df, col=col, col_wrap=5, aspect=1.41)
    g.map(sns.lineplot, x, y, ci=None)
    _min = df[x].min()
    _max = df[x].max()
    for ax in g.axes.flat:
        # Extract country from title
        title = ax.get_title()
        country = title.split("= ")[-1]
        ax.set(title=country, ylabel=ylabel)
        # Aesthetics
        format_time_axis(ax, _min, _max)
        ax.set_ylim(bottom=0)
        year = _exins.get(country)
        if year:
            ax.vlines(x=int(year), ymin=0.0, ymax=100, linewidth=2, color='r')
    # Save
    plt.savefig(fname, bbox_inches="tight")
    plt.close()


def make_stacked_lineplot(dfs, ys, fname, hue, x="year", ylabel=None,
                          figsize=(10, 12)):
    """Create and save stacked lineplots with possibly different y-values
    and x-value by year, and whose lines are colored by hue.
    """
    # Plot
    fig, axes = plt.subplots(len(dfs), 1, figsize=figsize, sharex=True)
    for idx, (df, y) in enumerate(zip(dfs, ys)):
        df = df.sort_values(hue)
        sns.lineplot(x=x, y=y, hue=hue, data=df, ax=axes[idx],
                     style=None, ci=None)
    # Legend
    handles, labels = axes[0].get_legend_handles_labels()
    axes[0].legend(handles=handles[1:], labels=labels[1:], ncol=2)
    for ax in axes[1:]:
        ax.get_legend().remove()
    # Aesthetics
    for idx, ax in enumerate(axes):
        ylabel = ylabel or ys[idx]
        ax.set(xlabel="", ylabel=ylabel)
        format_time_axis(ax, df[x].min(), df[x].max())
        ax.set_ylim(bottom=0)
        add_figure_letter(ax, idx)
    # Save
    fig.savefig(fname, bbox_inches="tight")
    plt.close(fig)


def make_single_lineplot(df, y, fname, hue, x="year", ylabel=None,
                         figsize=(10, 6)):
    """Create and save stacked lineplots with possibly different y-values
    and x-value by year, and whose lines are colored by hue.
    """
    # Plot
    fig, ax = plt.subplots(figsize=figsize)
    df = df.sort_values(hue)
    sns.lineplot(x=x, y=y, hue=hue, data=df, ax=ax, style=None, ci=None)
    # Legend
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles=handles[1:], labels=labels[1:], ncol=2)
    # Aesthetics
    ylabel = ylabel
    ax.set(xlabel="", ylabel=ylabel)
    format_time_axis(ax, df[x].min(), df[x].max())
    ax.set_ylim(bottom=0)
    # Save
    fig.savefig(fname, bbox_inches="tight")
    plt.close(fig)


def main():
    # Observation is author-country-year
    bycountry = pd.read_csv(SOURCE_FOLDER + "bycountry.csv")
    fname = OUTPUT_FOLDER + "Figures/multiaff_countriesmatrix-country.pdf"
    make_matrix_lineplot(bycountry, "multiaffshare", fname=fname)
    fname = OUTPUT_FOLDER + "Figures/foreignaff_countriesmatrix-country.pdf"
    make_matrix_lineplot(bycountry, "foreignaffshare", fname=fname)

    # Observation is author-countryfield-year
    bycountryfield = pd.read_csv(SOURCE_FOLDER + "bycountryfield.csv")
    fname = OUTPUT_FOLDER + "Figures/multiaff_countriesmatrix-countryfield.pdf"
    make_matrix_lineplot(bycountryfield, "multiaffshare", fname=fname)
    fname = OUTPUT_FOLDER + "Figures/foreignaff_countriesmatrix-countryfield.pdf"
    make_matrix_lineplot(bycountryfield, "foreignaffshare", fname=fname)

    # Observation is author-field-year
    ma_label = "Share of author-field-year obs. w/ multiple affiliations (in %)"
    fname = OUTPUT_FOLDER + "Figures/multiaff_fields-countryfield.pdf"
    make_single_lineplot(bycountryfield, "multiaffshare", hue="field",
                         fname=fname, ylabel=ma_label)
    byfield = pd.read_csv(SOURCE_FOLDER + "byfield.csv")
    fa_label = "Share of author-field-year obs. w/ foreign multiple affiliations (in %)"
    fname = OUTPUT_FOLDER + "Figures/foreignaff_fields-field-countryfield.pdf"
    make_stacked_lineplot([bycountryfield, byfield], ["foreignaffshare"]*2,
                          hue="field", fname=fname, ylabel=fa_label)

    # Combination of field, quality and country
    byquality = pd.read_csv(SOURCE_FOLDER + "byquality.csv")
    col = "Journal quality group"
    byquality[col] = pd.Categorical(byquality[col], ordered=True,
             categories=["Top octile", "Second octile", "Third octile",
                         "Fourth octile"])
    byquality = byquality.sort_values(col, ascending=False)
    bycountry["group"] = bycountry["country"].replace(_groups)
    bycountry = bycountry.sort_values(["group", "country"])
    ma_label = "Share of obs. w/ multiple affiliations (in %)"
    fname = OUTPUT_FOLDER + "Figures/multiaff_global.pdf"
    make_comparison_lineplot(bycountry, byfield, byquality, "multiaffshare",
                             ylabel=ma_label, fname=fname)
    fa_label = "Share of obs. w/ foreign multiple affiliations (in %)"
    fname = OUTPUT_FOLDER + "Figures/foreignaff_global.pdf"
    make_comparison_lineplot(bycountry, byfield, byquality, "foreignaffshare",
                             ylabel=fa_label, fname=fname)


if __name__ == '__main__':
    main()
