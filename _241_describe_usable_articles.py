#!/usr/bin/env python3
# Author:   Michael E. Rose <michael.ernst.rose@gmail.com>
"""Describes number of author- and article-observations by country,
raw data used and share of useable papers.
"""

from configparser import ConfigParser

import pandas as pd
from numpy import int64

from _002_sample_journals import write_stats
from _105_analyze_multiaff_shares import format_time_axis, read_source_files

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
    if isinstance(x, (int, int64)):
        return '{:,}'.format(x).replace(".0", "")
    elif isinstance(x, str):
        return x
    else:
        return "{:0.2f}".format(x)


def make_double_lineplot(dfs, labels, fname, hue, x="year", figsize=(10, 10)):
    """Create and save two stacked lineplots."""
    import matplotlib.pyplot as plt
    import seaborn as sns
    # Plot
    fig, axes = plt.subplots(2, 1, figsize=figsize, sharex=True)
    for idx, (df, label) in enumerate(zip(dfs, labels)):
        df = df.sort_values(hue)
        sns.lineplot(x=x, y=label, hue=hue, data=df, ax=axes[idx], style=None)
    # Aesthetics
    handles, labels = axes[0].get_legend_handles_labels()
    axes[0].legend(handles=handles[1:], labels=labels[1:], ncol=2)
    axes[1].get_legend().remove()
    format_time_axis(axes[-1], df[x].min(), df[x].max())
    for ax in axes:
        ax.set_ylim(bottom=0)
    # Save
    fig.savefig(fname, bbox_inches="tight")
    plt.close(fig)


def read_from_statistics(fname):
    """Read number from statistics text files."""
    fname = "{}Statistics/{}.txt".format(OUTPUT_FOLDER, fname)
    with open(fname) as inf:
        return int(inf.read().strip().replace(",", ""))


def main():
    # LaTeX table on authors and papers by country, and statistics
    cols = ["country", "author", "eid", "year"]
    df = read_source_files(cols, drop_duplicates=False)
    authors_unique = df['author'].nunique()
    articles_unique = df['eid'].nunique()
    authoryearfield = df.groupby(["author", "year", "field"]).count()
    authoryear = df.groupby(["author", "year"]).count()
    stats = {"N_of_authors_unique": authors_unique,
             "N_of_articles_unique": articles_unique,
             "N_of_authoryear": authoryear.shape[0],
             "N_of_authoryearfield": authoryearfield.shape[0],
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
    grouped = grouped[sorted(grouped.columns, key=lambda t: t[0])]
    fname = OUTPUT_FOLDER + "Tables/articlesauthors_country.tex"
    grouped.to_latex(fname, formatters=[latex_formatter]*grouped.shape[0],
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
                     formatters=[latex_formatter]*overall.shape[0])

    # Graph on shares of usable articles by field
    share_use = useable.div(papers)*100
    label_use = "Share of articles with useable affiliation information (in %)"
    share_use = format_shares(share_use, label_use)
    share_org = 100-nonorg.div(papers)*100
    label_org = "Share of articles with complete affiliation information (in %)"
    share_org = format_shares(share_org, label_org)
    fname = OUTPUT_FOLDER + "Figures/useable_share_field.pdf"
    make_double_lineplot((share_use, share_org), (label_use, label_org),
                         fname, hue="field")

if __name__ == '__main__':
    main()
