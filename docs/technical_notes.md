# Technical Notes

The main notebook is written for nontechnical users. These notes are for maintainers.

## Supported CAASPP file formats

The parser supports:

- ZIP files containing `.txt` or `.csv` files
- caret-delimited files (`^`)
- comma-delimited files
- common fixed-width ASCII Smarter Balanced research file layouts

The safest file choice for nontechnical users is the delimited version when CAASPP offers it.

## Main helper file

The parsing and export code is in:

```text
src/caaspp_sbs_tools.py
```

The notebook imports this file rather than putting all parsing code into visible notebook cells.

## Output files

The notebook writes:

```text
outputs/{district}_caaspp_wide.csv
outputs/{district}_caaspp_audit_long.csv
outputs/{district}_caaspp_gap_chart_data.csv
outputs/{district}_caaspp_chart_ready_outputs.xlsx
```

## Expected row count

For the default analysis:

```text
6 grades × 2 student groups × 2 subjects = 24 rows per year
```

The audit table should be checked if row counts differ.
