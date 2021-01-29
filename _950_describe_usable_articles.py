#!/usr/bin/env python3
# Author:   Michael E. Rose <michael.ernst.rose@gmail.com>
"""Describe raw data used and share of useable papers."""

from configparser import ConfigParser
from glob import glob

import pandas as pd

from _910_analyze_multiaff_shares import make_stacked_lineplot

JOURNAL_FOLDER = "./002_journal_samples/"
SOURCE_FOLDER = "./100_source_articles/"
COUNTS_FOLDER = "./100_meta_counts/"
OUTPUT_FOLDER = "./990_output/"

pd.plotting.register_matplotlib_converters()
pd.options.display.float_format = '{:,}'.format

config = ConfigParser()
config.optionxform = str
config.read("./definitions.cfg")
asjc_map = dict(config["field names"])


def format_shares(df, val_name):
    """Melt wide DataFrame and replace field codes with field names."""
    df.columns = [asjc_map.get(c, c) for c in df.columns]
    df = df[asjc_map.values()]
    df.index.name = "year"
    return (df.reset_index()
              .melt(id_vars=["year"], var_name="field", value_name=val_name)
              .sort_values("field"))


def read_from_statistics(fname):
    """Read number from statistics text files."""
    fname = f"{OUTPUT_FOLDER}Statistics/{fname}.txt"
    with open(fname) as inf:
        return int(inf.read().strip().replace(",", ""))


def main():
    # Compute number of authors by field
    author_counts = pd.Series(dtype="uint64")
    for field in asjc_map.keys():
        authors = set()
        for f in glob(f"{SOURCE_FOLDER}articles_{field}-*.csv"):
            df = pd.read_csv(f, encoding="utf8", usecols=["author"])
            authors.update(df["author"].unique())
        author_counts[field] = len(authors)

    # LaTeX table with authors and papers by field
    fname = JOURNAL_FOLDER + "journal-counts.csv"
    journals = pd.read_csv(fname, index_col=0, encoding="utf8").T
    journals = journals[["Total", "Coverage > 5 years", "Used"]]
    journals = journals.rename(columns={"Used": "Sampled"})
    overall = journals.copy()
    cols = [("Journals", c) for c in overall.columns]
    overall.columns = pd.MultiIndex.from_tuples(cols)

    # Add columns
    fname = COUNTS_FOLDER + "num_publications.csv"
    publications = pd.read_csv(fname, index_col=0, encoding="utf8")
    overall[("Articles", "Sampled")] = publications.sum(axis=0)
    fname = COUNTS_FOLDER + "num_articles.csv"
    articles = pd.read_csv(fname, index_col=0, encoding="utf8")
    overall[("Articles", "research-type")] = articles.sum(axis=0)
    fname = COUNTS_FOLDER + "num_useful.csv"
    useful = pd.read_csv(fname, index_col=0, encoding="utf8")
    overall[("Articles", "Useful")] = useful.sum(axis=0)
    fname = COUNTS_FOLDER + "num_used.csv"
    used = pd.read_csv(fname, index_col=0, encoding="utf8")
    overall[("Articles", "Used")] = used.sum(axis=0)
    share = overall[("Articles", "Used")]/overall[("Articles", "Sampled")]*100
    overall[("Articles", "Share (in %)")] = round(share, 2)
    overall[("Authors", "Used")] = author_counts

    # Sort alphabetically
    overall.index = [asjc_map.get(f, f) for f in overall.index]
    overall.index.name = "Field"
    overall = overall.sort_index()

    # Add row for totals
    overall.loc["Unique"] = [None] * overall.shape[1]
    totals = [(("Journals", "Total"), "N_of_journals_unique"),
              (("Journals", "Coverage > 5 years"), "N_of_journals_useful"),
              (("Journals", "Sampled"), "N_of_journals_used"),
              (("Articles", "Used"), "N_of_articles_unique"),
              (("Authors", "Used"), "N_of_authors_unique")]
    for col, fname in totals:
        overall.loc["Unique", col] = read_from_statistics(fname)

    # Write out
    overall = overall.astype(float)
    fname = OUTPUT_FOLDER + "Tables/overview_useable.tex"
    overall.to_latex(fname, float_format=lambda x: f"{x:,.0f}", na_rep="",
                     formatters={('Articles', 'Share (in %)'): lambda x: f"{x:,}"},
                     multicolumn_format='c')

    # Graph on shares of usable articles by field
    share_use = useful.div(articles)*100
    label_use = "Share of papers w/ useable affiliation information"
    share_use = format_shares(share_use, label_use)
    fname = COUNTS_FOLDER + "num_nonorg_papers.csv"
    nonorg = pd.read_csv(fname, index_col=0, encoding="utf8")
    share_org = 100-nonorg.div(articles)*100
    label_org = "Share of papers w/ complete affiliation information"
    share_org = format_shares(share_org, label_org)
    fname = OUTPUT_FOLDER + "Figures/useable_share_field.pdf"
    make_stacked_lineplot(dfs=(share_use, share_org), ys=(label_use, label_org),
                          ylabels=(label_use, label_org), fname=fname, hue="field")


if __name__ == '__main__':
    main()
