* Creates master for regression

clear all
cap log close

* READ IN
cap cd ".\100_source_articles\"

foreach j of numlist 1996/2019 {
	tempfile building`j'
	save `building'`j', emptyok replace
}

foreach j of numlist 1996/2019 {
   	local myfilelist : dir . files "*`j'*.csv"     
	di `j'
	di `myfilelist' 
	foreach file of local myfilelist {
	drop _all
	import delimited `"`file'"'
	drop type 
	gen field = ""
	local outfile = subinstr("`file'",".csv","",.)
	local outfile2 = subinstr("`outfile'","-","",.)
	local field = substr("`outfile2'", 10,2)
	local year = substr("`outfile2'", -6,4)
	replace field = "`field'" if field == ""
	destring field, replace
	gen year = `year'
	gen byte multiaff = (strpos(affiliations, ";") > 0)
	gen aggregation = substr(countries, 1, strpos(countries, "-")-1)
	replace aggregation = countries if aggregation == ""
	di `field'
	drop affiliations countries
	append using "`building'`j'"
	duplicates drop eid author year, force 
	save `building'`j', replace
}
}

tempfile final
save `final', emptyok
use `building'1996, clear
foreach j of numlist 1996/2019 {
    append using "`building'`j'"
	*bys eid author year: replace fieldcount = _n
	*reshape wide field, i(eid author year) j(fieldcount)
	*qui tab field, gen(field_)	
	*collapse (max) field_* (first) aggregation source_id author_count year multiaff, by(eid author)
	*cap drop fieldcount
	duplicates drop eid author year, force 
	save `final', replace
}
	
	

	*tab field, gen(field_)	
	*collapse (max) field_* (first) affiliations aggregation source_id author_count year multiaff, by(eid author)
	
cd ..

label variable field "scientific field"
label define field 11 "Agri_Bio" 12 "ArtsHumanities" 13 "Bioechm_Gen_Molbio" ///
	14 "Management" 15 "ChemEngi" 16 "Chemistry" 17 "Computer" 18 "Decision" ///
	19 "Earth" 20 "Economics" 21 "Energy" 22 "Engin" 23 "Environ" ///
	24 "Immunology" 25 "MatSci" 26 "Math" 27 "Medicine" 28 "Neuroscience" ///
	29 "Nursing" 30 "Pharmacology" 31 "Physics" 33 "Social" 34 "Veterinary" ///
	35 "Dentistry" 36 "Health"
label values field field
 
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
