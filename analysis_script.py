import pandas as pd
import numpy as np
from scipy import stats
import sys

sys.stdout = open('results.txt', 'w')

df = pd.read_excel('SurveyResponses.xlsx', header=0, skiprows=[1])

# ── Encode ordinal variables ──────────────────────────────────────────────────

prog_map = {
    'No programming experience': 1,
    'Completed one introductory programming course': 2,
    'Completed two or more programming courses': 3,
    'Regular personal or professional programming use': 4,
}

pharma_map = {
    'No exposure to this subject': 0,
    'General awareness (e.g., taking medications, reading labels)': 1,
    'Some formal coursework (one or two relevant courses)': 2,
    'Substantial coursework or independent study': 3,
    'Clinical experience or advanced study in pharmacology/medicine': 4,
}

chem_map = {
    'No exposure to this subject': 0,
    'General awareness (e.g., high school chemistry)': 1,
    'Some formal coursework (one or two relevant courses)': 2,
    'Substantial coursework or independent study': 3,
    'Research experience or advanced study in chemistry': 4,
}

finance_map = {
    'No exposure to this subject': 0,
    'General awareness (e.g., personal budgeting or everyday use)': 1,
    'Some formal coursework (one or two relevant courses)': 2,
    'Substantial coursework or independent study': 3,
    'Professional experience or advanced study in finance/accounting': 4,
}

df['prog_score']    = df['Q1'].map(prog_map)
df['pharma_score']  = df['Q9'].map(pharma_map)
df['chem_score']    = df['Q10'].map(chem_map)
df['finance_score'] = df['Q11'].map(finance_map)

computing_majors    = ['Computer Science / Software Engineering', 'Other (Computing Related)']
non_computing_mask  = ~df['Q2'].isin(computing_majors)
computing_mask      =  df['Q2'].isin(computing_majors)

# ── Figure 1: Participant disciplines and areas of study ──────────────────────

print("=" * 60)
print("FIGURE 1: Participant Disciplines and Areas of Study")
print("=" * 60)

discipline_counts = df['Q2'].value_counts().reset_index()
discipline_counts.columns = ['Major / Discipline', 'Count']
discipline_counts['Group'] = discipline_counts['Major / Discipline'].apply(
    lambda x: 'Computing' if x in computing_majors else 'Non-Computing'
)
discipline_counts = discipline_counts[['Group', 'Major / Discipline', 'Count']]
discipline_counts = discipline_counts.sort_values(['Group', 'Count'], ascending=[True, False])

print(discipline_counts.to_string(index=False))
print(f"\nTotal participants : {len(df)}")
print(f"Computing group    : {computing_mask.sum()}")
print(f"Non-computing group: {non_computing_mask.sum()}")

# ── Figure 2: Self-reported domain expertise by group ─────────────────────────

familiarity_labels = {
    0: '0 - No exposure',
    1: '1 - General awareness',
    2: '2 - Some formal coursework',
    3: '3 - Substantial coursework',
    4: '4 - Advanced/professional',
}

domain_cols = {
    'Pharmacology': 'pharma_score',
    'Chemistry':    'chem_score',
    'Finance':      'finance_score',
}

for group_label, mask in [('Non-Computing', non_computing_mask), ('Computing', computing_mask)]:
    print("\n" + "=" * 60)
    print(f"FIGURE 2: Self-Reported Domain Expertise -- {group_label} Participants (n={mask.sum()})")
    print("=" * 60)

    rows = []
    for domain, col in domain_cols.items():
        counts = df.loc[mask, col].value_counts().sort_index()
        for score, label in familiarity_labels.items():
            rows.append({
                'Domain':             domain,
                'Familiarity Level':  label,
                'Count':              int(counts.get(score, 0)),
            })

    expertise_df = pd.DataFrame(rows)
    expertise_df = expertise_df[expertise_df['Count'] > 0]
    print(expertise_df.to_string(index=False))

