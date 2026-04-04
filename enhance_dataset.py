import pandas as pd
import numpy as np

np.random.seed(42)

df = pd.read_csv("Lead Scoring.csv")

# Keep only the useful columns
keep_cols = [
    'Prospect ID', 'Lead Number', 'Lead Origin', 'Lead Source',
    'Do Not Email', 'Do Not Call', 'Converted',
    'TotalVisits', 'Total Time Spent on Website', 'Page Views Per Visit',
    'Last Activity', 'Country', 'City',
    'Asymmetrique Activity Score', 'Asymmetrique Profile Score',
    'Lead Quality', 'Lead Profile', 'Tags',
    'Search', 'Magazine', 'Newspaper', 'Digital Advertisement',
    'Through Recommendations', 'Last Notable Activity'
]

df = df[keep_cols].copy()

n = len(df)

# Normalize activity and profile scores for correlation (0 to 1)
activity = pd.to_numeric(df['Asymmetrique Activity Score'], errors='coerce').fillna(0)
profile  = pd.to_numeric(df['Asymmetrique Profile Score'], errors='coerce').fillna(0)
visits   = pd.to_numeric(df['TotalVisits'], errors='coerce').fillna(0)
time_spent = pd.to_numeric(df['Total Time Spent on Website'], errors='coerce').fillna(0)
converted  = pd.to_numeric(df['Converted'], errors='coerce').fillna(0)

# Normalize to 0-1
def norm(s):
    mn, mx = s.min(), s.max()
    if mx == mn:
        return pd.Series(np.zeros(len(s)))
    return (s - mn) / (mx - mn)

act_n   = norm(activity)
prof_n  = norm(profile)
vis_n   = norm(visits)
time_n  = norm(time_spent)
conv_n  = norm(converted)

# Combined score for correlation
combined = (act_n * 0.3 + prof_n * 0.3 + vis_n * 0.2 + time_n * 0.2)

# ── 1. job_role ────────────────────────────────────────────────────────────────
# Higher combined score → more senior role
roles = ['Analyst', 'Developer', 'Consultant', 'Manager', 'Director', 'Executive']
role_probs = np.column_stack([
    np.clip(0.30 - combined * 0.20, 0.05, 0.40),  # Analyst
    np.clip(0.25 - combined * 0.15, 0.05, 0.35),  # Developer
    np.clip(0.20 - combined * 0.10, 0.05, 0.30),  # Consultant
    np.clip(0.15 + combined * 0.10, 0.05, 0.30),  # Manager
    np.clip(0.07 + combined * 0.15, 0.02, 0.25),  # Director
    np.clip(0.03 + combined * 0.20, 0.01, 0.20),  # Executive
])
role_probs = role_probs / role_probs.sum(axis=1, keepdims=True)
df['job_role'] = [np.random.choice(roles, p=role_probs[i]) for i in range(n)]

# ── 2. years_of_experience ─────────────────────────────────────────────────────
# Correlated with job role and profile score
role_yoe = {'Analyst': (1,5), 'Developer': (2,7), 'Consultant': (3,10),
            'Manager': (5,15), 'Director': (8,18), 'Executive': (12,25)}
yoe = []
for i, role in enumerate(df['job_role']):
    low, high = role_yoe[role]
    boost = int(prof_n.iloc[i] * 5)
    yoe.append(min(np.random.randint(low, high + 1) + boost, 25))
df['years_of_experience'] = yoe

# ── 3. industry ───────────────────────────────────────────────────────────────
industries = ['Technology', 'Finance', 'Healthcare', 'Retail', 'Education', 'Manufacturing']
# Higher activity → Technology/Finance more likely
ind_probs = np.column_stack([
    np.clip(0.15 + act_n * 0.25, 0.10, 0.45),   # Technology
    np.clip(0.15 + prof_n * 0.20, 0.10, 0.40),  # Finance
    np.clip(0.18 - act_n * 0.05, 0.08, 0.25),   # Healthcare
    np.clip(0.20 - prof_n * 0.10, 0.08, 0.28),  # Retail
    np.clip(0.18 - combined * 0.10, 0.05, 0.25),# Education
    np.clip(0.14 - act_n * 0.05, 0.05, 0.22),   # Manufacturing
])
ind_probs = ind_probs / ind_probs.sum(axis=1, keepdims=True)
df['industry'] = [np.random.choice(industries, p=ind_probs[i]) for i in range(n)]

