# Atelier 1 — Exercices Partie 2 : Exploration du CUR

  > À remplir après avoir exécuté le notebook `01-exploration-cur.ipynb`.

  ## Exercice 2.1 — Lecture des données

  **Question 1.** Quel est le top 3 des services par coût sur les 90 jours ?

  | Rang | Service | Coût total ($) | % du total |
  |------|---------|---------------|------------|
  | 1 | AmazonEC2 | ~19 000 | ~56% |
  | 2 | AmazonRDS | ~5 500 | ~16% |
  | 3 | AmazonCloudWatch | ~4 500 | ~13% |

  **Question 2.** Quel jour observe-t-on un pic de dépense ? De combien (en valeur absolue et en % de la moyenne) ?

  > Le pic est observé le **2025-03-16** avec **$727.14**, soit environ **+93% au-dessus de la moyenne journalière** de
  $377.21. Ce pic peut s'expliquer par un déploiement en production, un batch mensuel ou un incident de scaling non
  maîtrisé.

  **Question 3.** Le compte `prod` consomme-t-il la majorité ? Est-ce attendu ? Notez la part de chaque compte.

  | Compte | Part (%) | Cohérent ? |
  |--------|----------|------------|
  | prod | ~60% | Oui — prod supporte le trafic réel et les workloads critiques |
  | staging | ~20% | Acceptable — environnement de validation proche de la prod |
  | dev | ~15% | Élevé — suggère des ressources non éteintes en dehors des heures de travail |
  | sandbox | ~5% | Normal — usage ponctuel d'expérimentation |

  **Question 4.** Identifiez **une anomalie visuelle** sur les graphiques (pic isolé, tendance bizarre, écart
  inattendu).

  > _Description :_ Creux prononcé vers le 9-10 février 2025 avec un coût journalier d'environ $150, soit 60% sous la
  moyenne.
  > _Hypothèse :_ Week-end avec arrêt partiel des environnements non-prod (dev + sandbox). Cela indiquerait que les
  équipes ont une bonne pratique d'extinction manuelle, mais non systématique.
  > _Que feriez-vous pour confirmer ?_ Filtrer le dataset sur ces deux jours, décomposer par compte et par service pour
  vérifier si dev/sandbox ont des coûts quasi nuls ce week-end là.

  ## Exercice 2.2 — Question ouverte

  Selon vous, à partir de quel **seuil de coût mensuel** une équipe devrait-elle obligatoirement avoir des tags
  d'allocation ? Justifiez (penser en termes de coût/bénéfice de la mise en place du tagging).

  > À partir de **$500/mois** par équipe ou projet. En dessous de ce seuil, le coût de mise en place du tagging
  (définition de la politique, enforcement via SCP/Policy, audits réguliers) dépasse le bénéfice financier de la
  visibilité obtenue. Au-delà, l'allocation devient indispensable pour prendre des décisions de rightsizing éclairées et
   responsabiliser les équipes sur leur consommation réelle.