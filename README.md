# Fiches Techniques & Calcul Nutritionnel — Django + SQL Server + Bootstrap

Application développée pour étendre le module **Gestion des fiches techniques**
existant (base `GClinique_MarocOLIV`) avec un calcul automatique des valeurs
nutritionnelles (calories, protéines, lipides, glucides, fibres, sodium) par
fiche et par personne, à partir d'un référentiel type **CIQUAL**.

## 1. Principe

- Les tables métier existantes (`Fiche_technique`, `Detaille_Fiche_Technique`,
  `Nature_article_Cuisine`) **ne sont pas modifiées**.
- Deux tables sont ajoutées : `Table_Composition_Nutritionnelle` (référentiel
  CIQUAL) et `Article_Nutrition` (correspondance article ↔ nutriment).
- Deux vues SQL (`vw_Nutrition_Ingredient`, `vw_Nutrition_Fiche`) et une
  procédure stockée (`sp_Get_Nutrition_Fiche`) font le calcul **côté base**
  pour de bonnes performances, même sur de grosses fiches.
- Django lit ces vues via des modèles `managed = False` (aucune migration
  Django n'est exécutée sur cette base de production).

## 2. Installation

### 2.1 Base de données (SSMS)

Exécuter le script `sql/nutrition_schema.sql` dans SSMS, connecté à
`GClinique_MarocOLIV`. Il est idempotent (peut être relancé sans erreur).

Adapter ensuite la table `Article_Nutrition` pour mapper vos vrais codes
articles (`Nature_article_Cuisine.Code`) aux codes CIQUAL importés.

### 2.2 Environnement Python

```bash
python -m venv venv
source venv/bin/activate        # ou venv\Scripts\activate sous Windows
pip install -r requirements.txt
cp .env.example .env
```

Renseigner `.env` avec les identifiants du login SQL Server dédié
(ex. `app_fiches`, rôles `db_datareader` + `db_datawriter`) et le nom exact
du driver ODBC installé sur la machine (`ODBC Driver 17` ou `18 for SQL
Server` — vérifiable dans le Panneau de configuration ODBC sous Windows).

### 2.3 Lancer le serveur

```bash
python manage.py runserver
```

Ouvrir http://127.0.0.1:8000/ — la liste des fiches techniques s'affiche,
avec un lien "Détail nutritionnel" par fiche.

### 2.4 (Optionnel) Importer un extrait CIQUAL

Télécharger l'export CSV public CIQUAL sur data.gouv.fr / ANSES, puis :

```bash
python manage.py import_ciqual chemin/vers/Table_Ciqual.csv
```

Les noms de colonnes attendus sont dans `fiches/management/commands/import_ciqual.py`
(`COL_MAP`) — à ajuster selon le millésime du fichier téléchargé.

## 3. Structure du projet

```
ficheapp/
├── config/                  # settings, urls, wsgi
├── fiches/
│   ├── models.py            # tables existantes + nouvelles tables (managed=False)
│   ├── services.py          # calcul nutritionnel (version SQL + version Python)
│   ├── views.py             # liste, détail, endpoint JSON /api/fiche/<code>/nutrition/
│   ├── admin.py             # back-office pour gérer le référentiel nutritionnel
│   ├── management/commands/import_ciqual.py
│   └── templates/fiches/    # base.html, liste_fiches.html, detail_fiche.html (Bootstrap 5)
├── sql/nutrition_schema.sql # script à exécuter dans SSMS
├── requirements.txt
└── .env.example
```

## 4. Points d'attention pour la suite du stage

- **Mapping articles → CIQUAL** : c'est la tâche la plus longue (associer
  chacun des ~X00 articles de `Nature_article_Cuisine` à un aliment CIQUAL
  pertinent). Prévoir un écran d'administration dédié si le volume est
  important (l'admin Django fourni permet déjà de le faire).
- **Unités `UN`** : le poids moyen par défaut (100 g) est une approximation
  grossière — pour les articles vendus à l'unité (ex. un œuf, un citron), il
  est préférable d'ajouter un champ `Poids_Unitaire_Moyen` sur `Nature_article_Cuisine`
  ou sur `Article_Nutrition` plutôt que d'utiliser une constante globale.
- **Régime alimentaire** : `Detaille_Fiche_Technique` a une clé composite
  incluant `Code_regime`, donc une même fiche peut avoir plusieurs déclinaisons
  nutritionnelles (ex. régime normal vs sans sel) — déjà géré par les vues SQL.
- **Performance** : pour des fiches à très nombreux ingrédients, privilégier
  systématiquement `get_nutrition_fiche_sql()` (vues SQL) plutôt que
  `get_nutrition_fiche_python()`, qui existe surtout à but pédagogique/debug.
