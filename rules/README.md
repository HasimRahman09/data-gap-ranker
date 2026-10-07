# Not-applicable rules
`malaria_free.csv`: countries (47) and one territory (Réunion) certified malaria-free by WHO, with
certification year. Transcribed by eye from the official WHO map "Countries and territories
certified malaria-free by WHO", data source WHO, map updated 15 July 2025
(https://www.who.int/teams/global-malaria-programme/elimination/countries-and-territories-certified-malaria-free-by-who;
PDF: https://cdn.who.int/media/docs/default-source/malaria/elimination/countries-territories-certified-malaria-free-by-who.pdf).
Names are WHO's own labels. Not an official UN or WHO product; WHO's map notes dotted lines are approximate borders.
Rule (proposed, not yet applied): slice SH_STA_MALR (malaria incidence per 1,000 population at risk)
is NOT_APPLICABLE for a country in every year >= its certification year in which no value is reported.

## Considered, not adopted: neglected tropical diseases (SH_TRP_INTVN)
Series is "Number of people requiring interventions against NTDs", source WHO GHO, footnote
"Aggregation across diseases". Two findings from the cached data (2026-10-07):
- Areas where no NTD needs intervention report a value of 0 (43 areas, e.g. Canada, Finland,
  New Zealand), so for them the cell is PRESENT, not missing. Absence therefore means "not
  reported", a real gap.
- WHO's list of countries that eliminated at least one NTD does not make the aggregate not
  applicable: eliminating one disease leaves the others in the sum.
No rule is added. Revisit only if a WHO source states that a given area is exempt from reporting.
