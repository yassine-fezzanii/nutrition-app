"""
Modèles Django mappés sur la base SQL Server GClinique_MarocOLIV.

IMPORTANT : toutes les tables (existantes ET nouvelles) sont créées via le
script /sql/nutrition_schema.sql exécuté directement dans SSMS, PAS via
`python manage.py migrate`. On utilise donc managed = False partout pour que
Django ne touche jamais au schéma de cette base de production.
"""
from django.db import models


# =================================================================
# Tables EXISTANTES (ne pas modifier la structure - lecture/écriture
# des données uniquement)
# =================================================================

class NatureArticleCuisine(models.Model):
    code = models.CharField(db_column='Code', max_length=20, primary_key=True)
    designation = models.CharField(db_column='Designation', max_length=100, null=True)
    unimes = models.CharField(db_column='unimes', max_length=10)
    taux_chute = models.DecimalField(db_column='Taux_chute', max_digits=18, decimal_places=3)
    cod_dep = models.CharField(db_column='CodDep', max_length=2)

    class Meta:
        managed = False
        db_table = 'Nature_article_Cuisine'

    def __str__(self):
        return f'{self.code} - {self.designation}'


class FicheTechnique(models.Model):
    code = models.CharField(db_column='Code', max_length=10, primary_key=True)
    designation = models.CharField(db_column='Designation', max_length=100)
    code_composition = models.CharField(db_column='Code_Composition', max_length=2)
    nombre_personne = models.DecimalField(db_column='Nombre_Personne', max_digits=18, decimal_places=0)
    version = models.DecimalField(db_column='Version', max_digits=18, decimal_places=0)
    user_create = models.CharField(db_column='User_Create', max_length=50)
    date_creation = models.DateTimeField(db_column='Date_Creation')
    actif = models.BooleanField(db_column='Actif')
    prix_achat_ht = models.DecimalField(db_column='Prix_Achat_HT', max_digits=18, decimal_places=3, null=True)
    code_prest = models.CharField(db_column='Code_Prest', max_length=50, null=True)
    cout_total_fiche = models.DecimalField(db_column='Cout_total_fiche', max_digits=18, decimal_places=3)
    valider = models.BooleanField(db_column='valider')
    user_valide = models.CharField(db_column='user_valide', max_length=20, null=True)
    date_valide = models.DateTimeField(db_column='date_valide', null=True)

    class Meta:
        managed = False
        db_table = 'Fiche_technique'

    def __str__(self):
        return f'{self.code} - {self.designation}'


class DetailleFicheTechnique(models.Model):
    # clé composite dans SQL Server -> on force une PK Django "factice"
    id = models.AutoField(primary_key=True, db_column='id_django_only')
    code_fiche = models.CharField(db_column='Code_Fiche', max_length=10)
    code_regime = models.CharField(db_column='Code_regime', max_length=8)
    codart = models.CharField(db_column='Codart', max_length=50)
    unite_grammage = models.CharField(db_column='Unite_Grammage', max_length=2)
    quantite = models.DecimalField(db_column='Quantite', max_digits=18, decimal_places=3)
    prix = models.DecimalField(db_column='prix', max_digits=18, decimal_places=3, null=True)

    class Meta:
        managed = False
        db_table = 'Detaille_Fiche_Technique'

    def __str__(self):
        return f'{self.code_fiche} / {self.codart}'


# =================================================================
# Tables NOUVELLES (créées par sql/nutrition_schema.sql)
# =================================================================

class TableCompositionNutritionnelle(models.Model):
    """Référentiel nutritionnel type CIQUAL - valeurs pour 100 g."""
    code_nutriment = models.CharField(db_column='Code_Nutriment', max_length=10, primary_key=True)
    libelle = models.CharField(db_column='Libelle', max_length=150)
    calories_100g = models.DecimalField(db_column='Calories_100g', max_digits=10, decimal_places=2)
    proteines_100g = models.DecimalField(db_column='Proteines_100g', max_digits=10, decimal_places=2)
    lipides_100g = models.DecimalField(db_column='Lipides_100g', max_digits=10, decimal_places=2)
    glucides_100g = models.DecimalField(db_column='Glucides_100g', max_digits=10, decimal_places=2)
    fibres_100g = models.DecimalField(db_column='Fibres_100g', max_digits=10, decimal_places=2)
    sodium_100g = models.DecimalField(db_column='Sodium_100g', max_digits=10, decimal_places=2)
    source = models.CharField(db_column='Source', max_length=30)

    class Meta:
        managed = False
        db_table = 'Table_Composition_Nutritionnelle'

    def __str__(self):
        return self.libelle