# ── 4. company_size ───────────────────────────────────────────────────────────
sizes = ['Small', 'Medium', 'Large', 'Enterprise']
size_probs = np.column_stack([
    np.clip(0.35 - combined * 0.25, 0.05, 0.50),  # Small
    np.clip(0.30 - combined * 0.10, 0.10, 0.40),  # Medium
    np.clip(0.20 + combined * 0.10, 0.10, 0.35),  # Large
    np.clip(0.15 + combined * 0.25, 0.05, 0.40),  # Enterprise
])
size_probs = size_probs / size_probs.sum(axis=1, keepdims=True)
df['company_size'] = [np.random.choice(sizes, p=size_probs[i]) for i in range(n)]

# ── 5. annual_budget ──────────────────────────────────────────────────────────
budget_rows = []
for i, row in df.iterrows():
    converted = row['Converted']
    size = row['company_size']
    if converted == 1:
        # Converted leads → more likely High budget
        size_budget = {
            'Small':      [0.30, 0.40, 0.30],
            'Medium':     [0.15, 0.35, 0.50],
            'Large':      [0.05, 0.25, 0.70],
            'Enterprise': [0.02, 0.13, 0.85]
        }
    else:
        # Non-converted leads → more likely Low/Medium budget
        size_budget = {
            'Small':      [0.65, 0.25, 0.10],
            'Medium':     [0.45, 0.40, 0.15],
            'Large':      [0.30, 0.45, 0.25],
            'Enterprise': [0.15, 0.45, 0.40]
        }
    budget_rows.append(np.random.choice(['Low', 'Medium', 'High'], p=size_budget[size]))
df['annual_budget'] = budget_rows

# ── 6. decision_maker ─────────────────────────────────────────────────────────
# Directors and Executives are more likely to be decision makers
dm_prob = {'Analyst': 0.05, 'Developer': 0.08, 'Consultant': 0.20,
           'Manager': 0.45, 'Director': 0.75, 'Executive': 0.92}
df['decision_maker'] = [
    'Yes' if np.random.random() < dm_prob[r] else 'No'
    for r in df['job_role']
]


# ── 7. last_contacted_days ────────────────────────────────────────────────────
# Higher activity = contacted more recently
last_days = []
for i in range(n):
    base = int(90 - act_n.iloc[i] * 75)
    noise = np.random.randint(-10, 11)
    last_days.append(max(1, min(90, base + noise)))
df['last_contacted_days'] = last_days

# ── 8. number_of_follow_ups ───────────────────────────────────────────────────
# Higher engagement = more follow ups done
followups = []
for i in range(n):
    base = int(combined.iloc[i] * 8)
    noise = np.random.randint(0, 4)
    followups.append(min(10, base + noise))
df['number_of_follow_ups'] = followups

# ── 9. product_demo_taken ─────────────────────────────────────────────────────
# High combined score + converted → more likely took demo
demo_prob = np.clip(combined * 0.6 + conv_n * 0.3, 0.05, 0.95)
df['product_demo_taken'] = [
    'Yes' if np.random.random() < demo_prob.iloc[i] else 'No'
    for i in range(n)
]

# ── 10. response_time_hours ───────────────────────────────────────────────────
# Higher activity = faster response
resp_hours = []
for i in range(n):
    base = int(72 - act_n.iloc[i] * 60)
    noise = np.random.randint(-5, 11)
    resp_hours.append(max(1, min(72, base + noise)))
df['response_time_hours'] = resp_hours

