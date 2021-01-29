#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Authors:   Michael E. Rose <michael.ernst.rose@gmail.com>
"""Creates shares of MA authors in various aggregations following
the s bar-notation.
"""

from configparser import ConfigParser
from glob import glob

import pandas as pd

from _002_sample_journals import write_stats
from _100_parse_articles import print_progress

JOURNAL_FOLDER = "./002_journal_samples/"
TARGET_FOLDER = "./105_multiaff_shares/"
OUTPUT_FOLDER = "./990_output/"

config = ConfigParser()
config.optionxform = str
config.read("./definitions.cfg")
_asjc_map = {int(k): v for k, v in dict(config["field names"]).items()}
_groups = dict(config["country groups"])


def aggregate(df, columns, aggs={"multiaff": ["size", sum], "foreignaff": sum},
              totals=False):
    """Compute multiaff share for unique observations via groupby."""
    if totals:
        tot = (df.drop_duplicates(["author", "year"])
                 .groupby(["year"]).agg(aggs)
                 .reset_index())
        tot[('field', '')] = "All"
    df = (df.drop_duplicates(["author", "year"] + columns)
            .groupby(["year"] + columns).agg(aggs)
            .reset_index())
    if totals:
        df = df.append(tot)
    df.columns = [''.join(col) for col in df.columns]
    df["multiaffshare"] = df["multiaffsum"]/df["multiaffsize"]*100
    df["foreignaffshare"] = df["foreignaffsum"]/df["multiaffsum"]*100
    return (df.rename(columns={"multiaffsize": "n_authors"})
              .drop(["multiaffsum", "foreignaffsum"], axis=1))


def count_unique(data):
    """Count the number of unique elements."""
    return data.nunique()


def make_articles_shares_table(df, fname, byvar):
    """Create and write out Latex-formated table on shares by
    field over time.
    """
    # Aggregate information at observational level
    df = (df.sort_values("multiaff", ascending=False)
            .groupby(["year", byvar, "eid"])["multiaff"].max()
            .reset_index())
    # Aggregate information at field-year level (for totals)
    grouped = df.groupby([byvar, "year"])["multiaff"]
    out = grouped.sum().to_frame()
    out["share"] = (out["multiaff"]/grouped.count())*100
    del grouped
    out = (out.reset_index()
              .drop("multiaff", axis=1)
              .pivot(columns=byvar, values="share", index="year"))
    overall = df.groupby(["year"])["multiaff"].agg(["sum", "count"])
    # Rename and sort columns
    out.columns = [_asjc_map.get(c, c) for c in out.columns]
    out = out[sorted(out.columns)]
    out["All"] = overall["sum"]/overall["count"]*100
    # Add average
    out.loc["Average"] = out.mean(axis=0)
    # Write out
    out.T.to_latex(fname, escape=False, index_names=False, float_format="%.2f")


def read_source_files(cols, drop_duplicates=None, **pd_kwds):
    """Read files from SOURCE_FOLDER."""
    from glob import glob
    from os.path import basename, splitext

    df = []
    files = glob("./100_source_articles/*.csv")
    total = len(files)
    print(">>> Reading files...")
    print_progress(0, total)
    for idx, f in enumerate(files):
        new = pd.read_csv(f, usecols=cols, encoding="utf8", **pd_kwds)
        if drop_duplicates:
            new = new.drop_duplicates(subset=drop_duplicates)
        name_parts = splitext(basename(f))[0].split("_")[1].split("-")
        new["field"] = int(name_parts[0])
        new["year"] = int(name_parts[1])
        df.append(new)
        print_progress(idx+1, total)
    df = pd.concat(df)
    print(">>> Optimizing dtypes")
    for c in ("year", "field"):
        df[c] = df[c].astype("uint32")
    print(">>> Reading done")
    return df