class ArticleNutrition(models.Model):
    """Correspondance entre un article de cuisine et sa fiche nutritionnelle."""
    codart = models.CharField(db_column='Codart', max_length=50, primary_key=True)
    code_nutriment = models.ForeignKey(
        TableCompositionNutritionnelle,
        db_column='Code_Nutriment',
        on_delete=models.PROTECT,
    )

    class Meta:
        managed = False
        db_table = 'Article_Nutrition'


class NutritionIngredient(models.Model):
    """Mappe la vue SQL vw_Nutrition_Ingredient (lecture seule)."""
    code_fiche = models.CharField(db_column='Code_Fiche', max_length=10, primary_key=True)
    code_regime = models.CharField(db_column='Code_regime', max_length=8)
    codart = models.CharField(db_column='Codart', max_length=50)
    designation_article = models.CharField(db_column='Designation_Article', max_length=100, null=True)
    unite_grammage = models.CharField(db_column='Unite_Grammage', max_length=2)
    quantite = models.DecimalField(db_column='Quantite', max_digits=18, decimal_places=3)
    quantite_grammes = models.DecimalField(db_column='Quantite_Grammes', max_digits=18, decimal_places=3)
    calories = models.DecimalField(db_column='Calories', max_digits=18, decimal_places=3)
    proteines = models.DecimalField(db_column='Proteines', max_digits=18, decimal_places=3)
    lipides = models.DecimalField(db_column='Lipides', max_digits=18, decimal_places=3)
    glucides = models.DecimalField(db_column='Glucides', max_digits=18, decimal_places=3)
    fibres = models.DecimalField(db_column='Fibres', max_digits=18, decimal_places=3)
    sodium = models.DecimalField(db_column='Sodium', max_digits=18, decimal_places=3)
    est_mappe = models.IntegerField(db_column='Est_Mappe')

    class Meta:
        managed = False
        db_table = 'vw_Nutrition_Ingredient'


class NutritionFiche(models.Model):
    """Mappe la vue SQL vw_Nutrition_Fiche (lecture seule)."""
    code_fiche = models.CharField(db_column='Code_Fiche', max_length=10, primary_key=True)
    designation = models.CharField(db_column='Designation', max_length=100)
    nombre_personne = models.DecimalField(db_column='Nombre_Personne', max_digits=18, decimal_places=0)
    calories_total = models.DecimalField(db_column='Calories_Total', max_digits=18, decimal_places=3)
    proteines_total = models.DecimalField(db_column='Proteines_Total', max_digits=18, decimal_places=3)
    lipides_total = models.DecimalField(db_column='Lipides_Total', max_digits=18, decimal_places=3)
    glucides_total = models.DecimalField(db_column='Glucides_Total', max_digits=18, decimal_places=3)
    fibres_total = models.DecimalField(db_column='Fibres_Total', max_digits=18, decimal_places=3)
    sodium_total = models.DecimalField(db_column='Sodium_Total', max_digits=18, decimal_places=3)
    calories_personne = models.DecimalField(db_column='Calories_Personne', max_digits=18, decimal_places=3)
    proteines_personne = models.DecimalField(db_column='Proteines_Personne', max_digits=18, decimal_places=3)
    lipides_personne = models.DecimalField(db_column='Lipides_Personne', max_digits=18, decimal_places=3)
    glucides_personne = models.DecimalField(db_column='Glucides_Personne', max_digits=18, decimal_places=3)
    fibres_personne = models.DecimalField(db_column='Fibres_Personne', max_digits=18, decimal_places=3)
    sodium_personne = models.DecimalField(db_column='Sodium_Personne', max_digits=18, decimal_places=3)
    tous_ingredients_mappes = models.IntegerField(db_column='Tous_Ingredients_Mappes')

    class Meta:
        managed = False
        db_table = 'vw_Nutrition_Fiche'
