"""
Logique métier du calcul nutritionnel.

Deux façons d'obtenir le résultat, au choix :
1) via les vues SQL Server (vw_Nutrition_Fiche / vw_Nutrition_Ingredient)
   -> le plus performant, calcul fait côté base (voir get_nutrition_fiche_sql)
2) via le calcul en Python à partir des tables brutes
   -> utile en debug, ou si on veut appliquer une logique supplémentaire
      (ex: alerter sur les ingrédients non mappés) sans dépendre des vues.
"""
from decimal import Decimal

from .models import DetailleFicheTechnique, ArticleNutrition, FicheTechnique, NutritionFiche, NutritionIngredient

# Facteurs de conversion vers grammes (poids par défaut pour une unité 'UN')
UNITE_VERS_GRAMMES = {
    'KG': Decimal('1000'),
    'GR': Decimal('1'),
    'LT': Decimal('1000'),   # approximation densité eau
    'CL': Decimal('10'),
    'UN': Decimal('100'),    # poids moyen par défaut, à affiner par article si besoin
}


def quantite_en_grammes(quantite: Decimal, unite: str) -> Decimal:
    facteur = UNITE_VERS_GRAMMES.get((unite or '').upper(), Decimal('1'))
    return quantite * facteur


def get_nutrition_fiche_sql(code_fiche: str):
    """
    Version RECOMMANDÉE : lit directement les vues SQL Server
    (calcul fait côté base -> rapide même sur de grosses fiches).
    Retourne (totaux, lignes_ingredients) ou (None, []) si fiche introuvable.
    """
    totaux = NutritionFiche.objects.filter(code_fiche=code_fiche).first()
    lignes = list(NutritionIngredient.objects.filter(code_fiche=code_fiche))
    return totaux, lignes


def get_nutrition_fiche_python(code_fiche: str):
    """
    Version alternative : calcul entièrement en Python à partir des
    tables brutes (Detaille_Fiche_Technique + Article_Nutrition).
    Pratique si les vues SQL ne sont pas encore déployées.
    """
    fiche = FicheTechnique.objects.filter(code=code_fiche).first()
    if not fiche:
        return None

    lignes = DetailleFicheTechnique.objects.filter(code_fiche=code_fiche)

    # Pré-charge le mapping article -> nutriment en un seul aller-retour DB
    codarts = [l.codart for l in lignes]
    mapping = {
        am.codart: am.code_nutriment
        for am in ArticleNutrition.objects.filter(codart__in=codarts).select_related('code_nutriment')
    }

    totaux = {
        'calories': Decimal('0'), 'proteines': Decimal('0'), 'lipides': Decimal('0'),
        'glucides': Decimal('0'), 'fibres': Decimal('0'), 'sodium': Decimal('0'),
    }
    detail = []
    ingredients_non_mappes = []

    for ligne in lignes:
        nutriment = mapping.get(ligne.codart)
        grammes = quantite_en_grammes(ligne.quantite, ligne.unite_grammage)

        if nutriment is None:
            ingredients_non_mappes.append(ligne.codart)
            valeurs = {'calories': 0, 'proteines': 0, 'lipides': 0, 'glucides': 0, 'fibres': 0, 'sodium': 0}
        else:
            valeurs = {
                'calories': grammes * nutriment.calories_100g / 100,
                'proteines': grammes * nutriment.proteines_100g / 100,
                'lipides': grammes * nutriment.lipides_100g / 100,
                'glucides': grammes * nutriment.glucides_100g / 100,
                'fibres': grammes * nutriment.fibres_100g / 100,
                'sodium': grammes * nutriment.sodium_100g / 100,
            }
            for k in totaux:
                totaux[k] += valeurs[k]

        detail.append({
            'codart': ligne.codart,
            'quantite': ligne.quantite,
            'unite': ligne.unite_grammage,
            'grammes': grammes,
            **valeurs,
        })

    nb_personnes = fiche.nombre_personne or Decimal('1')
    par_personne = {k: (v / nb_personnes if nb_personnes else 0) for k, v in totaux.items()}

    return {
        'fiche': fiche,
        'totaux': totaux,
        'par_personne': par_personne,
        'detail': detail,
        'ingredients_non_mappes': ingredients_non_mappes,
    }