# ── 11. previous_purchase ─────────────────────────────────────────────────────
# Higher profile score and converted → more likely previous customer
prev_prob = np.clip(prof_n * 0.4 + conv_n * 0.4, 0.03, 0.80)
df['previous_purchase'] = [
    'Yes' if np.random.random() < prev_prob.iloc[i] else 'No'
    for i in range(n)
]

# ── 12. location ──────────────────────────────────────────────────────────────
locations = ['Metro', 'Tier 2', 'Tier 3']
# Higher profile score → more likely Metro
loc_probs = np.column_stack([
    np.clip(0.30 + prof_n * 0.35, 0.15, 0.70),  # Metro
    np.clip(0.40 - prof_n * 0.10, 0.20, 0.50),  # Tier 2
    np.clip(0.30 - prof_n * 0.25, 0.05, 0.40),  # Tier 3
])
loc_probs = loc_probs / loc_probs.sum(axis=1, keepdims=True)
df['location'] = [np.random.choice(locations, p=loc_probs[i]) for i in range(n)]

# ── 13. age_group ─────────────────────────────────────────────────────────────
# Correlated with years of experience
age_groups = ['20-30', '31-40', '41-50', '50+']
age = []
for yoe_val in df['years_of_experience']:
    if yoe_val <= 5:
        probs = [0.70, 0.25, 0.04, 0.01]
    elif yoe_val <= 10:
        probs = [0.20, 0.55, 0.20, 0.05]
    elif yoe_val <= 18:
        probs = [0.05, 0.30, 0.50, 0.15]
    else:
        probs = [0.02, 0.10, 0.40, 0.48]
    age.append(np.random.choice(age_groups, p=probs))
df['age_group'] = age

# ── 14. lead_source_quality ───────────────────────────────────────────────────
sources = ['Referral', 'Organic', 'Paid', 'Cold']
# Higher combined score → better source quality
src_probs = np.column_stack([
    np.clip(0.10 + combined * 0.30, 0.05, 0.45),  # Referral
    np.clip(0.25 + combined * 0.15, 0.10, 0.45),  # Organic
    np.clip(0.35 - combined * 0.10, 0.15, 0.45),  # Paid
    np.clip(0.30 - combined * 0.35, 0.05, 0.40),  # Cold
])
src_probs = src_probs / src_probs.sum(axis=1, keepdims=True)
df['lead_source_quality'] = [np.random.choice(sources, p=src_probs[i]) for i in range(n)]

# ── 15. engagement_trend ──────────────────────────────────────────────────────
trends = ['Increasing', 'Stable', 'Decreasing']
# Higher time spent + visits = increasing trend
trend_probs = np.column_stack([
    np.clip(0.20 + time_n * 0.40 + vis_n * 0.20, 0.05, 0.75),  # Increasing
    np.clip(0.40 - time_n * 0.10, 0.15, 0.55),                  # Stable
    np.clip(0.40 - time_n * 0.30 - vis_n * 0.20, 0.05, 0.55),  # Decreasing
])
trend_probs = trend_probs / trend_probs.sum(axis=1, keepdims=True)
df['engagement_trend'] = [np.random.choice(trends, p=trend_probs[i]) for i in range(n)]

# ── Save ──────────────────────────────────────────────────────────────────────
df.to_csv("Lead_Scoring_Enhanced.csv", index=False)

print(f"Done! Enhanced dataset saved as Lead_Scoring_Enhanced.csv")
print(f"Total rows: {len(df)}")
print(f"Total columns: {len(df.columns)}")
print(f"\nNew columns added:")
new_cols = ['job_role', 'years_of_experience', 'industry', 'company_size',
            'annual_budget', 'decision_maker', 'last_contacted_days',
            'number_of_follow_ups', 'product_demo_taken', 'response_time_hours',
            'previous_purchase', 'location', 'age_group',
            'lead_source_quality', 'engagement_trend']
for col in new_cols:
    print(f"  - {col}: {df[col].value_counts().to_dict()}")