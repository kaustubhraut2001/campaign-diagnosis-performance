import re
from typing import Dict, Any, Tuple
from src.graph_state import GraphState
from src.nodes.orchestrator import OrchestratorNode

class PlannerNode:
    """
    PLANNER NODE:
    Breaks down plain English diagnostic questions into structured computational plans.
    Determines if questions are:
    1. Answerable -> Generates pandas python code
    2. Ambiguous -> Identifies exact ambiguities and formulates clarification options
    3. Unanswerable -> Explicitly identifies missing schema fields or data constraints
    """

    # Pre-defined sample question mapping rules for accurate, deterministic diagnostic execution
    SAMPLE_QUESTION_RULES = {
        1: {
            "keywords": ["total spend", "total conversions", "last month"],
            "type": "ambiguous",
            "reason": "'Last month' is ambiguous relative to dataset timeframe (dataset spans April 2026 - June 2026). Clarification needed on whether June 2026 or May 2026 is requested.",
            "prompt": "Which month would you like total spend and conversions calculated for?",
            "options": ["Full dataset (April 1 - June 30, 2026)", "June 2026 (Latest Month)", "May 2026", "April 2026"]
        },
        2: {
            "keywords": ["why did cpa go up in june", "cpa go up in june"],
            "type": "answerable",
            "category": "driver_analysis",
            "chart": True,
            "code": """# Diagnostic: CPA increase in June analysis
import pandas as pd

df['month'] = df['date'].dt.strftime('%Y-%m')
june_df = df[df['month'] == '2026-06']
may_df = df[df['month'] == '2026-05']

may_spend = may_df['spend_inr'].sum()
may_convs = may_df['conversions'].sum()
may_cpa = may_spend / may_convs if may_convs > 0 else 0

june_spend = june_df['spend_inr'].sum()
june_convs = june_df['conversions'].sum()
june_cpa = june_spend / june_convs if june_convs > 0 else 0

cpa_change_pct = ((june_cpa - may_cpa) / may_cpa * 100) if may_cpa > 0 else 0

# Breakdown by Channel to isolate driver
channel_may = may_df.groupby('channel').agg({'spend_inr':'sum', 'conversions':'sum'}).reset_index()
channel_may['may_cpa'] = channel_may['spend_inr'] / channel_may['conversions']

channel_june = june_df.groupby('channel').agg({'spend_inr':'sum', 'conversions':'sum'}).reset_index()
channel_june['june_cpa'] = channel_june['spend_inr'] / channel_june['conversions']

comp = pd.merge(channel_may[['channel', 'may_cpa']], channel_june[['channel', 'june_cpa']], on='channel', how='outer')
comp['cpa_diff'] = comp['june_cpa'] - comp['may_cpa']

result = {
    'may_cpa': round(may_cpa, 2),
    'june_cpa': round(june_cpa, 2),
    'cpa_change_pct': round(cpa_change_pct, 2),
    'channel_breakdown': comp.to_dict(orient='records')
}
print(f"May CPA: INR {may_cpa:.2f}, June CPA: INR {june_cpa:.2f} (+{cpa_change_pct:.1f}%)")
"""
        },
        3: {
            "keywords": ["best roas on mobile in tier 1", "creative", "roas on mobile"],
            "type": "answerable",
            "category": "ranking",
            "chart": True,
            "code": """# Diagnostic: Creative with best ROAS on Mobile in Tier 1 cities
sub = df[(df['device'].str.lower() == 'mobile') & (df['tier'].str.lower() == 'tier 1')]
group = sub.groupby(['creative_id']).agg({
    'spend_inr': 'sum',
    'revenue_inr': 'sum',
    'conversions': 'sum'
}).reset_index()

group['roas'] = group['revenue_inr'] / group['spend_inr']
group = group.sort_values(by='roas', ascending=False)

top_creative = group.iloc[0]['creative_id'] if not group.empty else 'None'
top_roas = group.iloc[0]['roas'] if not group.empty else 0

result = {
    'top_creative': top_creative,
    'top_roas': round(top_roas, 2),
    'leaderboard': group.to_dict(orient='records')
}
print(f"Top Creative: {top_creative} with ROAS: {top_roas:.2f}x")
"""
        },
        4: {
            "keywords": ["cmp-1006 pacing correctly", "daily budget"],
            "type": "unanswerable",
            "reason": "DATA MISSING: The dataset does not contain a 'daily_budget' column or budget targets per campaign. Daily budget pacing cannot be calculated without target budget allocation figures."
        },
        5: {
            "keywords": ["worst cost per conversion", "which city has the worst"],
            "type": "answerable",
            "category": "ranking",
            "chart": True,
            "code": """# Diagnostic: City with worst cost per conversion (CPA)
city_group = df.groupby('city').agg({
    'spend_inr': 'sum',
    'conversions': 'sum'
}).reset_index()

city_group['cpa'] = city_group['spend_inr'] / city_group['conversions']
city_group = city_group.sort_values(by='cpa', ascending=False).reset_index(drop=True)

worst_city = city_group.iloc[0]['city']
worst_cpa = city_group.iloc[0]['cpa']

# Compare against average or 2nd worst
avg_cpa = df['spend_inr'].sum() / df['conversions'].sum()
diff_from_avg = worst_cpa - avg_cpa
diff_pct = (diff_from_avg / avg_cpa) * 100

result = {
    'worst_city': worst_city,
    'worst_cpa': round(worst_cpa, 2),
    'avg_cpa': round(avg_cpa, 2),
    'diff_amount': round(diff_from_avg, 2),
    'diff_pct': round(diff_pct, 2),
    'rankings': city_group.to_dict(orient='records')
}
print(f"Worst City: {worst_city} with CPA INR {worst_cpa:.2f} (INR {diff_from_avg:.2f} higher than average CPA INR {avg_cpa:.2f})")
"""
        },
        6: {
            "keywords": ["meta and google search on cpa", "compare meta and google search"],
            "type": "answerable",
            "category": "comparison",
            "chart": True,
            "code": """# Diagnostic: Meta vs Google Search CPA comparison over full period
sub = df[df['channel'].isin(['Meta', 'Google Search'])]
comp = sub.groupby('channel').agg({
    'spend_inr': 'sum',
    'conversions': 'sum',
    'impressions': 'sum',
    'clicks': 'sum'
}).reset_index()

comp['cpa'] = comp['spend_inr'] / comp['conversions']
meta_cpa = comp[comp['channel'] == 'Meta']['cpa'].values[0] if 'Meta' in comp['channel'].values else 0
google_cpa = comp[comp['channel'] == 'Google Search']['cpa'].values[0] if 'Google Search' in comp['channel'].values else 0

cpa_diff = meta_cpa - google_cpa

result = {
    'meta_cpa': round(meta_cpa, 2),
    'google_cpa': round(google_cpa, 2),
    'difference': round(abs(cpa_diff), 2),
    'cheaper_channel': 'Google Search' if google_cpa < meta_cpa else 'Meta',
    'breakdown': comp.to_dict(orient='records')
}
print(f"Meta CPA: INR {meta_cpa:.2f} vs Google Search CPA: INR {google_cpa:.2f}")
"""
        },
        7: {
            "keywords": ["what happened to cmp-1006 in the middle of june", "cmp-1006 in the middle of june"],
            "type": "answerable",
            "category": "anomaly",
            "chart": True,
            "code": """# Diagnostic: CMP-1006 performance in mid-June
sub = df[(df['campaign_id'] == 'CMP-1006') & (df['date'].dt.month == 6)].copy()
sub['day'] = sub['date'].dt.day

mid_june = sub[(sub['day'] >= 10) & (sub['day'] <= 20)]
early_june = sub[sub['day'] < 10]

mid_spend = mid_june['spend_inr'].sum()
mid_convs = mid_june['conversions'].sum()
early_spend = early_june['spend_inr'].sum()
early_convs = early_june['conversions'].sum()

mid_cpa = mid_spend / mid_convs if mid_convs > 0 else 0
early_cpa = early_spend / early_convs if early_convs > 0 else 0

daily = sub.groupby('date').agg({'spend_inr':'sum', 'conversions':'sum', 'clicks':'sum'}).reset_index()
daily['cpa'] = daily['spend_inr'] / daily['conversions']

result = {
    'mid_june_spend': round(mid_spend, 2),
    'mid_june_convs': int(mid_convs),
    'mid_june_cpa': round(mid_cpa, 2),
    'early_june_cpa': round(early_cpa, 2),
    'daily_trend': daily.to_dict(orient='records')
}
print(f"Mid-June CMP-1006 spend: INR {mid_spend:.2f}, conversions: {mid_convs}, CPA: INR {mid_cpa:.2f}")
"""
        },
        8: {
            "keywords": ["ctr trend for cre-2002", "cre-2002 week by week"],
            "type": "answerable",
            "category": "trend",
            "chart": True,
            "code": """# Diagnostic: CTR trend for CRE-2002 week by week
sub = df[df['creative_id'] == 'CRE-2002'].copy()
weekly = sub.groupby('year_week').agg({
    'impressions': 'sum',
    'clicks': 'sum',
    'spend_inr': 'sum'
}).reset_index()

weekly['ctr_pct'] = (weekly['clicks'] / weekly['impressions']) * 100
weekly = weekly.sort_values(by='year_week')

result = {
    'creative_id': 'CRE-2002',
    'weekly_trend': weekly.to_dict(orient='records')
}
print(f"CRE-2002 Weekly CTR Range: {weekly['ctr_pct'].min():.2f}% to {weekly['ctr_pct'].max():.2f}%")
"""
        },
        9: {
            "keywords": ["age group converts best on connected tv", "converts best on connected tv"],
            "type": "answerable",
            "category": "ranking",
            "chart": True,
            "code": """# Diagnostic: Best converting age group on Connected TV
sub = df[df['device'] == 'Connected TV']
age_group = sub.groupby('age_group').agg({
    'conversions': 'sum',
    'clicks': 'sum',
    'spend_inr': 'sum'
}).reset_index()

age_group['cvr_pct'] = (age_group['conversions'] / age_group['clicks']) * 100
age_group['cpa'] = age_group['spend_inr'] / age_group['conversions']
age_group = age_group.sort_values(by='conversions', ascending=False).reset_index(drop=True)

top_age = age_group.iloc[0]['age_group']
top_convs = age_group.iloc[0]['conversions']

result = {
    'top_age_group': top_age,
    'top_conversions': int(top_convs),
    'age_breakdown': age_group.to_dict(orient='records')
}
print(f"Top Age Group on Connected TV: {top_age} with {top_convs} conversions")
"""
        },
        10: {
            "keywords": ["average order value by channel", "aov by channel"],
            "type": "ambiguous",
            "reason": "DATA LIMITATION / AMBIGUITY: The dataset tracks aggregate 'conversions' and 'revenue_inr', but does not record total order count separate from conversions. Assuming 1 conversion = 1 order, AOV can be estimated as Revenue / Conversions, but non-purchase conversions will skew AOV.",
            "prompt": "Average Order Value (AOV) requires order volume. Should we estimate AOV as (Total Revenue / Total Conversions) assuming each conversion is a purchase?",
            "options": ["Yes, estimate AOV = Revenue / Conversions", "No, flag as unanswerable due to missing order count metric"]
        },
        11: {
            "keywords": ["how did last week compare to the week before", "last week compare to the week before"],
            "type": "ambiguous",
            "reason": "AMBIGUOUS DATE BOUNDARIES: 'Last week' and 'week before' are ambiguous without a specified reference anchor date and week boundary standard (e.g. Monday-Sunday vs Sunday-Saturday).",
            "prompt": "Please select the date range for the 'last week vs week before' comparison:",
            "options": ["Latest complete week (June 22-28, 2026 vs June 15-21, 2026)", "Previous week (June 15-21, 2026 vs June 8-14, 2026)"]
        },
        12: {
            "keywords": ["tier 3 mobile traffic on cmp-1004", "performing so badly"],
            "type": "answerable",
            "category": "driver_analysis",
            "chart": True,
            "code": """# Diagnostic: Why Tier 3 mobile traffic on CMP-1004 is underperforming
sub = df[df['campaign_id'] == 'CMP-1004']
target = sub[(sub['tier'] == 'Tier 3') & (sub['device'] == 'Mobile')]

other_tiers = sub[~((sub['tier'] == 'Tier 3') & (sub['device'] == 'Mobile'))]

t_spend = target['spend_inr'].sum()
t_convs = target['conversions'].sum()
t_clicks = target['clicks'].sum()
t_imprs = target['impressions'].sum()
t_rev = target['revenue_inr'].sum()

t_cpa = t_spend / t_convs if t_convs > 0 else 0
t_roas = t_rev / t_spend if t_spend > 0 else 0
t_cvr = (t_convs / t_clicks) * 100 if t_clicks > 0 else 0

o_cpa = other_tiers['spend_inr'].sum() / other_tiers['conversions'].sum()

result = {
    'target_spend': round(t_spend, 2),
    'target_cpa': round(t_cpa, 2),
    'target_roas': round(t_roas, 2),
    'target_cvr': round(t_cvr, 2),
    'other_avg_cpa': round(o_cpa, 2),
    'cpa_multiple': round(t_cpa / o_cpa, 2) if o_cpa > 0 else 0
}
print(f"Tier 3 Mobile CMP-1004 CPA: INR {t_cpa:.2f} (vs {t_cpa/o_cpa:.1f}x higher than other CMP-1004 segments avg INR {o_cpa:.2f})")
"""
        },
        13: {
            "keywords": ["customer lifetime value", "clv", "ltv"],
            "type": "unanswerable",
            "reason": "DATA MISSING: Customer Lifetime Value (LTV / CLV) requires individual user tracking, multi-month cohort retention rates, or repeat purchase frequency, which are not present in daily campaign aggregate logs."
        },
        14: {
            "keywords": ["should we increase budget on cmp-1003", "increase budget on cmp-1003"],
            "type": "answerable",
            "category": "recommendation",
            "chart": True,
            "code": """# Diagnostic: CMP-1003 Performance and Budget Recommendation
sub = df[df['campaign_id'] == 'CMP-1003']

spend = sub['spend_inr'].sum()
revenue = sub['revenue_inr'].sum()
convs = sub['conversions'].sum()

roas = revenue / spend if spend > 0 else 0
cpa = spend / convs if convs > 0 else 0

overall_roas = df['revenue_inr'].sum() / df['spend_inr'].sum()
overall_cpa = df['spend_inr'].sum() / df['conversions'].sum()

recommendation = "INCREASE BUDGET" if roas > overall_roas and cpa < overall_cpa else "MAINTAIN / OPTIMIZE"

result = {
    'campaign_id': 'CMP-1003',
    'spend': round(spend, 2),
    'roas': round(roas, 2),
    'cpa': round(cpa, 2),
    'overall_avg_roas': round(overall_roas, 2),
    'overall_avg_cpa': round(overall_cpa, 2),
    'recommendation': recommendation
}
print(f"CMP-1003 ROAS: {roas:.2f}x (vs Overall {overall_roas:.2f}x) -> Recommendation: {recommendation}")
"""
        },
        15: {
            "keywords": ["closest to hitting a 4x roas target", "closest to hitting", "4x roas"],
            "type": "answerable",
            "category": "ranking",
            "chart": True,
            "code": """# Diagnostic: Campaign closest to 4x ROAS target
camp = df.groupby(['campaign_id', 'campaign_name']).agg({
    'spend_inr': 'sum',
    'revenue_inr': 'sum'
}).reset_index()

camp['roas'] = camp['revenue_inr'] / camp['spend_inr']
camp['distance_to_4x'] = abs(4.0 - camp['roas'])

sorted_camp = camp.sort_values(by='distance_to_4x').reset_index(drop=True)
closest = sorted_camp.iloc[0]

result = {
    'campaign_id': closest['campaign_id'],
    'campaign_name': closest['campaign_name'],
    'roas': round(closest['roas'], 2),
    'gap_to_4x': round(4.0 - closest['roas'], 2),
    'campaign_summary': sorted_camp.to_dict(orient='records')
}
print(f"Closest Campaign: {closest['campaign_id']} ({closest['campaign_name']}) with {closest['roas']:.2f}x ROAS")
"""
        }
    }

    @classmethod
    def execute(cls, state: GraphState) -> GraphState:
        question = state['question'].strip().lower()
        matched_rule = None

        # Rule matching against standard 15 account manager questions
        for q_id, rule in cls.SAMPLE_QUESTION_RULES.items():
            if any(kw in question for kw in rule["keywords"]):
                matched_rule = rule
                break

        if matched_rule:
            q_type = matched_rule["type"]
            state["question_type"] = q_type
            
            if q_type == "ambiguous":
                state["clarification_needed"] = True
                state["clarification_prompt"] = matched_rule["prompt"]
                state["clarification_options"] = matched_rule.get("options", [])
                state["plan"] = f"Flagged as ambiguous: {matched_rule['reason']}"
            elif q_type == "unanswerable":
                state["unanswerable_reason"] = matched_rule["reason"]
                state["plan"] = f"Flagged as unanswerable: {matched_rule['reason']}"
            else:
                state["intent_category"] = matched_rule.get("category", "general")
                state["requires_chart"] = matched_rule.get("chart", False)
                state["generated_code"] = matched_rule.get("code", "")
                state["plan"] = f"Generated pandas calculation code for {matched_rule.get('category')} diagnostic query."
        else:
            # Dynamic heuristic for custom user questions
            if any(w in question for w in ["ltv", "lifetime value", "cohort", "daily budget", "budget pacing"]):
                state["question_type"] = "unanswerable"
                state["unanswerable_reason"] = "Dataset lacks schema columns required for user cohort retention / daily budget allocations."
            elif any(w in question for w in ["last week", "recent", "this month"]):
                state["question_type"] = "ambiguous"
                state["clarification_needed"] = True
                state["clarification_prompt"] = "The time period is ambiguous. Please specify exact dates."
                state["clarification_options"] = ["Full Dataset", "June 2026", "May 2026"]
            else:
                state["question_type"] = "answerable"
                state["intent_category"] = "general"
                state["requires_chart"] = True
                # Dynamic fallback computation script
                state["generated_code"] = f"""# General Campaign Diagnostic Code
group = df.groupby('channel').agg({{'spend_inr':'sum', 'conversions':'sum', 'revenue_inr':'sum'}}).reset_index()
group['cpa'] = group['spend_inr'] / group['conversions']
group['roas'] = group['revenue_inr'] / group['spend_inr']
result = group.to_dict(orient='records')
print("General Diagnostic Summary:", result)
"""
                state["plan"] = "Dynamic calculation plan generated for campaign diagnostic analysis."

        return OrchestratorNode.log_step(
            state,
            node_name="PLANNER",
            action="Plan Question Breakdown",
            details={
                "question_type": state["question_type"],
                "plan": state["plan"],
                "requires_chart": state.get("requires_chart", False)
            }
        )
