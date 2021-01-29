#!/usr/bin/env python3
# Author:   Michael E. Rose <michael.ernst.rose@gmail.com>
"""Plots share of foreign co-affiliations and most important partner countries
for authors with multiple affiliations of each country.

This script requires a *nix system to run properly.
"""

from collections import Counter, defaultdict
from configparser import ConfigParser
from glob import glob
from math import sqrt
from os.path import basename, splitext

import matplotlib as mpl
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
import seaborn as sns
from cdlib import algorithms
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from numpy import array

SHARES_FILE = "./105_multiaff_shares/bycountry.csv"
COUNTRY_FOLDER = "./120_country_matrices/"
OUTPUT_FOLDER = "./990_output/"

CMAP = "cool"  # Colormap for left panel
LENGTH = 4  # Number of years over which averages are computed
WEIGHT_CUTOFF = 0.1  # Minimum share of foreign authors for community plot

mpl.use('Agg')
config = ConfigParser()
config.optionxform = str
config.read("./graphs.cfg")
_colors = dict(config["Countries"])
plt.rcParams['font.family'] = config["styles"]["font"]
sns.set(style=config["styles"]["style"], font=config["styles"]["font"])


def make_community_plot(edges, fname):
    """Draw network of countries with color by community."""
    # Create network
    edges = edges[edges["Share"] > WEIGHT_CUTOFF]
    G = nx.from_pandas_edgelist(edges, edge_attr=["Share"],
                                create_using=nx.DiGraph())
    label_map = {c: c.replace(" ", "\n") for c in G.nodes()}
    G = nx.relabel_nodes(G, label_map)
    # Compute communities
    assignments = []
    communities = algorithms.leiden(G).communities
    for i, countries in enumerate(communities):
        for c in countries:
            assignments.append((c, i))
    # Assign colors to communities
    assignments = sorted(assignments)
    cmap = plt.cm.Accent
    norm = mpl.colors.Normalize(vmin=0, vmax=len(communities))
    colors = [mpl.colors.to_hex(cmap(norm(c))) for _, c in assignments]
    # Set plotting data
    weights = [d["Share"]**(1/4)*2 for u, v, d in G.edges(data=True)]
    pos = {'Australia': array([0.7, -0.5]),
           'Austria': array([1.6, 0.2]),
           'Argentina': array([-0.7, 1.4]),
           'Belgium': array([-0.8, -1.2]),
           'Canada': array([2.22575671, 1.5610229]),
           'Chile': array([-0.8, 0.5]),
           'China': array([1.61854788, 1.32449744]),
           'Czechia': array([1.9, -0.2]),
           'Denmark': array([0.55, 0.0]),
           'Estonia': array([0.9, -1.4]),
           'Finland': array([1.2, -0.8]),
           'France': array([0.5, -1.4]),
           'Greece': array([-0.62007952, -0.29862564]),
           'Germany': array([0.52524589, 0.29605388]),
           'Ireland': array([-1.40267759, -0.95125886]),
           'Israel': array([-0.27088909, 1.67098229]),
           'Italy': array([-1.27570138, -0.39003278]),
           'Japan': array([1.3, 2.2]),
           'Hungary': array([-0.58183462, 0.3007111]),
           'Lithuania': array([-0.18229243, -0.87409266]),
           'Mexico': array([-1.04499295, 0.8088658]),
           'Netherlands': array([-0.2, -0.1]),
           'New\nZealand': array([1.13144828, -0.40443485]),
           'Norway': array([0.4, -1.1]),
           'Poland': array([-0.5, 0.9]),
           'Portugal': array([-1.56933095, -0.02689741]),
           'Romania': array([-0.1, -1.5]),
           'Russia': array([-0.9, 1.]),
           'Singapore': array([0.9, -0.1]),
           'Slovakia': array([1.6, 0.5]),
           'Slovenia': array([-1.25634143, -1.17581249]),
           'South\nAfrica': array([-0.88135798, -0.66437467]),
           'South\nKorea': array([0.55168098, 2.029026]),
           'Spain': array([-1.43098845, 0.50067855]),
           'Switzerland': array([0.23053752, 0.15402242]),
           'Sweden': array([0.90539775, -1.05909741]),
           'Taiwan': array([1.8, 2.0]),
           'Turkey': array([-0.2, 0.3]),
           'United\nKingdom': array([0.1, -0.65800041]),
           'United\nStates': array([1.0, 1.2])}
    # Make plot
    fig, ax = plt.subplots(figsize=(15, 15))
    nodelist = sorted(G.nodes())
    nx.draw(G, ax=ax, nodelist=nodelist, pos=pos, with_labels=True, font_size=12,
            node_size=2000, node_color=colors, width=weights, edge_color="grey",
            arrows=True, font_weight="bold", arrowstyle='-|>', arrowsize=12,
            connectionstyle="arc3, rad = 0.1")
    plt.savefig(fname, bbox_inches="tight")
    plt.clf()


