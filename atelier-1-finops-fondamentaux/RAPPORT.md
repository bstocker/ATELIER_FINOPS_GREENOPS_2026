# Rapport Atelier 1 — FinOps Fondamentaux

## 1. Synthèse des chiffres clés (90 jours)

| Indicateur | Valeur |
|------------|--------|
| Coût total | $33 948.85 |
| Coût moyen / jour | $377.21 |
| Pic journalier | $727.14 le 2025-03-16 (+93% vs moyenne) |
| Nombre de services | 8 |
| Nombre de comptes | 4 |
| Taux de tagging (tag_team) | 81.9% |

---

## 2. Top 3 des services par coût

| Rang | Service | Coût estimé | % du total |
|------|---------|-------------|------------|
| 1 | AmazonEC2 | ~$19 000 | ~56% |
| 2 | AmazonRDS | ~$5 500 | ~16% |
| 3 | AmazonCloudWatch | ~$4 500 | ~13% |

EC2 représente plus de la moitié des dépenses — c'est le principal levier d'optimisation.

---

## 3. Répartition par compte

| Compte | Part (%) | Analyse |
|--------|----------|---------|
| prod | ~60% | Cohérent — supporte le trafic réel |
| staging | ~20% | Acceptable |
| dev | ~15% | Élevé — ressources probablement non éteintes le week-end |
| sandbox | ~5% | Normal |

---

## 4. Anomalie détectée

**Creux du 9-10 février 2025** : coût journalier ~$150 (60% sous la moyenne).  
**Hypothèse** : week-end avec extinction partielle des environnements non-prod.  
**Confirmation** : filtrer sur ces deux jours et décomposer par compte — si dev/sandbox sont quasi nuls, c'est confirmé.

---

## 5. Analyse du tagging (Notebook 02)

- **tag_team** : 81.9% de couverture — 18.1% des coûts non attribuables
- Services prioritaires à tagger : EC2 ($3 328), RDS ($1 031), CloudWatch ($740), EBS ($632)
- La matrice compte × service montre que le compte `sandbox` a la couverture la plus faible

---

## 6. Allocation proportionnelle (Notebook 03)

| Équipe | Coût taggé | Coût alloué total | Part |
|--------|-----------|-------------------|------|
| data | $7 562 | $9 235 | 27.2% |
| platform | $7 426 | $9 070 | 26.7% |
| frontend | $6 669 | $8 145 | 24.0% |
| payments | $6 141 | $7 499 | 22.1% |

La méthode proportionnelle est préférable à l'even split car elle respecte la consommation réelle de chaque équipe.

---

## 7. Détection des gaspillages (Notebook 04)

| Heuristique | Résultat |
|-------------|----------|
| EBS sans EC2 | Non détecté (EC2 actif tous les jours) |
| Ressources constantes en dev | Détecté — coût constant 24/7 |
| Coût week-end vs semaine non-prod | Ratio ~1 → gaspillage week-end confirmé |
| Usage_type > $1000 en décroissance | Non détecté |
| EC2 surdimensionnées | Instances xlarge identifiées |
| Croissance MoM > 50% | Non détectée |

**Économie potentielle estimée** : extinction des envs non-prod le week-end pourrait économiser ~60-70% des coûts dev/sandbox sur cette période.

---

## 8. Budget vs Réel (Dashboard)

| Équipe | Budget mensuel | Réel moyen/mois | Statut |
|--------|---------------|-----------------|--------|
| platform | $6 000 | ~$3 024 | 🟢 OK |
| data | $3 500 | ~$2 521 | 🟢 OK |
| payments | $4 500 | ~$2 047 | 🟢 OK |
| frontend | $2 000 | ~$2 223 | 🔴 Dépassement (+112%) |

**Alerte** : l'équipe `frontend` dépasse son budget mensuel de 12%.

---

## 9. 5 actions prioritaires recommandées à la direction IT

### Action 1 — Extinction automatique des environnements non-prod le week-end
**Priorité : haute | Effort : faible**  
Les comptes dev et sandbox maintiennent un coût constant 7j/7. Mettre en place des scripts d'arrêt automatique (AWS Instance Scheduler ou Lambda) permettrait d'économiser ~60% des coûts non-prod, soit ~$2 000/mois.

### Action 2 — Rightsizing des instances EC2
**Priorité : haute | Effort : moyen**  
EC2 représente 56% des dépenses. L'analyse des usage_type révèle des instances xlarge et 2xlarge dont l'usage réel est probablement bien inférieur aux capacités réservées. Un passage aux familles t3/t4g avec AWS Compute Optimizer permettrait d'économiser 20-40%.

### Action 3 — Atteindre 100% de couverture tagging
**Priorité : haute | Effort : moyen**  
18.1% des coûts ($6 150) ne sont pas attribuables à une équipe. Implémenter des SCPs (Service Control Policies) imposant le tagging à la création via AWS Config rules et bloquer les déploiements sans tags via CI/CD.

### Action 4 — Réviser le budget frontend
**Priorité : moyenne | Effort : faible**  
L'équipe frontend dépasse son budget de 12%. Soit le budget est sous-estimé (à réviser), soit l'équipe a des ressources à optimiser. Organiser une revue mensuelle de showback avec cette équipe.

### Action 5 — Mettre en place un processus FinOps mensuel
**Priorité : moyenne | Effort : moyen**  
Aucun processus de revue des coûts n'existe actuellement. Instaurer une réunion mensuelle de 30 min avec les tech leads pour présenter le showback, identifier les anomalies et prioriser les optimisations. Cible : réduire le coût unitaire de 15% en 6 mois.

---

## 10. Questions de réflexion

**En quoi le FinOps diffère-t-il d'une démarche d'audit financier classique ?**  
Un audit financier est rétrospectif, ponctuel et externe. Le FinOps est continu, embarqué dans les équipes d'ingénierie, et vise l'optimisation opérationnelle en temps réel. Il responsabilise les équipes qui consomment (principe "you build it, you own it, you pay for it") plutôt que de contrôler après coup.

**Pourquoi le tagging à la création est-il préférable au tagging rétroactif ?**  
Le tagging rétroactif est incomplet (ressources déjà supprimées), coûteux en effort humain, et génère des périodes sans données d'allocation. À la création, via IaC (Terraform, CDK) ou SCPs, le tag est garanti sans surcoût opérationnel.

**Quelle métrique pour suivre la maturité FinOps ?**  
Le **taux de couverture tagging** (objectif 100%) combiné au **ratio coût unitaire** (coût / utilisateur actif ou coût / transaction) permettent de mesurer à la fois la visibilité et l'efficience. Une organisation mature a une couverture > 95% et un coût unitaire en amélioration continue.
