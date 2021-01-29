#!/usr/bin/env python3
# Author:   Michael E. Rose <michael.ernst.rose@gmail.com>
"""Creates LaTeX table depicting the share of solo-authored papers
over time and by field.
"""

from configparser import ConfigParser

import matplotlib.pyplot as plt
import seaborn as sns

from _002_sample_journals import write_stats
from _105_aggregate_shares import read_source_files
from _110_rank_affiliations import format_time_axis

SOURCE_FOLDER = "./100_source_articles/"
OUTPUT_FOLDER = "./990_output/"

config = ConfigParser()
config.optionxform = str
config.read("./graphs.cfg")
plt.rcParams['font.family'] = config["styles"]["font"]
sns.set(style=config["styles"]["style"], font=config["styles"]["font"])
config.read("./definitions.cfg")
asjc_map = dict(config["field names"])


def make_shares_graph(fname, df, figsize=(10, 5)):
    """Create and save graph depicting share of solo-authored papers on
    all papers and share of solo-authored papers with MA on solo-authored
    papers."""
    # Share of solo-authored papers on all papers
    share = df.groupby(["year"])["solo"].mean().reset_index()
    share["solo"] = share["solo"]*100
    share_label = "Solo-authored articles (left axis)"
    share = share.rename(columns={"solo": share_label})
    # Share of solo-authored MA papers on all solo-authored papers
    solo = df[df["solo"] == 1].copy()
    ma_label = "Solo-authored articles with multiple affilations (right axis)"
    solo[ma_label] = solo["multiaff"].fillna(0)
    solo_ma = solo.groupby(["year"])[ma_label].mean().reset_index()
    solo_ma[ma_label] = solo_ma[ma_label]*100
    # Plot
    fig, ax1 = plt.subplots(figsize=figsize)
    share.plot(x="year", y=share_label, ax=ax1, legend=False)
    ax2 = ax1.twinx()
    solo_ma.plot(x="year", y=ma_label, ax=ax2, legend=False, color="r")
    # Aesthetics
    ax1.set_ylabel("Share of solo-authored articles on all articles (in %)")
    ax1.set_ylim(bottom=0)
    ax2.set_ylabel("Share of solo-authored articles with MA on solo-authored articles (in %)")
    ax2.set_ylim(bottom=0)
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="best", ncol=1)
    format_time_axis(ax1, share["year"].min(), share["year"].max())
    # Write out
    fig.savefig(fname, bbox_inches="tight")
    plt.close(fig)


def make_shares_table(fname, df):
    """Create and save table depicting shares of solo-authored papers."""
    # Compute shares
    grouped = df.groupby(["year", "field"])["solo"].mean().reset_index()
    grouped["field"] = grouped["field"].replace(asjc_map)
    # Format
    out = grouped.pivot(index="field", columns="year", values="solo")
    out = (out.fillna(0) * 100).round(0).astype(int)
    out.columns.name = "Year"
    out.index.name = ""
    # Write out
    out.T.to_latex(fname)


def main():
    # Read in
    dtypes = {"author_count": "uint8"}
    df = read_source_files(["eid", "author_count", "affiliations"],
                           drop_duplicates=["eid"], dtype=dtypes)
    write_stats({"N_of_authorpaper": df.shape[0]})
    df["solo"] = (df["author_count"] == 1)*1
    df["multiaff"] = (df["affiliations"].str.find(";") != -1).astype("uint8")
    df = df.drop(["affiliations", "author_count"], axis=1)

    # Graph with shares
    fname = OUTPUT_FOLDER + "Figures/solo-multiaff_shares-paper-all.pdf"
    make_shares_graph(fname, df)

    # Table with shares of solo-authored papers
    fname = OUTPUT_FOLDER + "Tables/solo_shares-paper-all.tex"
    make_shares_table(fname, df)


if __name__ == '__main__':
    main()
