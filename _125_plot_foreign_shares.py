#!/usr/bin/env python3
# Author:   Michael E. Rose <michael.ernst.rose@gmail.com>
"""Plots share of foreign co-affiliations and most important partner countries
for authors with multiple affiliations of each country.
NOTE: Ticks "125%" and "150%" need to be removed manually.
"""

from collections import Counter, defaultdict
from configparser import ConfigParser
from glob import glob
from math import ceil
from os.path import basename, splitext

import matplotlib as mpl
import pandas as pd
import seaborn as sns

from _105_analyze_multiaff_shares import read_source_files

COUNTRY_WHITELIST = "./098_country_whitelist/oecd_others.csv"
COUNTRIES_FOLDER = "./100_country_combinations/"
SHARES_FILE = "./105_multiaff_shares/shares.csv"
OUTPUT_FOLDER = "./990_output/"

countries = pd.read_csv(COUNTRY_WHITELIST, index_col=0)
_whitelist = set(countries.index)
_comparison_group = ["United States", "Russia", "United Kingdom", "China",
                     "Germany", "France", "Spain", "Italy", "Israel", "Canada"]
CMAP = "winter"  # Colormap for left panel
LENGTH = 4  # Number of years over which averages are computed

config = ConfigParser()
config.optionxform = str
config.read("./graphs.cfg")
_colors = dict(config["colors"])
mpl.pyplot.rcParams['font.family'] = config["styles"]["font"]
sns.set(style=config["styles"]["style"], font=config["styles"]["font"])


def compute_intensities(df):
    """Compute the intensity with which countries collaborate with
    each other.
    """
    intensities = {}
    for country in df['source'].unique():
        mask = (df['source'] == country)
        total = df[mask]['weight'].sum()
        internal = df[mask & (df['target'] == country)]['weight'].sum()
        intensities[country] = float(internal/total)
    return intensities


def make_foreign_multiaff_plot(fname, lhs, rhs, figsize, cmap,
                               norm, barwidth=1.5):
    """Create figure with two panels: Left panel shows share of authors
    with foreign co-affiliations, right panel shows most important
    partner countries.
    """
    from mpl_toolkits.axes_grid1.inset_locator import inset_axes
    country_map = lhs.reset_index()[""].to_dict()
    long = len(country_map) > 20
    # Prepare shares of countries for RHS
    rhs = rhs.groupby(["source", "target"]).sum().reset_index()
    totals = (rhs.groupby(['source'])['weight'].sum()
                 .to_frame(name="total_foreign"))
    rhs = rhs.merge(totals, "left", left_on="source", right_index=True)
    rhs["Share"] = rhs["weight"]/rhs["total_foreign"]
    rhs = (rhs.sort_values("Share", ascending=False)
              .drop(["weight", "total_foreign"], axis=1))
    # Start plot
    fig, axes = mpl.pyplot.subplots(len(country_map), 2, figsize=figsize)
    partners = []
    for idx, ax in enumerate(axes):
        country = country_map[idx]
        # LHS plot: Stacked bar for share of authors with foreign co-aff
        row = lhs.T[[country]].T
        row[["Foreign", "Domestic"]].plot(kind='barh', stacked=True, ax=ax[0],
                                          color=[row["color"], "#ffffff"],
                                          legend=False, width=barwidth)
        val = lhs.loc[country, "Foreign"]
        ax[0].text(val+3, -0.5, "{0:g}%".format(val), fontsize=8)
        # RHS plot: Stacked bar for most important partner countries
        subset = rhs[rhs["source"] == country].copy()
        least = subset.iloc[3:]["target"]
        subset.loc[subset["target"].isin(least), "target"] = "Other"
        partners.extend(subset["target"])
        subset = subset.set_index("target").groupby("target").sum()
        subset[["Share"]] = subset[["Share"]]*100
        subset["order"] = subset["Share"].rank()
        subset.loc["Other", "order"] = 0
        subset = subset.sort_values("order", ascending=False)
        color = [_colors.get(c, "black") for c in subset.index]
        subset[["Share"]].T.plot(kind='barh', stacked=True, legend=False,
                                 ax=ax[1], color=color, width=barwidth)
        # Increase width artifically for country legend to fit in
        if long:
            ax[1].set_xlim((0, 165))
        else:
            ax[1].set_xlim((0, 149))
        # Add titles to first row
        if idx == 0:
            ax[0].title.set_text('Share of authors with co-affiliation abroad')
            ax[1].title.set_text('Top 3 co-affiliation host countries')
        # Switch of axes (except for bottom-right row) and grids
        ax[1].axes.get_yaxis().set_visible(False)
        if idx != len(axes)-1:
            for sub_ax in ax:
                sub_ax.axes.get_xaxis().set_visible(False)
        else:
            ax[0].axes.get_xaxis().set_visible(False)
        for sub_ax in ax:
            sub_ax.grid(False)
            for frame in ("top", "right", "bottom", "left"):
                sub_ax.spines[frame].set_visible(False)
            sub_ax.xaxis.set_major_formatter(
                mpl.ticker.FuncFormatter(lambda y, _: '{0:g}%'.format(y)))
    # Add colorlegend
    idx = 5
    if long:
        idx *= 2
    cax = inset_axes(axes[idx, 0], width=0.3, height=2.0,
                     bbox_transform=fig.transFigure, bbox_to_anchor=(0.4, 0.5),
                     loc="right")
    _ = mpl.colorbar.ColorbarBase(cax, cmap=cmap, norm=norm,
        orientation='vertical', label="Share of authors with multiple affiliations")
    # Add country legend with fixed colors ordered according to frequency
    legend_elements = []
    partners = sorted([p for p in partners if not p == "Other"])
    for c, _ in Counter(partners).most_common():
        new = mpl.patches.Patch(color=_colors[c], lw=4, label=c)
        legend_elements.append(new)
    axes[0, 1].legend(handles=legend_elements)
    axes[0, 1].set_zorder(1)
    # Save
    mpl.pyplot.draw()
    fig.savefig(fname, bbox_inches="tight")
    mpl.pyplot.close()


