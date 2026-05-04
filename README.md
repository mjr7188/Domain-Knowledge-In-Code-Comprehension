# Domain-Knowledge-In-Code-Comprehension
This README describes every file in this replication package and provides
step-by-step instructions for reproducing all reported results from scratch.

---

## Repository Contents

| File | Description |
|---|---|
| `SurveyResponses.xlsx` | Raw survey data (one row per participant, n=10) |
| `analysis_script.py` | Single end-to-end analysis pipeline (Python) |
| `results.txt` | Expected output — all figures and analyses |
| `README.md` | This file |

---

## Research Context

This study examines whether **domain expertise** or a **CS background**
better predicts comprehension of technical documents across three domains:
Pharmacology, Chemistry, and Finance. Ten participants were split into a
computing group (n=3) and a non-computing group (n=7). Comprehension was
measured via domain-specific question sets embedded in the survey instrument.

---

## Requirements

### Python Version
Python **3.8 or later** is recommended.

### Dependencies
Install all required packages with:

```bash
pip install pandas numpy scipy openpyxl
```

| Package | Purpose |
|---|---|
| `pandas` | Data loading and manipulation |
| `numpy` | Matrix operations (linear regression) |
| `scipy` | Spearman correlation, Mann-Whitney U |
| `openpyxl` | Reading `.xlsx` files |

---

## How to Reproduce Results

### 1. Place all files in the same directory

```
your-folder/
├── SurveyResponses.xlsx
├── analysis_script.py
├── results.txt          ← expected output for comparison
└── README.md
```

### 2. Run the analysis script

```bash
cd your-folder
python analysis_script.py
```

The script writes all output to **`results.txt`**, overwriting any existing
file. A confirmation message is printed to the terminal when complete:

```
Results written to results.txt
```

### 3. Verify output

Diff your newly generated `results.txt` against the provided reference copy:

```bash
diff results.txt results.txt   # replace second arg with your reference copy
```

A clean diff (no output) confirms full numerical reproducibility.

---

## Data File Notes (`SurveyResponses.xlsx`)

- **Row 1** — Column headers (question IDs: `Q1`, `Q2`, `Q9`, `Q10`, `Q11`, etc.)
- **Row 2** — Human-readable question labels *(skipped by the script via `skiprows=[1]`)*
- **Rows 3+** — One participant per row

### Key Columns

| Column | Content |
|---|---|
| `Q1` | Programming experience (text, ordinal-encoded to 1–4) |
| `Q2` | Declared major / discipline |
| `Q9` | Pharmacology familiarity (text, encoded 0–4) |
| `Q10` | Chemistry familiarity (text, encoded 0–4) |
| `Q11` | Finance familiarity (text, encoded 0–4) |
| `SC1` | Pharmacology comprehension score |
| `SC2` | Chemistry comprehension score |
| `SC3` | Computing comprehension score |
| `SC4` | Finance comprehension score |
| `A*-Q*` | Individual Pharmacology question responses |
| `B*-Q*` | Individual Chemistry question responses |
| `C*-Q*` | Individual Computing question responses |
| `D*-Q*` | Individual Finance question responses |

> **Survey routing:** Participants who rated their familiarity at
> *General awareness* or below (score ≤ 1) were not presented with that
> domain's comprehension tasks. The script detects routing by checking
> whether any per-question response column is non-blank.

---

## Analysis Pipeline Overview

The script runs four sequential stages.

### Stage 1 — Ordinal Encoding
Free-text familiarity and programming experience responses are mapped to
integer scales using dictionaries defined at the top of the script.
Group membership (`computing_mask` / `non_computing_mask`) is derived from `Q2`.

### Stage 2 — Domain Eligibility Check
A domain is included in Analyses 1 and 2 only if **at least one
non-computing participant** reported familiarity ≥ 2 (*Some formal
coursework*), meaning they were actually routed to that domain's tasks.

> **Finance** fails this check — all 7 non-computing participants reported
> only *General awareness* (score = 1) — and is excluded from all
> inferential analyses.

### Stage 3 — Analysis 1: Spearman Correlation
Spearman's *r* between domain familiarity score and comprehension score,
computed across **all 10 participants** for each eligible domain.
`scipy.stats.spearmanr` is used with `nan_policy='omit'`.

### Stage 4 — Analysis 2: Mann-Whitney U
Two-sided Mann-Whitney U test comparing comprehension scores between:
- **CS group** — participants in Computing majors
- **Domain group** — participants in Pre-Medicine/Nursing or Chemistry/Biochemistry

Per-domain, only participants who were **routed** to that domain's tasks
are included. The Computing domain is included as a shared baseline.
`scipy.stats.mannwhitneyu` is used with `alternative='two-sided'`.

### Stage 5 — Analysis 3: Multiple Linear Regression
OLS regression predicting Pharmacology comprehension (`SC1`) from
`pharma_score` and `prog_score`, fit via `numpy.linalg.lstsq`.
All 10 participants with complete data are used (n=10).

> **Note:** Standard errors, *p*-values, and R² are not reported for
> this regression due to the small sample size making those values
> unreliable. Coefficients are reported as directional indicators only.

---

## Expected Results Summary

| Analysis | Domain | Result |
|---|---|---|
| Spearman *r* | Pharmacology | r = 0.315, p = 0.375 (n.s.) |
| Spearman *r* | Chemistry | r = −0.262, p = 0.464 (n.s.) |
| Mann-Whitney U | Pharmacology | U = 5.0, p = 1.000 (n.s.) |
| Mann-Whitney U | Chemistry | U = 2.5, p = 1.000 (n.s.) |
| Mann-Whitney U | Computing | U = 11.5, p = 0.069 (marginal) |
| Regression | Pharmacology SC1 | Intercept −3.04, familiarity +2.63, prog +2.47 |

No result reaches conventional significance (α = 0.05). The Computing
domain comparison (p = 0.069) represents the strongest trend but remains
non-significant given the sample size.

---


