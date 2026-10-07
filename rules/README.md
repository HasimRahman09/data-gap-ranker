# Not-applicable rules
`malaria_free.csv`: countries (47) and one territory (Réunion) certified malaria-free by WHO, with
certification year. Transcribed by eye from the official WHO map "Countries and territories
certified malaria-free by WHO", data source WHO, map updated 15 July 2025
(https://www.who.int/teams/global-malaria-programme/elimination/countries-and-territories-certified-malaria-free-by-who;
PDF: https://cdn.who.int/media/docs/default-source/malaria/elimination/countries-territories-certified-malaria-free-by-who.pdf).
Names are WHO's own labels. Not an official UN or WHO product; WHO's map notes dotted lines are approximate borders.
Rule (proposed, not yet applied): slice SH_STA_MALR (malaria incidence per 1,000 population at risk)
is NOT_APPLICABLE for a country in every year >= its certification year in which no value is reported.