def read_file(fname):
    """Read file and transform."""
    df = pd.read_csv(fname)
    return (df.melt(id_vars="Unnamed: 0", var_name="target", value_name="weight")
              .rename(columns={"Unnamed: 0": "source"})
              .dropna())


def main():
    # Read in and aggregate field- and year-wise
    container = defaultdict(lambda: pd.DataFrame())
    for fname in glob(COUNTRIES_FOLDER + "*.csv"):
        df = read_file(fname)
        rename = {'target': 'source', 'source': 'target'}
        df = pd.concat([df, df.rename(columns=rename)], sort=False)
        df = df[(df['source'].isin(_whitelist))]
        field, year = splitext(basename(fname))[0].split("_")
        container[year] = pd.concat([container[year], df])

    # Compute share of foreign co-affils by year
    all_intens = {}
    for identifier, df in container.items():
        df = df.groupby(['source', 'target']).sum().reset_index()
        all_intens[identifier] = compute_intensities(df)

    # Compute share of authors with MA by country and year
    cols = ["author", "country", "multiaff", "year"]
    df = read_source_files(cols, drop_duplicates=False)
    df["multiaff"] = df["multiaff"].fillna(0)
    shares = (df.sort_values("multiaff", ascending=False)
                .drop_duplicates(subset=["author", "year"])
                .groupby(["country", "year"])["multiaff"].agg(["size", sum])
                .reset_index())
    shares["share"] = shares["sum"]/shares["size"]
    n_col = ceil(shares["share"].max()*100)
    cmap = mpl.cm.get_cmap(CMAP, n_col)
    norm = mpl.colors.Normalize(vmin=0, vmax=n_col)

    # Plots of foreign affiliations by country of author
    for year in (1996, 2015):
        years = range(year, year+LENGTH)
        mask = shares["year"].isin(years)
        ma_share = shares[mask].groupby("country")["share"].mean().reset_index()
        # Prepare LHS
        lhs = pd.DataFrame({y: pd.Series(all_intens[str(y)]) for y in years})
        lhs["Domestic"] = lhs.sum(axis=1)
        lhs["Foreign"] = LENGTH - lhs["Domestic"]
        lhs = (lhs[["Foreign", "Domestic"]]/LENGTH)*100
        lhs = (lhs.round(0).astype(int)
                  .sort_values("Foreign", ascending=False)
                  .merge(ma_share, "left", left_index=True, right_on="country")
                  .set_index("country"))
        lhs["share_normed"] = lhs["share"]/(n_col/100)
        lhs["color"] = lhs["share_normed"].apply(
            lambda x: mpl.colors.to_hex(cmap(x)))
        lhs.index.name = ""
        # Prepare RHS
        rhs = pd.concat([container[str(y)] for y in years])
        rhs = rhs[rhs["source"] != rhs["target"]]
        # Correlation of share foreign and share MA authors
        print(">>> {:.3f}".format(lhs[["Foreign", "share"]].corr().iloc[1, 0]))
        # ...all countries
        fname = "{}Figures/foreignshare-partner_country-all_{}-{}.pdf".format(
            OUTPUT_FOLDER, year, year+LENGTH-1)
        make_foreign_multiaff_plot(fname, lhs, rhs, cmap=cmap,
                                   figsize=(9, 9), norm=norm)
        # ... selected countries
        lhs = lhs[lhs.index.isin(_comparison_group)]
        make_foreign_multiaff_plot(fname.replace("-all", ""), lhs, rhs,
                                   cmap=cmap, figsize=(8, 4), norm=norm)


if __name__ == '__main__':
    main()