def make_foreign_partner_plot(fname, lhs, rhs, cmap, norm, figsize=(9, 9),
                              barwidth=1.5, n_neigh=2):
    """Create figure with two panels: Left panel shows share of authors
    with foreign co-affiliations, right panel shows most important
    partner countries.
    """
    country_map = lhs.reset_index()[""].to_dict()

    # Start plot
    fig, axes = plt.subplots(len(country_map), 2, figsize=figsize)
    partners = []
    lhs_cols = ["fa_share", "rest"]
    for idx, ax in enumerate(axes):
        country = country_map[idx]
        # LHS plot: Stacked bar for share of authors with foreign co-aff
        row = lhs.T[[country]].T
        row[lhs_cols].plot(kind='barh', stacked=True, width=barwidth, ax=ax[0],
                           color=[row["color"][0], "#ffffff"], legend=False)
        value = row["fa_share"][0]
        ax[0].text(value+3, -0.5, f"{value:g}%", fontsize=8)
        # RHS plot: Stacked bar for most important partner countries
        subset = rhs[rhs["source"] == country].copy()
        least = subset.iloc[n_neigh:]["target"]
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
        # Increase width artificially for country legend to fit in
        ax[1].set_xlim((0, 165))
        # Add titles to first row
        if idx == 0:
            ax[0].title.set_text('Share of multiple aff. authors w/ co-affiliation abroad')
            ax[1].title.set_text(f'Top {n_neigh} co-affiliation host countries')
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
                mpl.ticker.FuncFormatter(lambda x, _: f'{x:g}%'))

    # Add colored legend on LHS
    cax = inset_axes(axes[10, 0], width=0.3, height=2.0, loc="right",
                     bbox_transform=fig.transFigure, bbox_to_anchor=(0.4, 0.5))
    label = "Share of authors w/ multiple affiliations"
    _ = mpl.colorbar.ColorbarBase(cax, cmap=cmap, norm=norm,
                                  orientation='vertical', label=label)

    # Add country legend ordered according to frequency on RHS
    legend_elements = []
    partners = sorted([p for p in partners if not p == "Other"])
    for c, _ in Counter(partners).most_common():
        new = mpl.patches.Patch(color=_colors.get(c, "black"), lw=4, label=c)
        legend_elements.append(new)
    axes[0, 1].legend(handles=legend_elements)
    axes[0, 1].set_zorder(1)

    # Save
    plt.draw()
    fig.savefig(fname, bbox_inches="tight")
    plt.clf()


def make_network_plot(fname, edges, nodes, cmap, norm, cutoff=2,
                      figsize=(15, 15)):
    """Plot network conneting countries for hosting co-affiliations."""
    # Create network
    edges["weight"] = (edges["Share"] * 100).round().apply(sqrt)
    edges = (edges.sort_values(["source", "weight"], ascending=False)
                  .groupby("source").head(cutoff))
    G = nx.from_pandas_edgelist(edges, edge_attr=["weight"],
                                create_using=nx.DiGraph())
    # Initiate canvas
    fig, ax = plt.subplots(figsize=figsize)
    # Draw network
    weights = [d['weight'] for u, v, d in G.edges(data=True)]
    pos = nx.spring_layout(G, seed=15, scale=500, iterations=100)
    nx.draw(G, ax=ax, nodelist=list(nodes.index), pos=pos, with_labels=True,
            node_color=nodes["color"].values, node_size=nodes["size"].values,
            edge_color="grey", connectionstyle='arc3, rad = 0.1', width=weights,
            arrows=True, arrowstyle='-|>', arrowsize=12)
    # Add colored legend
    cax = inset_axes(ax, width=0.3, height=2, loc="lower right")
    label = "Share of authors w/ multiple affiliations"
    _ = mpl.colorbar.ColorbarBase(cax, cmap=cmap, norm=norm, label=label)
    # Save graph
    plt.savefig(fname, bbox_inches="tight")
    plt.clf()


