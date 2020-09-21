* Creates master for regression

clear all 
cap log close

* READ IN
cap cd ".\000_journal_rankings"
tempfile building
save `building', emptyok

local myfilelist : dir . files"*.csv"
foreach file of local myfilelist {
	drop _all
	import delimited `"`file'"'
	drop rank title type issn totaldocs2017 totaldocs3years totalrefs totalcites3years citesdoc2years refdoc country categories
	append using "`building'"
	compress
	save `building', replace
}
cd ..

unique sourceid
rename sourceid source_id
save ../009_Stata_rankings/sjr_complete, replace

