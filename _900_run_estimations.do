clear all
cap log close
log using ./990_output/estimations.log, replace

cap graph drop _all
set maxvar 50000
set matsize 11000

use ./200_regression_master/master.dta
merge m:m source_id using ".\009_Stata_rankings\sjr_complete.dta"
drop if _merge == 2
drop _merge
replace sjr = subinstr(sjr, ",", ".", .)
destring sjr, replace
replace sjr = 0 if sjr == .
gen lnauthor_count = ln(author_count)

**********************
* Publication-based analysis
**********************

** Japan onset in 2002
reg multiaff EI_Japan##t02 lnauthor_count i.aggr_id i.field i.year sjr if year < 2012 & (aggregation == "Japan" | EI == 0), cluster(aggr_id)
est store Japan_short
bys EI: tab aggregation if e(sample)

reg multiaff EI_Japan##t02 lnauthor_count i.aggr_id i.field i.year sjr if aggregation == "Japan" | EI == 0, cluster(aggr_id)
est store Japan_reg
bys EI: tab aggregation if e(sample)

reg multiaff EI_Japan##i.year lnauthor_count i.aggr_id i.field sjr if (aggregation == "Japan" | EI == 0) & year < 2002, cluster(aggr_id)
testparm EI_Japan#i.year

** China onset in 2002
reg multiaff EI_China##t02 lnauthor_count i.aggr_id i.field i.year sjr if year < 2012 & (aggregation == "China" | EI == 0), cluster(aggr_id)
est store China_short
bys EI: tab aggregation if e(sample)

reg multiaff EI_China##t02 lnauthor_count i.aggr_id i.field  i.year sjr if aggregation == "China" | EI == 0, cluster(aggr_id)
est store China_reg
bys EI: tab aggregation if e(sample)

reg multiaff EI_China##i.year lnauthor_count i.aggr_id i.field sjr if (aggregation == "China" | EI == 0) & year < 2002, cluster(aggr_id)
testparm EI_China#i.year

** Norway onset in 2003
reg multiaff EI_Norway##t03 lnauthor_count i.aggr_id i.field i.year sjr if year < 2013 & (aggregation == "Norway" | EI == 0), cluster(aggr_id)
est store Norway_short
bys EI: tab aggregation if e(sample)

reg multiaff EI_Norway##t03 lnauthor_count i.aggr_id i.field i.year sjr if aggregation == "Norway" | EI == 0, cluster(aggr_id)
est store Norway_reg
bys EI: tab aggregation if e(sample)

reg multiaff EI_Norway##i.year lnauthor_count i.aggr_id i.field sjr if (aggregation == "Norway" | EI == 0) & year < 2003, cluster(aggr_id)
testparm EI_Norway#i.year

** Australia onset in 2003
reg multiaff EI_Australia##t03 lnauthor_count i.aggr_id i.field i.year sjr  if year < 2013 & (aggregation == "Australia" | EI == 0), cluster(aggr_id)
est store Australia_short
bys EI: tab aggregation if e(sample)

reg multiaff EI_Australia##t03 lnauthor_count i.aggr_id i.field  i.year sjr if aggregation == "Australia" | EI == 0, cluster(aggr_id)
est store Australia_reg
bys EI: tab aggregation if e(sample)

reg multiaff EI_Australia##i.year lnauthor_count i.aggr_id i.field sjr if (aggregation == "Australia" | EI == 0) & year < 2003, cluster(aggr_id)
testparm EI_Australia#i.year

** South Korea onset in 2004
reg multiaff EI_SouthKorea##t04 lnauthor_count i.aggr_id i.field i.year sjr if year < 2014 & (aggregation == "SouthKorea" | EI == 0), cluster(aggr_id)
est store SouthKorea_short
bys EI: tab aggregation if e(sample)

reg multiaff EI_SouthKorea##t04 lnauthor_count i.aggr_id i.field i.year sjr if aggregation == "SouthKorea" | EI == 0, cluster(aggr_id)
est store SouthKorea_reg
bys EI: tab aggregation if e(sample)

reg multiaff EI_SouthKorea##i.year lnauthor_count i.aggr_id i.field sjr if (aggregation == "SouthKorea" | EI == 0) & year < 2004, cluster(aggr_id)
testparm EI_SouthKorea#i.year

** Russia onset in 2005
reg multiaff EI_Russia##t05 lnauthor_count i.aggr_id i.field i.year sjr if year < 2015 & (aggregation == "Russia" | EI == 0), cluster(aggr_id)
est store Russia_short
bys EI: tab aggregation if e(sample)

