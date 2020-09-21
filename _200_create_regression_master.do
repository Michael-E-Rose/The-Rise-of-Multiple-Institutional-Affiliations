* Creates master for regression

clear all
cap log close
log using ./200_regression_master/building.log, replace

* READ IN
cap cd ".\100_source_articles"
tempfile building
save `building', emptyok

local myfilelist : dir . files"*.csv"
foreach file of local myfilelist {
	drop _all
	import delimited `"`file'"'
	gen field = ""
	local outfile = subinstr("`file'",".csv","",.)
	local outfile2 = subinstr("`outfile'","-","",.)
	local field = substr("`outfile2'", 10,2)
	replace field = "`field'" if field == ""
	drop affiliations inst_types
	append using "`building'"
	di `field'
	compress
	save `building', replace
}
cd ..

* FORMAT VARIABLES
for var foreign_multiaff multiaff: replace X = 0 if X == .

replace field = subinstr(field,"3-","13",.)
replace field = subinstr(field,"_1","13",.)

destring field, replace

label variable field "scientific field"
label define field 11 "Agri_Bio" 12 "ArtsHumanities" 13 "Bioechm_Gen_Molbio" 14 "Management" 16 "Chemistry" 17 "Computer" 19 "Earth" 20 "Economics" 22 "Engin" 24 "Immunology" 26 "Math" 28 "Neuroscience" 27 "Medicine" 29 "Nursing" 30 "Pharmacology" 31 "Physics" 33 "Social"
label values field field

rename country aggregation
replace aggregation = subinstr(aggregation, " ", "", .)

* EXCELLENCE INITIATIVE MARKER
gen EIonset = .
replace EIonset = 2002 if aggregation == "China"
replace EIonset = 2003 if aggregation == "Australia"
replace EIonset = 2003 if aggregation == "Norway"
replace EIonset = 2004 if aggregation == "SouthKorea"
replace EIonset = 2005 if aggregation == "Taiwan"
replace EIonset = 2006 if aggregation == "Singapore"
replace EIonset = 2006 if aggregation == "Germany"
replace EIonset = 2008 if aggregation == "Denmark"
replace EIonset = 2008 if aggregation == "France"
replace EIonset = 2009 if aggregation == "Spain"
replace EIonset = 2010 if aggregation == "Israel"
replace EIonset = 2010 if aggregation == "Japan"
replace EIonset = 2012 if aggregation == "Poland"
replace EIonset = 2012 if aggregation == "India"
replace EIonset = 2014 if aggregation == "Canada"

egen maxonset = max(EIonset), by(aggregation)
replace EIonset = maxonset if EIonset == .

gen EI = .
replace EI = 1 if EIonset !=.
replace EI = 1 if aggregation == "UnitedKingdom"
replace EI = 1 if aggregation == "Italy"
replace EI = 0 if EI == .
label var EI "country with EI"

gen ei = .
replace ei = 0 if year < EIonset | EIonset == .
replace ei = 1 if year >= EIonset
replace ei = 1 if  aggregation == "UnitedKingdom" & year > 2007
replace ei = 1 if  aggregation == "Italy" & year > 2008
replace ei = 1 if  aggregation == "Canada"
replace EI = 1 if aggregation == "Russia"
label var ei "time varying treatment"

bys EI: tab aggregation
egen aggr_id = group(aggregation)

gen t02 = 1 == year > 2002
gen t03 = 1 == year > 2003
gen t04 = 1 == year > 2004
gen t05 = 1 == year > 2005
gen t06 = 1 == year > 2006
gen t07 = 1 == year > 2007
gen t08 = 1 == year > 2008
gen t09 = 1 == year > 2009
gen t10 = 1 == year > 2010
gen t11 = 1 == year > 2011
gen t12 = 1 == year > 2012
gen t14 = 1 == year > 2014

levelsof aggregation, local(levels)

foreach l of local levels {
	gen EI_`l' = 1 if EI == 1 & aggregation == "`l'"
	replace EI_`l' = 0 if EI_`l' == .
	}

compress
save ./200_regression_master/master.dta, replace
log close
