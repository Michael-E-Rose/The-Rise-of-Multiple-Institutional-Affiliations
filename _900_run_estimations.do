clear all
cap log close
log using ./990_output/estimations.log, replace

cap graph drop _all
set maxvar 50000
set matsize 11000

use ./200_regression_master/master.dta
merge m:m source_id year using ".\009_Stata_rankings\sjr_complete.dta"
drop if _merge == 2
drop _merge _fillin title hindex issn avg_citations
count if sjr == .
gen lnauthor_count = ln(author_count)

*** new version with journal fixed effects


** Japan onset in 2002
areg multiaff EI_Japan##t02 lnauthor_count sjr i.aggr_id i.year if year < 2012 & (aggregation == "Japan" | EI == 0), absorb(source_id) cluster(aggr_id)
est store Japan_short
bys EI: tab aggregation if e(sample)

areg multiaff EI_Japan##t02 lnauthor_count sjr i.aggr_id i.year if aggregation == "Japan" | EI == 0, absorb(source_id) cluster(aggr_id)
est store Japan_reg
bys EI: tab aggregation if e(sample)

areg multiaff EI_Japan##i.year lnauthor_count sjr i.aggr_id if (aggregation == "Japan" | EI == 0) & year < 2002, absorb(source_id) cluster(aggr_id)

** China onset in 2002
areg multiaff EI_China##t02 lnauthor_count sjr i.aggr_id i.year if year < 2012 & (aggregation == "China" | EI == 0), absorb(source_id) cluster(aggr_id)
est store China_short
bys EI: tab aggregation if e(sample)

areg multiaff EI_China##t02 lnauthor_count sjr i.aggr_id i.year if aggregation == "China" | EI == 0, absorb(source_id) cluster(aggr_id)
est store China_reg
bys EI: tab aggregation if e(sample)

areg multiaff EI_China##i.year lnauthor_count sjr i.aggr_id if (aggregation == "China" | EI == 0) & year < 2002, absorb(source_id) cluster(aggr_id)

** Norway onset in 2003
areg multiaff EI_Norway##t03 lnauthor_count sjr i.aggr_id i.year if year < 2013 & (aggregation == "Norway" | EI == 0), absorb(source_id) cluster(aggr_id)
est store Norway_short
bys EI: tab aggregation if e(sample)

areg multiaff EI_Norway##t03 lnauthor_count sjr i.aggr_id i.year if aggregation == "Norway" | EI == 0, absorb(source_id) cluster(aggr_id)
est store Norway_reg
bys EI: tab aggregation if e(sample)

areg multiaff EI_Norway##i.year lnauthor_count sjr i.aggr_id if (aggregation == "Norway" | EI == 0) & year < 2003, absorb(source_id) cluster(aggr_id)

** Australia onset in 2003
areg multiaff EI_Australia##t03 lnauthor_count sjr i.aggr_id i.year  if year < 2013 & (aggregation == "Australia" | EI == 0), absorb(source_id) cluster(aggr_id)
est store Australia_short
bys EI: tab aggregation if e(sample)

areg multiaff EI_Australia##t03 lnauthor_count sjr i.aggr_id  i.year if aggregation == "Australia" | EI == 0, absorb(source_id) cluster(aggr_id)
est store Australia_reg
bys EI: tab aggregation if e(sample)

areg multiaff EI_Australia##i.year lnauthor_count sjr i.aggr_id if (aggregation == "Australia" | EI == 0) & year < 2003, absorb(source_id) cluster(aggr_id)

** South Korea onset in 2004
areg multiaff EI_SouthKorea##t04 lnauthor_count sjr i.aggr_id i.year if year < 2014 & (aggregation == "SouthKorea" | EI == 0), absorb(source_id) cluster(aggr_id)
est store SouthKorea_short
bys EI: tab aggregation if e(sample)

areg multiaff EI_SouthKorea##t04 lnauthor_count sjr i.aggr_id i.year if aggregation == "SouthKorea" | EI == 0, absorb(source_id) cluster(aggr_id)
est store SouthKorea_reg
bys EI: tab aggregation if e(sample)