reg multiaff EI_Russia##t05 lnauthor_count i.aggr_id i.field i.year sjr if aggregation == "Russia" | EI == 0, cluster(aggr_id)
est store Russia_reg
bys EI: tab aggregation if e(sample)

reg multiaff EI_Russia##i.year lnauthor_count i.aggr_id i.field sjr if (aggregation == "Russia" | EI == 0) & year < 2005, cluster(aggr_id)
testparm EI_Russia#i.year

** Germany onset in 2006
reg multiaff EI_Germany##t06 lnauthor_count i.aggr_id i.field i.year sjr if year < 2016 & (aggregation == "Germany" | EI == 0), cluster(aggr_id)
est store Germany_short
bys EI: tab aggregation if e(sample)

reg multiaff EI_Germany##t06 lnauthor_count i.aggr_id i.field i.year sjr if aggregation == "Germany" | EI == 0, cluster(aggr_id)
est store Germany_reg
bys EI: tab aggregation if e(sample)

reg multiaff EI_Germany##i.year author_count i.aggr_id i.field sjr if (aggregation == "Germany" | EI == 0) & year < 2006, cluster(aggr_id)
testparm EI_Germany#i.year

** Singapore onset in 2006
reg multiaff EI_Singapore##t06 lnauthor_count i.aggr_id i.field i.year sjr if year < 2016 & (aggregation == "Singapore" | EI == 0), cluster(aggr_id)
est store Singapore_short
bys EI: tab aggregation if e(sample)

reg multiaff EI_Singapore##t06 lnauthor_count i.aggr_id i.field i.year sjr if aggregation == "Singapore" | EI == 0, cluster(aggr_id)
est store Singapore_reg
bys EI: tab aggregation if e(sample)

reg multiaff EI_Singapore##i.year author_count i.aggr_id i.field sjr if (aggregation == "Singapore" | EI == 0) & year < 2006, cluster(aggr_id)
testparm EI_Singapore#i.year

** Taiwan onset in 2006
reg multiaff EI_Taiwan##t06 lnauthor_count i.aggr_id i.field i.year sjr if year < 2016 & (aggregation == "Taiwan" | EI == 0), cluster(aggr_id)
est store Taiwan_short
bys EI: tab aggregation if e(sample)

reg multiaff EI_Taiwan##t06 lnauthor_count i.aggr_id i.field i.year sjr if aggregation == "Taiwan" | EI == 0, cluster(aggr_id)
est store Taiwan_reg
bys EI: tab aggregation if e(sample)

reg multiaff EI_Taiwan##i.year author_count i.aggr_id i.field sjr if (aggregation == "Taiwan" | EI == 0) & year < 2006, cluster(aggr_id)
testparm EI_Taiwan#i.year

** Denmark onset in 2008
reg multiaff EI_Denmark##t08 lnauthor_count i.aggr_id i.field i.year sjr if aggregation == "Denmark" | EI == 0, cluster(aggr_id)
est store Denmark_reg
bys EI: tab aggregation if e(sample)

reg multiaff EI_Denmark##i.year lnauthor_count i.aggr_id i.field sjr if (aggregation == "Denmark" | EI == 0) & year < 2008, cluster(aggr_id)
testparm EI_Denmark#i.year	

** France: onset EI in 2008
reg multiaff EI_France##t08 lnauthor_count i.aggr_id i.field i.year sjr if aggregation == "France" | EI == 0, cluster(aggr_id)
est store France_reg
bys EI: tab aggregation if e(sample)

reg multiaff EI_France##i.year lnauthor_count i.aggr_id i.field sjr if (aggregation == "France" | EI == 0) & year < 2008, cluster(aggr_id)
testparm EI_France#i.year	

** UK onset in 2008
reg multiaff EI_UnitedKingdom##t08 lnauthor_count i.aggr_id i.field i.year sjr if aggregation == "UnitedKingdom" | EI == 0, cluster(aggr_id)
est store UnitedKingdom_reg
bys EI: tab aggregation if e(sample)

reg multiaff EI_UnitedKingdom##i.year lnauthor_count i.aggr_id i.field sjr if (aggregation == "UnitedKingdom" | EI == 0) & year < 2008, cluster(aggr_id)
testparm EI_UnitedKingdom#i.year	

** Italy onset in 2008
reg multiaff EI_Italy##t08 lnauthor_count i.aggr_id i.field sjr if aggregation == "Italy" | EI == 0, cluster(aggr_id)
est store Italy_reg
bys EI: tab aggregation if e(sample)

reg multiaff EI_Italy##i.year lnauthor_count i.aggr_id i.field sjr if (aggregation == "Italy" | EI == 0) & year < 2008, cluster(aggr_id)
testparm EI_Italy#i.year	

