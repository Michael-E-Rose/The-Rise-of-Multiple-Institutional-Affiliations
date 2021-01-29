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

from _110_rank_affiliations import format_time_axis

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
_exins = pd.read_csv(COUNTRY_FILE, index_col=0, encoding="utf8")["EI"].dropna().to_dict()

COUNTRIES_U = ["United States", "Russia", "China", "Israel", "Canada",
               "Europe", "World"]
COUNTRIES_L = ["Germany", "France", "Italy", "United Kingdom", "Spain",
               "Scandinavia w/o Norway", "Norway", "Netherlands",
               "Switzerland", "Belgium"]
N_FIELDS = 13  # Number of fields to show in multiaff_global.pdf


def add_figure_letter(ax, n):
    """Add letter as plot label for multiplot figures."""
    from string import ascii_uppercase
    letter = ascii_uppercase[n]
    ax.text(-0.08, 1, letter, transform=ax.transAxes, size=20, weight='bold')


def make_comparison_lineplot(bycountry, byfield, byquality, y, ylabel, fname,
                             figsize=(9, 9), x="year"):
    """Make graph with three panels:
    1. Share of MA authors by field
    2. Share of MA authors by journal quality group
    3. Share of MA authors for selected countries
    4. Share of MA authors for European countries
    """
    byfield_var = "field"
    byquality_var = "Journal quality group"
    bycountry_var = "group"
    # Start plot
    fig, axes = plt.subplots(2, 2, figsize=figsize, sharex=True, sharey=True)
    fig.tight_layout()
    # Line styles
    _linestyle = {c: "" for c in bycountry["country"].unique()}
    _linestyle["Europe"] = (5, 1)  # long dashes
    _linestyle["Scandinavia w/o Norway"] = (3, 1)  # short dashes
    _linestyle["World"] = (1, 1)  # dots
    _quality_order = ["Top", "Second", "Third", "Fourth"]
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
            # Legend
            title = None
            if idx1 == 0 and idx2 == 1:
                title = byquality_var
            ncols = 1
            if (idx1 == 0 and idx2 == 0) or (idx1 == 1 and idx2 == 1):
                ncols = 2
            ax.legend(loc="best", ncol=ncols, title=title)
            # Figure letter
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


def make_shares_table(df, fname, index, values):
    """Transform long table and write out Latex table."""
    df = df.pivot(index=index, columns="year", values=values)
    df["Average"] = df.mean(axis=1)
    df.to_latex(fname, escape=False, float_format="%.1f", index_names=False)


def make_stacked_lineplot(dfs, ys, fname, hue, x="year", ylabels=None,
                          figsize=(10, 12), ncol=4):
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
    axes[0].legend(handles=handles[0:], labels=labels[0:], ncol=ncol, loc="best")
    for ax in axes[1:]:
        ax.get_legend().remove()
    # Aesthetics
    for i, ax in enumerate(axes):
        ax.set(xlabel="", ylabel=ylabels[i])
        format_time_axis(ax, df[x].min(), df[x].max())
        ax.set_ylim(bottom=0, top=100)
        add_figure_letter(ax, i)
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
    ax.legend(handles=handles[0:], labels=labels[0:], ncol=2)
    # Aesthetics
    ax.set(xlabel="", ylabel=ylabel)
    format_time_axis(ax, df[x].min(), df[x].max())
    ax.set_ylim(bottom=0)
    # Save
    fig.savefig(fname, bbox_inches="tight")
    plt.close(fig)


def main():
    # Observation is author-country-year
    bycountry = pd.read_csv(SOURCE_FOLDER + "bycountry.csv", encoding="utf8")
    for a in ("multiaffshare", "foreignaffshare"):
        fname = f"{OUTPUT_FOLDER}Figures/{a[:-5]}_countriesmatrix-country.pdf"
        make_matrix_lineplot(bycountry, a, fname)
        fname = f"{OUTPUT_FOLDER}Tables/{a[:-5]}_authors_share-country.tex"
        make_shares_table(bycountry, fname, index="country", values=a)

    # Observation is author-countryfield-year
    bycountryfield = pd.read_csv(SOURCE_FOLDER + "bycountryfield.csv", encoding="utf8")
    for a in ("multiaffshare", "foreignaffshare"):
        fname = f"{OUTPUT_FOLDER}Figures/{a[:-5]}_countriesmatrix-countryfield.pdf"
        make_matrix_lineplot(bycountryfield, a, fname)
        fname = f"{OUTPUT_FOLDER}Tables/{a[:-5]}_authors_share-countryfield.tex"
        temp = bycountryfield.groupby(["field", "year"]).mean().reset_index()
        make_shares_table(temp, fname, index="field", values=a)
    ma_label = "Share of author-field-year obs. w/ MA (in %)"
    fname = OUTPUT_FOLDER + "Figures/multiaff_fields-countryfield.pdf"
    make_single_lineplot(bycountryfield, "multiaffshare", hue="field",
                         fname=fname, ylabel=ma_label)

    # Observation is author-fieldcountry-year
    for a in ("multiaffshare", "foreignaffshare"):
        fname = f"{OUTPUT_FOLDER}Tables/{a[:-5]}_authors_share-fieldcountry.tex"
        temp = bycountryfield.groupby(["country", "year"]).mean().reset_index()
        make_shares_table(temp, fname, index="country", values=a)

    # Observation is author-field-year
    byfield = pd.read_csv(SOURCE_FOLDER + "byfield.csv", encoding="utf8")
    for a in ("multiaffshare", "foreignaffshare"):
        fname = f"{OUTPUT_FOLDER}Tables/{a[:-5]}_authors_share-field.tex"
        make_shares_table(byfield, fname, index="field", values=a)
    fa_label = "Share of author-field-year obs. w/ foreign MA (in %)"
    fname = OUTPUT_FOLDER + "Figures/foreignaff_fields-field-countryfield.pdf"
    make_stacked_lineplot([bycountryfield, byfield], ["foreignaffshare"]*2,
                          hue="field", fname=fname, ylabels=[fa_label]*2)

    # Observation is author-journal quality group-year
    byquality = pd.read_csv(SOURCE_FOLDER + "byquality.csv", encoding="utf8")
    col = "Journal quality group"
    byquality[col] = byquality[col].astype("category")
    ordering = ['Top', 'Second', 'Third', 'Fourth']
    byquality[col] = byquality[col].cat.reorder_categories(ordering)
    for a in ("multiaffshare", "foreignaffshare"):
        fname = f"{OUTPUT_FOLDER}Tables/{a[:-5]}_authors_share-quality.tex"
        make_shares_table(byquality, fname, index=col, values=a)

    # Combination of field, quality and country
    bycountry["group"] = bycountry["country"].replace(_groups)
    bycountry = bycountry.sort_values(["group", "country"])
    top_fields = (byfield.groupby("field")["n_authors"].sum()
                         .sort_values().tail(N_FIELDS).index)
    byfield = byfield[byfield["field"].isin(top_fields)]
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
