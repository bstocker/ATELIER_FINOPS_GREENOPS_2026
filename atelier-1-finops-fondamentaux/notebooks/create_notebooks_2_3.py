import nbformat

# ── Notebook 02 : Tagging Coverage ──────────────────────────────────────────

nb2 = nbformat.v4.new_notebook()
nb2.cells = [
    nbformat.v4.new_markdown_cell("# Notebook 02 — Analyse du taux de tagging"),
    nbformat.v4.new_code_cell(
        "import pandas as pd\n"
        "from pathlib import Path\n"
        "df = pd.read_csv(Path('../../ressources/datasets/cur_sample.csv'), parse_dates=['usage_date'])\n"
        "account_labels = {'111111111111':'prod','222222222222':'staging','333333333333':'dev','444444444444':'sandbox'}\n"
        "df['account_name'] = df['account_id'].map(account_labels)\n"
        "print('Dataset charge :', len(df), 'lignes')"
    ),
    nbformat.v4.new_markdown_cell("## 1. Taux de couverture global par dimension de tag"),
    nbformat.v4.new_code_cell(
        "total_cost = df['unblended_cost'].sum()\n"
        "for tag in ['tag_team', 'tag_env', 'tag_project']:\n"
        "    tagged = df[df[tag].notna() & (df[tag] != '')]['unblended_cost'].sum()\n"
        "    print(f'{tag:15s} : {tagged/total_cost*100:.1f}% couvert (${tagged:,.0f} / ${total_cost:,.0f})')"
    ),
    nbformat.v4.new_markdown_cell("## 2. Services orphelins (sans tag_team)"),
    nbformat.v4.new_code_cell(
        "untagged = df[df['tag_team'].isna() | (df['tag_team'] == '')]\n"
        "orphans = untagged.groupby('service')['unblended_cost'].sum().sort_values(ascending=False)\n"
        "print('Services sans tag_team :')\n"
        "print(orphans.to_string())\n"
        "print(f'\\nTotal non tague : ${orphans.sum():,.2f} ({orphans.sum()/total_cost*100:.1f}% du total)')"
    ),
    nbformat.v4.new_markdown_cell("## 3. Matrice de couverture : compte x service"),
    nbformat.v4.new_code_cell(
        "df['is_tagged'] = (df['tag_team'].notna() & (df['tag_team'] != '')).astype(int)\n"
        "matrix = df.pivot_table(\n"
        "    index='service', columns='account_name',\n"
        "    values='is_tagged', aggfunc='mean'\n"
        ").round(2) * 100\n"
        "print('Taux de tagging (%) par service x compte :')\n"
        "print(matrix.to_string())"
    ),
    nbformat.v4.new_markdown_cell("## 4. Top services a tagger en priorite"),
    nbformat.v4.new_code_cell(
        "priority = untagged.groupby('service')['unblended_cost'].sum().sort_values(ascending=False).head(5)\n"
        "print('Priorite de tagging (cout non tague) :')\n"
        "for svc, cost in priority.items():\n"
        "    print(f'  {svc:25s} : ${cost:,.2f}')"
    ),
]

nbformat.write(nb2, '02-tagging-coverage.ipynb')
print("OK - notebook 02 cree")

# ── Notebook 03 : Allocation ─────────────────────────────────────────────────

nb3 = nbformat.v4.new_notebook()
nb3.cells = [
    nbformat.v4.new_markdown_cell("# Notebook 03 — Allocation des couts non tagges"),
    nbformat.v4.new_code_cell(
        "import pandas as pd\n"
        "from pathlib import Path\n"
        "df = pd.read_csv(Path('../../ressources/datasets/cur_sample.csv'), parse_dates=['usage_date'])\n"
        "df_tagged = df[df['tag_team'].notna() & (df['tag_team'] != '')].copy()\n"
        "df_untagged = df[df['tag_team'].isna() | (df['tag_team'] == '')].copy()\n"
        "print(f'Couts tagges   : ${df_tagged.unblended_cost.sum():,.2f}')\n"
        "print(f'Couts non tagges: ${df_untagged.unblended_cost.sum():,.2f}')\n"
        "print(f'Total          : ${df.unblended_cost.sum():,.2f}')"
    ),
    nbformat.v4.new_markdown_cell("## Exercice 3 — Implémenter allocate_proportional()"),
    nbformat.v4.new_code_cell(
        "def allocate_proportional(df_tagged: pd.DataFrame, df_untagged: pd.DataFrame) -> pd.DataFrame:\n"
        "    \"\"\"\n"
        "    Repartit les couts non tagges proportionnellement aux couts tagges par equipe.\n"
        "    Retourne un DataFrame avec le cout total alloue par equipe.\n"
        "    \"\"\"\n"
        "    # Calcul du total tague par equipe\n"
        "    team_tagged = df_tagged.groupby('tag_team')['unblended_cost'].sum()\n"
        "    \n"
        "    # Part de chaque equipe (en %)\n"
        "    team_share = team_tagged / team_tagged.sum()\n"
        "    \n"
        "    # Total des couts non tagges a redistribuer\n"
        "    total_untagged = df_untagged['unblended_cost'].sum()\n"
        "    \n"
        "    # Allocation proportionnelle\n"
        "    team_allocated = total_untagged * team_share\n"
        "    \n"
        "    # Consolidation : tague + allocated\n"
        "    result = pd.DataFrame({\n"
        "        'tag_team': team_tagged.index,\n"
        "        'cout_tague': team_tagged.values,\n"
        "        'cout_alloue': team_allocated.values,\n"
        "    })\n"
        "    result['cout_total'] = result['cout_tague'] + result['cout_alloue']\n"
        "    return result.sort_values('cout_total', ascending=False).reset_index(drop=True)\n"
        "\n"
        "result = allocate_proportional(df_tagged, df_untagged)\n"
        "print(result.to_string(index=False))\n"
        "\n"
        "# Verification : la somme doit etre egale au total original\n"
        "total_original = df['unblended_cost'].sum()\n"
        "total_result = result['cout_total'].sum()\n"
        "print(f'\\nVerification conservation des couts :')\n"
        "print(f'  Total original : ${total_original:,.2f}')\n"
        "print(f'  Total result   : ${total_result:,.2f}')\n"
        "print(f'  OK : {abs(total_original - total_result) < 0.01}')"
    ),
    nbformat.v4.new_markdown_cell("## Comparaison des 3 methodes d'allocation"),
    nbformat.v4.new_code_cell(
        "total_untagged = df_untagged['unblended_cost'].sum()\n"
        "teams = df_tagged['tag_team'].unique()\n"
        "n_teams = len(teams)\n"
        "\n"
        "# Even split\n"
        "even = df_tagged.groupby('tag_team')['unblended_cost'].sum() + total_untagged / n_teams\n"
        "\n"
        "# Proportional (deja calcule)\n"
        "proportional = result.set_index('tag_team')['cout_total']\n"
        "\n"
        "comparison = pd.DataFrame({\n"
        "    'even_split': even,\n"
        "    'proportional': proportional,\n"
        "})\n"
        "comparison['difference_%'] = ((comparison['proportional'] - comparison['even_split']) / comparison['even_split'] * 100).round(1)\n"
        "print(comparison.to_string())"
    ),
]

nbformat.write(nb3, '03-allocation-exercice.ipynb')
print("OK - notebook 03 cree")