** Spain onset in 2009
reg multiaff EI_Spain##t09 lnauthor_count i.aggr_id i.field i.year sjr if aggregation == "Spain" | EI == 0, cluster(aggr_id)
est store Spain_reg
bys EI: tab aggregation if e(sample)
			
reg multiaff EI_Spain##i.year lnauthor_count i.aggr_id i.field sjr if (aggregation == "Spain" | EI == 0) & year < 2009, cluster(aggr_id)
testparm EI_Spain#i.year	

** Israel onset in 2010
reg multiaff EI_Israel##t10 lnauthor_count i.aggr_id i.field i.year sjr if aggregation == "Israel" | EI == 0, cluster(aggr_id)
est store Israel_reg
bys EI: tab aggregation if e(sample)
			
reg multiaff EI_Israel##i.year lnauthor_count i.aggr_id i.field sjr if (aggregation == "Israel" | EI == 0) & year < 2010, cluster(aggr_id)
testparm EI_Israel#i.year

** Poland onset in 2012
reg multiaff EI_Poland##t12 lnauthor_count i.aggr_id i.field i.year sjr if aggregation == "Poland" | EI == 0, cluster(aggr_id)
est store Poland_reg
bys EI: tab aggregation if e(sample)
			
reg multiaff EI_Poland##c.year lnauthor_count i.aggr_id i.field sjr if (aggregation == "Poland" | EI == 0) & year < 2012, cluster(aggr_id)
testparm EI_Poland#c.year

** Canada onset in 2014
reg multiaff EI_Canada##t14 lnauthor_count i.aggr_id i.field i.year sjr if aggregation == "Canada" | EI == 0, cluster(aggr_id)
est store Canada_reg
bys EI: tab aggregation if e(sample)

reg multiaff EI_Canada##i.year lnauthor_count i.aggr_id i.field sjr if (aggregation == "Canada" | EI == 0) & year < 2014, cluster(aggr_id)
testparm EI_Canada#i.year

** Write out
esttab Japan_short China_short Norway_short Australia_short SouthKorea_short Russia_short Germany_short Singapore_short Taiwan_short ///
	using ".\990_output\Tables\ols_exin-short.tex", ar2 b(3) p(2) r2(3) compress replace
esttab Japan_reg China_reg Norway_reg Australia_reg SouthKorea_reg Russia_reg Germany_reg Singapore_reg Taiwan_reg ///
	using ".\990_output\Tables\ols_exin1.tex", ar2 b(3) p(2) r2(3) compress replace
esttab Denmark_reg France_reg UnitedKingdom_reg Singapore_reg Italy_reg Spain_reg Israel_reg Poland_reg Canada_reg  ///
	using ".\990_output\Tables\ols_exin2.tex", ar2 b(3) p(2) r2(3) compress replace

log close
exit

**********************
* Country analysis
**********************

preserve
collapse (max) EI (mean) multiaff lnauthor_count sjr, by(aggr_id year)
reg multiaff EI##c.year, robust
margins EI, at(year=(1996(2)2019))
marginsplot
restore

preserve
keep if aggregation == "Germany" | EI == 0
collapse (max) EI (mean) meanmultiaff=multiaff (sd) sdmultiaff=multiaff, by(aggr_id year)
gen lb=mean-sd
gen ub=mean+sd
sort EI
twoway line meanmultiaff year if EI || line ub lb year if ~EI, xline(2005, lwidth(5pt) lcolor(grey)) scheme(plottig) bgcolor(white) graphregion(color(white))
reg multiaff i.EI##i.year i.aggr_id i.field, rob
margins EI, at(year=(1996(2)2019))
marginsplot
restore



preserve
collapse (mean) multiaff author_count EI_* t* EI, by(aggregation year field)
reg multiaff EI_Poland##t12 author_count i.aggr_id i.field i.year if aggregation == "Poland" | EI == 0, cluster(aggr_id)
restore


/*
local texfile = "\\nas.ads.mwn.de\ga85fac\TUM-PC\Dokumente\GitHub\multiaff\990_output\Tables\results.tex"
local stars = "* 0.1 ** 0.05 *** 0.01"

esttab using `texfile', replace label se(%4.3f) b(3) star(`stars') delimiter(_tab "&") ///
    noconstant booktabs alignment(S) substitute("\_" "_") varwidth(70) ///
    mlabels(, depvars lhs("Dependent variable") p("{") s("}")) ///
    indicate("Field fixed effects = *.field" "Year fixed effects = *.year" "Country fixed effects =  *.aggr_id", labels({Yes} {No}))
*/
