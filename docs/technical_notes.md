# Technical Notes

The notebook is intentionally simple for nontechnical users. It creates one CSV output:

```text
OUTPUT_PREFIX_caaspp_sed_nsed_met_above.csv
```

The parser is designed to handle CAASPP Smarter Balanced districtwide **All Student Groups** files across multiple formats:

- ZIP files containing TXT/CSV files
- caret-delimited files
- comma-delimited files
- fixed-width text files when the common CAASPP header is absent

The notebook filters districtwide rows using:

- County Code
- District Code
- School Code `0000000`
- Student Group ID `031` for SED
- Student Group ID `111` for NSED
- Test ID `01` for ELA
- Test ID `02` for Math
- Grades `03`, `04`, `05`, `06`, `08`, and `11` by default

The notebook creates an internal audit table for sanity checks, but the only file downloaded by default is the wide CSV for Google Sheets.