areg multiaff EI_SouthKorea##i.year lnauthor_count sjr i.aggr_id if (aggregation == "SouthKorea" | EI == 0) & year < 2004, absorb(source_id) cluster(aggr_id)

** Russia onset in 2005
areg multiaff EI_Russia##t05 lnauthor_count sjr i.aggr_id i.year if year < 2015 & (aggregation == "Russia" | EI == 0), absorb(source_id) cluster(aggr_id)
est store Russia_short
bys EI: tab aggregation if e(sample)

areg multiaff EI_Russia##t05 lnauthor_count sjr i.aggr_id i.year if aggregation == "Russia" | EI == 0, absorb(source_id) cluster(aggr_id)
est store Russia_reg
bys EI: tab aggregation if e(sample)

areg multiaff EI_Russia##i.year lnauthor_count sjr i.aggr_id if (aggregation == "Russia" | EI == 0) & year < 2005, absorb(source_id) cluster(aggr_id)

** Germany onset in 2006
areg multiaff EI_Germany##t06 lnauthor_count sjr i.aggr_id i.year if year < 2016 & (aggregation == "Germany" | EI == 0), absorb(source_id) cluster(aggr_id)
est store Germany_short
bys EI: tab aggregation if e(sample)

areg multiaff EI_Germany##t06 lnauthor_count sjr i.aggr_id i.year  if aggregation == "Germany" | EI == 0, absorb(source_id) cluster(aggr_id)
est store Germany_reg
bys EI: tab aggregation if e(sample)

areg multiaff EI_Germany##i.year author_count sjr i.aggr_id if (aggregation == "Germany" | EI == 0) & year < 2006, absorb(source_id) cluster(aggr_id)

** Singapore onset in 2006
areg multiaff EI_Singapore##t06 lnauthor_count sjr i.aggr_id i.year if year < 2016 & (aggregation == "Singapore" | EI == 0), absorb(source_id) cluster(aggr_id)
est store Singapore_short
bys EI: tab aggregation if e(sample)

areg multiaff EI_Singapore##t06 lnauthor_count sjr i.aggr_id i.year if aggregation == "Singapore" | EI == 0, absorb(source_id) cluster(aggr_id)
est store Singapore_reg
bys EI: tab aggregation if e(sample)

areg multiaff EI_Singapore##i.year author_count sjr i.aggr_id if (aggregation == "Singapore" | EI == 0) & year < 2006, absorb(source_id) cluster(aggr_id)

** Taiwan onset in 2006
areg multiaff EI_Taiwan##t06 lnauthor_count sjr i.aggr_id i.year if year < 2016 & (aggregation == "Taiwan" | EI == 0), absorb(source_id) cluster(aggr_id)
est store Taiwan_short
bys EI: tab aggregation if e(sample)

areg multiaff EI_Taiwan##t06 lnauthor_count sjr i.aggr_id i.year if aggregation == "Taiwan" | EI == 0, absorb(source_id) cluster(aggr_id)
est store Taiwan_reg
bys EI: tab aggregation if e(sample)

areg multiaff EI_Taiwan##i.year author_count sjr i.aggr_id if (aggregation == "Taiwan" | EI == 0) & year < 2006, absorb(source_id) cluster(aggr_id)

** Denmark onset in 2008
areg multiaff EI_Denmark##t08 lnauthor_count sjr i.aggr_id i.year if aggregation == "Denmark" | EI == 0, absorb(source_id) cluster(aggr_id)
est store Denmark_reg
bys EI: tab aggregation if e(sample)

areg multiaff EI_Denmark##i.year lnauthor_count sjr i.aggr_id if (aggregation == "Denmark" | EI == 0) & year < 2008, absorb(source_id) cluster(aggr_id)

** France: onset EI in 2008
areg multiaff EI_France##t08 lnauthor_count sjr i.aggr_id i.year if aggregation == "France" | EI == 0, absorb(source_id) cluster(aggr_id)
est store France_reg
bys EI: tab aggregation if e(sample)