# ── Domain eligibility check (all domains) ───────────────────────────────────
# In the survey, participants who rated their familiarity as "General awareness"
# or below (score <= 1) were not presented with that domain's comprehension
# tasks at all. A domain is only included in Analysis 1 if at least one
# non-computing participant rated their familiarity above general awareness
# (score >= 2), meaning they were actually shown and completed those tasks.

domains = {
    'Pharmacology': ('pharma_score', 'SC1'),
    'Chemistry':    ('chem_score',   'SC2'),
    'Finance':      ('finance_score','SC4'),
}

THRESHOLD = 2  # "Some formal coursework" — minimum to receive domain tasks

print("=" * 60)
print("DOMAIN ELIGIBILITY CHECK (non-computing participants)")
print("Threshold: familiarity score >= 2 (some formal coursework)")
print("=" * 60)

included_domains = {}
for domain, (fam_col, score_col) in domains.items():
    eligible_count = (df.loc[non_computing_mask, fam_col] >= THRESHOLD).sum()
    if eligible_count > 0:
        included_domains[domain] = (fam_col, score_col)
        print(f"{domain:<15}: {eligible_count} non-computing participant(s) met threshold  --> included")
    else:
        print(f"{domain:<15}: 0 non-computing participants met threshold  --> excluded (no participants received this domain's tasks)")

# ── Analysis 1: Spearman Correlation ─────────────────────────────────────────
# Domain familiarity score vs. comprehension accuracy per domain
# Only domains that passed the variance check are analysed.

print("\n" + "=" * 60)
print("ANALYSIS 1: Spearman Correlation")
print("Domain familiarity vs. comprehension accuracy")
print("=" * 60)

for domain, (fam_col, score_col) in included_domains.items():
    r, p = stats.spearmanr(df[fam_col], df[score_col], nan_policy='omit')
    print(f"{domain:<15}: r = {r:.3f},  p = {p:.3f}")

excluded = [d for d in domains if d not in included_domains]
for domain in excluded:
    print(f"{domain:<15}: excluded (no variance in non-computing familiarity scores)")

# ── Analysis 2: Mann-Whitney U ────────────────────────────────────────────────
# High-domain / low-programming vs. low-domain / high-programming
# Only domains that passed the eligibility check in Analysis 1 are included,
# plus the computing domain as the shared baseline reference.
# Participants with all-blank question responses for a domain are excluded
# as they were not routed to that domain's tasks by the survey instrument.

print("\n" + "=" * 60)
print("ANALYSIS 2: Mann-Whitney U")
print("CS group vs. Domain group -- per-domain comprehension score")
print("(Only eligibility-checked domains + computing baseline)")
print("(Participants not routed to a domain are excluded per domain)")
print("=" * 60)

domain_mask = df['Q2'].isin(['Pre-Medicine / Nursing', 'Chemistry / Biochemistry'])

# Domain question columns — used to detect routing
domain_question_cols = {
   'Pharmacology': [c for c in df.columns if c.startswith('A') and '-Q' in c],
   'Chemistry':    [c for c in df.columns if c.startswith('B') and '-Q' in c],
   'Finance':      [c for c in df.columns if c.startswith('D') and '-Q' in c],
   'Computing':    [c for c in df.columns if c.startswith('C') and '-Q' in c],
}

# Score columns per domain
domain_score_cols = {domain: cols[1] for domain, cols in included_domains.items()}
domain_score_cols['Computing'] = 'SC3'

analysis2_domains = {**{d: domain_score_cols[d] for d in included_domains}, 'Computing': 'SC3'}

