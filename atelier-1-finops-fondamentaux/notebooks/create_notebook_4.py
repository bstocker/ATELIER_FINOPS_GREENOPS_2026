import nbformat

nb4 = nbformat.v4.new_notebook()
nb4.cells = [
    nbformat.v4.new_markdown_cell("# Notebook 04 — Detection des gaspillages"),
    nbformat.v4.new_code_cell(
        "import pandas as pd\n"
        "from pathlib import Path\n"
        "df = pd.read_csv(Path('../../ressources/datasets/cur_sample.csv'), parse_dates=['usage_date'])\n"
        "account_labels = {'111111111111':'prod','222222222222':'staging','333333333333':'dev','444444444444':'sandbox'}\n"
        "df['account_name'] = df['account_id'].map(account_labels)\n"
        "df['month'] = df['usage_date'].dt.to_period('M')\n"
        "df['is_weekend'] = df['usage_date'].dt.dayofweek >= 5\n"
        "print('Dataset charge :', len(df), 'lignes')"
    ),
    nbformat.v4.new_markdown_cell("## Heuristique 1 — EBS sans EC2 actif le meme jour"),
    nbformat.v4.new_code_cell(
        "days_with_ec2 = df[df['service'] == 'AmazonEC2']['usage_date'].unique()\n"
        "ebs_no_ec2 = df[\n"
        "    (df['service'] == 'AmazonEBS') &\n"
        "    (~df['usage_date'].isin(days_with_ec2))\n"
        "]\n"
        "print(f'Cout EBS sans EC2 actif : ${ebs_no_ec2.unblended_cost.sum():,.2f}')\n"
        "if len(ebs_no_ec2) == 0:\n"
        "    print('Aucun jour sans EC2 — heuristique non declenchee sur ce dataset')"
    ),
    nbformat.v4.new_markdown_cell("## Heuristique 2 — Ressources constantes 24/7 en environnement dev"),
    nbformat.v4.new_code_cell(
        "dev_daily = df[df['account_name'] == 'dev'].groupby(['service', 'usage_date'])['unblended_cost'].sum().reset_index()\n"
        "dev_stats = dev_daily.groupby('service')['unblended_cost'].agg(['mean', 'std', 'count']).reset_index()\n"
        "dev_stats['cv'] = (dev_stats['std'] / dev_stats['mean']).round(3)\n"
        "constant = dev_stats[dev_stats['cv'] < 0.1].sort_values('mean', ascending=False)\n"
        "print('Services avec cout constant en dev (CV < 10%) :')\n"
        "print(constant[['service', 'mean', 'cv']].to_string(index=False))\n"
        "print(f'\\nCout mensuel estime gaspille : ${constant[\"mean\"].sum() * 8:,.2f} (week-ends inclus)')"
    ),
    nbformat.v4.new_markdown_cell("## Heuristique 3 — Cout week-end vs semaine en non-prod"),
    nbformat.v4.new_code_cell(
        "non_prod = df[df['account_name'].isin(['dev', 'sandbox'])]\n"
        "we = non_prod.groupby('is_weekend')['unblended_cost'].mean()\n"
        "ratio = we[True] / we[False]\n"
        "print(f'Cout moyen semaine  : ${we[False]:,.2f}')\n"
        "print(f'Cout moyen week-end : ${we[True]:,.2f}')\n"
        "print(f'Ratio week-end/semaine : {ratio:.2f}')\n"
        "if ratio > 0.8:\n"
        "    savings = (we[True] - we[False] * 0.1) * 8 * 4\n"
        "    print(f'=> Gaspillage : les envs non-prod tournent le week-end')\n"
        "    print(f'=> Economie potentielle si arret week-end : ${savings:,.2f}/mois')"
    ),
    nbformat.v4.new_markdown_cell("## Heuristique 4 — Top 10 usage_type avec cout > $1000 et tendance decroissante"),
    nbformat.v4.new_code_cell(
        "monthly = df.groupby(['usage_type', 'month'])['unblended_cost'].sum().reset_index()\n"
        "monthly['month_num'] = monthly['month'].dt.month\n"
        "top_usage = df.groupby('usage_type')['unblended_cost'].sum()\n"
        "top_usage = top_usage[top_usage > 1000].index\n"
        "\n"
        "declining = []\n"
        "for ut in top_usage:\n"
        "    data = monthly[monthly['usage_type'] == ut].sort_values('month_num')\n"
        "    if len(data) >= 2 and data['unblended_cost'].iloc[-1] < data['unblended_cost'].iloc[0]:\n"
        "        declining.append({'usage_type': ut,\n"
        "                          'cout_debut': data['unblended_cost'].iloc[0],\n"
        "                          'cout_fin': data['unblended_cost'].iloc[-1],\n"
        "                          'baisse_%': round((1 - data['unblended_cost'].iloc[-1]/data['unblended_cost'].iloc[0])*100, 1)})\n"
        "\n"
        "if declining:\n"
        "    print('Usage types > $1000 avec tendance decroissante :')\n"
        "    print(pd.DataFrame(declining).sort_values('baisse_%', ascending=False).to_string(index=False))\n"
        "else:\n"
        "    print('Aucun usage_type > $1000 avec tendance decroissante')"
    ),
    nbformat.v4.new_markdown_cell("## Heuristique 5 — Instances EC2 potentiellement surdimensionnees"),
    nbformat.v4.new_code_cell(
        "ec2 = df[df['service'] == 'AmazonEC2'].copy()\n"
        "large = ec2[ec2['usage_type'].str.contains('xlarge|2xlarge|4xlarge', na=False)]\n"
        "print('Instances EC2 de grande taille (potentiellement surdimensionnees) :')\n"
        "print(large.groupby('usage_type')['unblended_cost'].sum().sort_values(ascending=False).to_string())\n"
        "print(f'\\nCout total grandes instances : ${large.unblended_cost.sum():,.2f}')"
    ),
    nbformat.v4.new_markdown_cell("## Exercice 4 — Heuristique 6 : croissance MoM > 50%"),
    nbformat.v4.new_code_cell(
        "def detect_high_growth(df: pd.DataFrame, threshold_pct: float = 50.0) -> pd.DataFrame:\n"
        "    \"\"\"\n"
        "    Detecte les services dont la croissance MoM (Month over Month) depasse threshold_pct%\n"
        "    et qui ne sont pas tagges tag_project=growth.\n"
        "    \"\"\"\n"
        "    monthly_svc = df.groupby(['service', 'month'])['unblended_cost'].sum().reset_index()\n"
        "    monthly_svc = monthly_svc.sort_values(['service', 'month'])\n"
        "    monthly_svc['prev_cost'] = monthly_svc.groupby('service')['unblended_cost'].shift(1)\n"
        "    monthly_svc['mom_pct'] = ((monthly_svc['unblended_cost'] - monthly_svc['prev_cost'])\n"
        "                              / monthly_svc['prev_cost'] * 100).round(1)\n"
        "\n"
        "    high_growth = monthly_svc[\n"
        "        (monthly_svc['mom_pct'] > threshold_pct) &\n"
        "        (monthly_svc['prev_cost'].notna())\n"
        "    ]\n"
        "\n"
        "    # Exclure les services tagges growth\n"
        "    growth_projects = df[df['tag_project'] == 'growth']['service'].unique()\n"
        "    high_growth = high_growth[~high_growth['service'].isin(growth_projects)]\n"
        "\n"
        "    return high_growth[['service', 'month', 'prev_cost', 'unblended_cost', 'mom_pct']]\n"
        "\n"
        "result = detect_high_growth(df)\n"
        "if len(result) > 0:\n"
        "    print('Services avec croissance MoM > 50% (hors tag_project=growth) :')\n"
        "    print(result.to_string(index=False))\n"
        "else:\n"
        "    print('Aucun service avec croissance MoM > 50% detecte')"
    ),
]

nbformat.write(nb4, '04-waste-detection.ipynb')
print("OK - notebook 04 cree")