areg multiaff EI_France##i.year lnauthor_count sjr i.aggr_id if (aggregation == "France" | EI == 0) & year < 2008, absorb(source_id) cluster(aggr_id)

** UK onset in 2008
areg multiaff EI_UnitedKingdom##t08 lnauthor_count sjr i.aggr_id i.year if aggregation == "UnitedKingdom" | EI == 0, absorb(source_id) cluster(aggr_id)
est store UnitedKingdom_reg
bys EI: tab aggregation if e(sample)

areg multiaff EI_UnitedKingdom##i.year lnauthor_count sjr i.aggr_id if (aggregation == "UnitedKingdom" | EI == 0) & year < 2008, absorb(source_id) cluster(aggr_id)

** Italy onset in 2008
areg multiaff EI_Italy##t08 lnauthor_count sjr i.aggr_id if aggregation == "Italy" | EI == 0, absorb(source_id) cluster(aggr_id)
est store Italy_reg
bys EI: tab aggregation if e(sample)

areg multiaff EI_Italy##i.year lnauthor_count sjr i.aggr_id if (aggregation == "Italy" | EI == 0) & year < 2008, absorb(source_id) cluster(aggr_id)

** Spain onset in 2009
areg multiaff EI_Spain##t09 lnauthor_count sjr i.aggr_id i.year if aggregation == "Spain" | EI == 0, absorb(source_id) cluster(aggr_id)
est store Spain_reg
bys EI: tab aggregation if e(sample)
			
areg multiaff EI_Spain##i.year lnauthor_count sjr i.aggr_id if (aggregation == "Spain" | EI == 0) & year < 2009, absorb(source_id) cluster(aggr_id)

** Israel onset in 2010
areg multiaff EI_Israel##t10 lnauthor_count sjr i.aggr_id i.year if aggregation == "Israel" | EI == 0, absorb(source_id) cluster(aggr_id)
est store Israel_reg
bys EI: tab aggregation if e(sample)
			
areg multiaff EI_Israel##i.year lnauthor_count sjr i.aggr_id if (aggregation == "Israel" | EI == 0) & year < 2010, absorb(source_id) cluster(aggr_id)

** Poland onset in 2012
areg multiaff EI_Poland##t12 lnauthor_count sjr i.aggr_id i.year if aggregation == "Poland" | EI == 0, absorb(source_id) cluster(aggr_id)
est store Poland_reg
bys EI: tab aggregation if e(sample)
			
areg multiaff EI_Poland##c.year lnauthor_count sjr i.aggr_id if (aggregation == "Poland" | EI == 0) & year < 2012, absorb(source_id) cluster(aggr_id)

** Canada onset in 2014
areg multiaff EI_Canada##t14 lnauthor_count sjr i.aggr_id i.year if aggregation == "Canada" | EI == 0, absorb(source_id) cluster(aggr_id)
est store Canada_reg
bys EI: tab aggregation if e(sample)

areg multiaff EI_Canada##i.year lnauthor_count sjr i.aggr_id if (aggregation == "Canada" | EI == 0) & year < 2014, absorb(source_id) cluster(aggr_id)

** Write out
esttab Japan_short China_short Norway_short Australia_short SouthKorea_short Russia_short Germany_short Singapore_short Taiwan_short ///
	using ".\990_output\Tables\ols_exin-short.tex", ar2 b(3) p(2) r2(3) compress replace drop(*aggr_id *year)
esttab Japan_reg China_reg Norway_reg Australia_reg SouthKorea_reg Russia_reg Germany_reg Singapore_reg Taiwan_reg ///
	using ".\990_output\Tables\ols_exin1.tex", ar2 b(3) p(2) r2(3) compress replace drop(*aggr_id *year)
esttab Denmark_reg France_reg UnitedKingdom_reg Singapore_reg Italy_reg Spain_reg Israel_reg Poland_reg Canada_reg  ///
	using ".\990_output\Tables\ols_exin2.tex", ar2 b(3) p(2) r2(3) compress replace drop(*aggr_id *year)
log close
exit