for domain, score_col in analysis2_domains.items():
   q_cols = domain_question_cols[domain]

   # A participant was routed if at least one question in the domain is non-blank
   routed_mask = df[q_cols].notna().any(axis=1)

   # Compare CS group vs ALL non-computing participants for every domain.
   comparison_mask = non_computing_mask
   group_label     = 'Non-CS group  '

   cs_scores         = df.loc[computing_mask   & routed_mask, score_col].dropna()
   comparison_scores = df.loc[comparison_mask  & routed_mask, score_col].dropna()

   print(f"\n{domain}")
   print(f"  CS group      (n={len(cs_scores)}): {cs_scores.values}")
   print(f"  {group_label}(n={len(comparison_scores)}): {comparison_scores.values}")

   if len(cs_scores) > 0 and len(comparison_scores) > 0:
       stat, p = stats.mannwhitneyu(cs_scores, comparison_scores, alternative='two-sided')
       print(f"  Mann-Whitney U = {stat:.1f},  p = {p:.3f}")
   else:
       print("  Insufficient data for test")

excluded_a2 = [d for d in ['Pharmacology', 'Chemistry', 'Finance'] if d not in included_domains]
for domain in excluded_a2:
    print(f"\n{domain}: excluded (did not pass eligibility check)")

# ── Analysis 3: Multiple Linear Regression ───────────────────────────────────
# Predictors: domain familiarity + programming experience
# Outcome: pharmacology comprehension score (SC1)

print("\n" + "=" * 60)
print("ANALYSIS 3: Multiple Linear Regression")
print("Predictors: domain familiarity + programming experience")
print("Outcome: pharmacology comprehension score (SC1)")
print("(Participants not routed to pharmacology tasks excluded)")
print("=" * 60)
 
pharma_routed_mask = df[domain_question_cols['Pharmacology']].notna().any(axis=1)
sub = df.loc[pharma_routed_mask, ['pharma_score', 'prog_score', 'SC1']].dropna()
n = len(sub)
print(f"n = {n}")
 
X = sub[['pharma_score', 'prog_score']].values
y = sub['SC1'].values
X_aug = np.column_stack([np.ones(n), X])
p = X_aug.shape[1]          # number of parameters (intercept + 2 predictors)

# ── OLS coefficients ──────────────────────────────────────────────────────────
coeffs, _, _, _ = np.linalg.lstsq(X_aug, y, rcond=None)

# ── Model fit ─────────────────────────────────────────────────────────────────
y_hat   = X_aug @ coeffs
resid   = y - y_hat
RSS = float(resid @ resid)                          # residual sum of squares
TSS = float(((y - y.mean()) ** 2).sum())            # total sum of squares
R2 = 1 - RSS / TSS
R2_adj = 1 - (RSS / (n - p)) / (TSS / (n - 1))        # adjusted R²
F_stat = (R2 / (p - 1)) / ((1 - R2) / (n - p))        # overall F-statistic
F_p = 1 - stats.f.cdf(F_stat, p - 1, n - p)

# ── Coefficient standard errors & t-tests ────────────────────────────────────
s2 = RSS / (n - p)                                 # mean squared error
cov = s2 * np.linalg.inv(X_aug.T @ X_aug)          # covariance matrix
se = np.sqrt(np.diag(cov))                         # standard errors
t_stats = coeffs / se
p_vals = 2 * (1 - stats.t.cdf(np.abs(t_stats), df=n - p))

labels  = ['Intercept', 'Domain familiarity', 'Programming experience']

# ── Print coefficient table ───────────────────────────────────────────────────
print(f"\n{'Predictor':<25} {'Coeff':>8} {'SE':>8} {'t':>8} {'p':>8}")
print("-" * 61)
for lbl, coef, s, t, pv in zip(labels, coeffs, se, t_stats, p_vals):
   sig = " *" if pv < 0.05 else ("  ." if pv < 0.10 else "")
   print(f"{lbl:<25} {coef:>8.3f} {s:>8.3f} {t:>8.3f} {pv:>8.3f}{sig}")

# ── Print model fit summary ───────────────────────────────────────────────────
print(f"\nR-squared              : {R2:.3f}")
print(f"Adjusted R-squared     : {R2_adj:.3f}")
print(f"F-statistic     : {F_stat:.3f}  (df1={p-1}, df2={n-p})")
print(f"F p-value       : {F_p:.3f}")

sys.stdout.close()
sys.stdout = sys.__stdout__
print("Results written to results.txt")
