* Creates file with Journal Impact Factors

clear all 
cap log close

import delimited "https://raw.githubusercontent.com/Michael-E-Rose/ScimagoJournalImpactFactors/master/compiled/Scimago_JIFs.csv"
rename sourceid source_id


set obs `=_N+1'
replace year = 1996 if year == .
set obs `=_N+1'
replace year = 1997 if year == .
set obs `=_N+1'
replace year = 1998 if year == .

fillin source_id year

bys source_id: egen max = max(sjr)
replace sjr = max if sjr == . & year > 1998

bys source_id: gen max2 = sjr if year == 1999
bys source_id: egen mmax2 = mean(max) 

replace sjr = mmax2 if sjr == . 

drop *max*

sort source_id year 
duplicates drop source_id year, force
unique source_id year 
save ../009_Stata_rankings/sjr_complete, replace

exit