def main():
    # Read articles list
    cols = ["author_count", "countries", "source_id", "eid", "author"]
    dtypes = {"author_count": "uint8", "author": "uint64", "source_id": "uint64"}
    df = read_source_files(cols, dtype=dtypes)
    print(">>> Computing paper status")
    df["countries"] = df["countries"].str.split("-")
    df["multiaff"] = (df["countries"].str.len() > 1).astype("uint32")
    df["foreignaff"] = (df["countries"].apply(set).str.len() > 1).astype("uint32")
    df["countries"] = df["countries"].str[0].astype("category")
    df = df.rename(columns={"countries": "country"})
    df = df.sort_values("multiaff", ascending=False)
    dedup = df.drop_duplicates(["author", "eid"])
    n_ma_obs = dedup["multiaff"].sum()
    n_fa_obs = dedup["foreignaff"].sum()
    print(f">>> Found {n_ma_obs:,} author-article obs. with MA "
          f"({n_ma_obs/dedup.shape[0]:.2%} of all), of which {n_fa_obs:,} "
          f"({n_fa_obs/n_ma_obs:.2%}) contain a foreign affiliation")
    del dedup
    stats = {"N_of_authors_unique": df["author"].nunique(),
             "N_of_articles_unique": df['eid'].nunique()}

    # LaTeX table on papers and authors by country
    grouped = df.groupby(["country"]).agg(
        Articles=pd.NamedAgg(column='eid', aggfunc=count_unique),
        Authors=pd.NamedAgg(column='author', aggfunc=count_unique))
    cols = grouped.columns
    mult_cols = [(c, "Unique") for c in cols]
    grouped.columns = pd.MultiIndex.from_tuples(mult_cols)
    for c in cols:
        label = (c, "Unique")
        total = grouped[label].sum()
        grouped[(c, "Share (in %)")] = round(grouped[label] / total * 100, 2)
    grouped.index.name = "Country"
    grouped[("Authors", "Unique")] = grouped[("Authors", "Unique")].astype(int)
    grouped = grouped[sorted(grouped.columns, key=lambda t: t[0])]
    fname = OUTPUT_FOLDER + "Tables/articlesauthors_country.tex"
    formatters = {('Articles', 'Unique'): lambda x: f"{x:,}",
                  ('Authors', 'Unique'): lambda x: f"{x:,}"}
    grouped.to_latex(fname, formatters=formatters, multicolumn_format='c',
                     float_format=lambda x: f"{x:,.2f}", index_names=False)
    del grouped

    # Create table on share of MA articles by field over time
    print(">>> Table articles by field")
    fname = OUTPUT_FOLDER + "Tables/multiaff_articles_share-field.tex"
    make_articles_shares_table(df, fname, byvar="field")

    # Compute some aggregates
    paper = (df.groupby(["year", "eid"])["author_count", "multiaff"].max()
               .reset_index().drop("eid", axis=1))
    df = df.drop("author_count", axis=1)
    print(">>> Correlation group size and MA author incidence: "
          f"{paper[['author_count', 'multiaff']].corr().iloc[1, 0]:.2}")
    print(">>> Share articles overall with MA author(s): "
          f"{paper['multiaff'].sum()/paper.shape[0]:.2%}")
    totals = paper["year"].value_counts()
    counts = paper.groupby("year")[["multiaff"]].sum()["multiaff"]
    print(">>> Share of articles w/ MA author by year")
    print((counts/totals*100).round(4))
    del counts, totals, paper

    # Observation is author-octile-year
    print(">>> File byquality")
    jour = pd.concat([pd.read_csv(f, usecols=["Sourceid", "octile"]) for f in
                      glob(JOURNAL_FOLDER + "[0-9][0-9].csv")])
    jour = (jour.sort_values("octile", ascending=False)
                .drop_duplicates(["Sourceid"]))
    quality = (df.merge(jour, "inner", left_on="source_id", right_on="Sourceid")
                 .drop(["field", "Sourceid", "source_id", "country", "eid"], axis=1)
                 .sort_values(["octile", "multiaff"], ascending=False))
    del jour
    byquality = aggregate(quality, ["octile"])
    del quality
    oct_labels = {8: "Top", 7: "Second", 6: "Third", 5: "Fourth"}
    byquality["octile"] = byquality["octile"].replace(oct_labels)
    byquality = byquality.rename(columns={"octile": "Journal quality group"})
    fname = TARGET_FOLDER + "byquality.csv"
    byquality.to_csv(fname, float_format='%g', index=False, encoding="utf8")
    stats["N_of_authoroctileyear"] = byquality["n_authors"].sum()
    del byquality

    # Observation is author-country-year
    print(">>> File bycountry")
    bycountry = aggregate(df, ["country"])
    fname = TARGET_FOLDER + "bycountry.csv"
    bycountry.to_csv(fname, float_format='%g', index=False, encoding="utf8")
    stats["N_of_authorcountryyear"] = bycountry["n_authors"].sum()
    del bycountry

    # Observation is author-countryfield-year
    print(">>> File bycountryfield")
    df["field"] = df["field"].replace(_asjc_map)
    bycountryfield = aggregate(df, ["country", "field"])
    fname = TARGET_FOLDER + "bycountryfield.csv"
    bycountryfield.to_csv(fname, float_format='%g', index=False, encoding="utf8")
    stats["N_of_authorcountryfieldyear"] = bycountryfield["n_authors"].sum()
    del bycountryfield

    # Observation is author-field-year
    print(">>> File byfield")
    byfield = aggregate(df, ["field"], totals=True)
    byfield = byfield.sort_values(["field", "year"])
    fname = TARGET_FOLDER + "byfield.csv"
    byfield.to_csv(fname, float_format='%g', index=False, encoding="utf8")
    mask = byfield["field"] != "All"
    stats["N_of_authorfieldyear"] = byfield.loc[mask, "n_authors"].sum()
    del byfield

    # Write statistics
    print(">>> No. of observations:", stats)
    write_stats(stats)


if __name__ == '__main__':
    main()
