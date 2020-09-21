#!/usr/bin/env python3
# Author:   Michael E. Rose <michael.ernst.rose@gmail.com>
"""Describe raw data used and share of useable papers."""

from configparser import ConfigParser

import pandas as pd
from numpy import int32, int64

from _002_sample_journals import write_stats
from _105_aggregate_shares import read_source_files
from _910_plot_multiaff_shares import make_stacked_lineplot

JOURNAL_FOLDER = "./002_journal_samples/"
COUNTS_FOLDER = "./100_meta_counts/"
OUTPUT_FOLDER = "./990_output/"

pd.plotting.register_matplotlib_converters()
pd.options.display.float_format = '{:,}'.format

config = ConfigParser()
config.optionxform = str
config.read("./definitions.cfg")
asjc_map = dict(config["field names"])


def count_unique(data):
    """Count the number of unique elements."""
    return data.nunique()


def format_shares(df, val_name):
    """Melt wide DataFrame and replace field codes with field names."""
    df.columns = [asjc_map.get(c, c) for c in df.columns]
    df = df[asjc_map.values()]
    df.index.name = "year"
    return (df.reset_index()
              .melt(id_vars=["year"], var_name="field", value_name=val_name)
              .sort_values("field"))


def latex_formatter(x):
    """Add thousands separator to large numbers."""
    if isinstance(x, (int, int32, int64)):
        return f'{x:,}'.replace(".0", "")
    elif isinstance(x, str):
        return x
    else:
        return "{:0.2f}".format(x)


def read_from_statistics(fname):
    """Read number from statistics text files."""
    fname = f"{OUTPUT_FOLDER}Statistics/{fname}.txt"
    with open(fname) as inf:
        return int(inf.read().strip().replace(",", ""))


def main():
    # LaTeX table on authors and papers by country, and statistics
    dtypes = {"author": "uint64", "year": "uint16"}
    df = read_source_files(["country", "author", "eid", "year"], dtype=dtypes)
    df["country"] = df["country"].astype("category")
    articles_unique = df['eid'].nunique()
    authoryear = df.groupby(["author", "year"]).count()
    stats = {"N_of_articles_unique": articles_unique,
             "N_of_authoryear": authoryear.shape[0],
             "N_of_authorpaperfield": df.shape[0]}
    write_stats(stats)
    grouped = df.groupby(["country"]).agg(
        Articles=pd.NamedAgg(column='eid', aggfunc=count_unique),
        Authors=pd.NamedAgg(column='author', aggfunc=count_unique))
    del df
    cols = grouped.columns
    mult_cols = [(c, "Unique") for c in cols]
    grouped.columns = pd.MultiIndex.from_tuples(mult_cols)
    for c in cols:
        label = (c, "Unique")
        total = grouped[label].sum()
        grouped[(c, "Share (in %)")] = round(grouped[label]/total*100, 2)
    grouped.index.name = "Country"
    grouped[("Authors", "Unique")] = grouped[("Authors", "Unique")].astype(int)
    grouped = grouped[sorted(grouped.columns, key=lambda t: t[0])]
    fname = OUTPUT_FOLDER + "Tables/articlesauthors_country.tex"
    grouped.to_latex(fname, formatters=[latex_formatter]*(grouped.shape[1]),
                     multicolumn_format='c',)

    # Read meta information
    journals = pd.read_csv(JOURNAL_FOLDER + "journal-counts.csv", index_col=0).T
    journals = journals[["Total", "Coverage > 5 years", "Used"]]
    journals = journals.rename(columns={"Used": "Sampled for Study"})
    authors = pd.read_csv(COUNTS_FOLDER + "num_unique_authors.csv", index_col=0).T
    papers = pd.read_csv(COUNTS_FOLDER + "num_unique_papers.csv", index_col=0)
    useable = pd.read_csv(COUNTS_FOLDER + "num_unique_papers-useful.csv", index_col=0)
    nonorg = pd.read_csv(COUNTS_FOLDER + "num_nonorg_papers.csv", index_col=0)

    # LaTeX table with authors and papers by field
    overall = journals.copy()
    cols = [("Journals", c) for c in overall.columns]
    overall.columns = pd.MultiIndex.from_tuples(cols)
    overall[("Authors", "Total")] = authors["all"]
    overall[("Articles", "Total")] = papers.sum(axis=0)
    overall[("Articles", "Used in Study")] = useable.sum(axis=0)
    share = overall[("Articles", "Used in Study")]/overall[("Articles", "Total")]*100
    overall[("Articles", "Share (in %)")] = round(share, 2)
    overall = overall.sort_index()
    # Add column totals
    overall.loc["Unique"] = [""] * overall.shape[1]
    journals_total = read_from_statistics("N_of_journals_unique")
    overall.loc["Unique", ("Journals", "Total")] = journals_total
    journals_useful = read_from_statistics("N_of_journals_useful")
    overall.loc["Unique", ("Journals", "Coverage > 5 years")] = journals_useful
    journals_used = read_from_statistics("N_of_journals_used")
    overall.loc["Unique", ("Journals", "Sampled for Study")] = journals_used
    overall.loc["Unique", ("Authors", "Total")] = authors_unique
    overall.loc["Unique", ("Articles", "Used in Study")] = articles_unique
    overall.index = [asjc_map.get(f, f) for f in overall.index]
    overall.index.name = "Field"
    # Write out
    fname = OUTPUT_FOLDER + "Tables/overview_useable.tex"
    overall.to_latex(fname, multicolumn_format='c',
                     formatters=[latex_formatter]*overall.shape[1])

    # Graph on shares of usable articles by field
    share_use = useable.div(papers)*100
    label_use = "Share of articles w/ useable affiliation information"
    share_use = format_shares(share_use, label_use)
    share_org = 100-nonorg.div(papers)*100
    label_org = "Share of articles w/ complete affiliation information"
    share_org = format_shares(share_org, label_org)
    fname = OUTPUT_FOLDER + "Figures/useable_share_field.pdf"
    make_stacked_lineplot((share_use, share_org), (label_use, label_org),
                          fname, hue="field")


if __name__ == '__main__':
    main()