def read_file_and_melt(fname):
    """Read file and melt."""
    df = pd.read_csv(fname, encoding="utf8")
    return (df.melt(id_vars="Unnamed: 0", var_name="target", value_name="authors")
              .rename(columns={"Unnamed: 0": "source"})
              .dropna())


def main():
    # Read linkages between countries
    linkages = defaultdict(lambda: pd.DataFrame())
    for f in glob(COUNTRY_FOLDER + "*[0-9].csv"):
        year = int(splitext(basename(f))[0])
        linkages[year] = read_file_and_melt(f)

    # Read share of MA authors by country and year
    cols = ['year', 'country', 'n_authors', 'multiaffshare']
    ma_shares = pd.read_csv(SHARES_FILE, encoding="utf8", usecols=cols)
    ma_shares = ma_shares.rename(columns={"multiaffshare": "ma_share"})
    fa_shares = pd.read_csv(COUNTRY_FOLDER + "foreign-share.csv", encoding="utf8")
    fa_shares = (fa_shares.rename(columns={"Unnamed: 0": "country"})
                          .melt(id_vars="country", var_name="year",
                                value_name="fa_share"))
    fa_shares["year"] = fa_shares["year"].astype("uint16")
    shares = ma_shares.merge(fa_shares, "left", on=["country", "year"])
    shares["fa_size"] = shares["n_authors"] * shares["fa_share"]
    shares["fa_share"] *= 100

    # Compute averages of MA and FA shares
    dfs = {}
    for year in (1996, 2016):
        years = range(year, year+LENGTH)
        # Prepare LHS
        grouped = shares[shares["year"].isin(years)].groupby("country")
        ma_share = grouped["ma_share"].mean().round(0).astype(int)
        fa_share = grouped["fa_share"].mean().round(0).astype(int)
        lhs = pd.concat([ma_share, fa_share], axis=1)
        lhs["rest"] = 100 - lhs["fa_share"]
        lhs["size"] = grouped["fa_size"].mean().apply(sqrt) * 100
        lhs.index.name = ""
        dfs[year] = lhs

    # Norm values to color
    n_col = pd.concat(dfs.values())["ma_share"].max()
    cmap = mpl.cm.get_cmap(CMAP, n_col)
    norm = mpl.colors.Normalize(vmin=0, vmax=n_col)

    # Plots of foreign affiliations by country of author
    for year, lhs in dfs.items():
        print(f">>> Working on {year}")
        # Define color of left bar
        lhs["color"] = lhs.apply(lambda s: mpl.colors.to_hex(cmap(s.ma_share/n_col)),
                                 axis=1)
        # Correlation of share foreign and share MA authors
        corr = lhs[["ma_share", "fa_share"]].corr().iloc[1, 0]
        print("... Correlation MA intensity & share foreign "
              f"aff authors: {corr:.3f}")

        # Compute linkages between countries
        rhs = pd.concat([linkages[y] for y in range(year, year+LENGTH)])
        rhs = rhs[rhs["source"] != rhs["target"]]
        rhs = rhs.groupby(["source", "target"]).sum().reset_index()
        rhs["total_foreign"] = rhs.groupby("source")["authors"].transform(sum)
        rhs = rhs[rhs["target"] != "Other"]

        # Print importance of US as most frequent host country
        print(">>> Distribution of share of US among partners:")
        rhs["Share"] = rhs["authors"] / rhs["total_foreign"]
        rhs = rhs.sort_values("Share", ascending=False)
        usa_mask = (rhs["target"] == "United States") & (~rhs["source"].duplicated())
        print((rhs[usa_mask]["Share"] * 100).round(2).describe(percentiles=[]))

        # Plot double barchart
        suffix = f"{year}-{year+LENGTH-1}"
        fname = f"{OUTPUT_FOLDER}Figures/foreignshare-partner_"\
                f"{suffix}.pdf"
        make_foreign_partner_plot(fname, lhs, rhs, cmap=cmap, norm=norm)

        # Plot network alternative
        rhs = rhs[rhs["source"] != "Other"]
        fname = f"{OUTPUT_FOLDER}Figures/network-partner_{suffix}.pdf"
        make_network_plot(fname, edges=rhs, nodes=lhs, cmap=cmap, norm=norm)

        # Plot community network
        if year == 2016:
            fname = f"{OUTPUT_FOLDER}Figures/network_{suffix}.pdf"
            make_community_plot(rhs, fname=fname)


if __name__ == '__main__':
    main()
