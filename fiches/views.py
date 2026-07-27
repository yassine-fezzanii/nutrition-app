from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from django.http import JsonResponse

from .models import FicheTechnique
from .services import get_nutrition_fiche_sql


def liste_fiches(request):
    """Page d'accueil : liste + filtre (équivalent de l'écran 'GESTION DES FICHES TECHNIQUES')."""
    q = request.GET.get('q', '').strip()
    etat = request.GET.get('etat', 'tous')  # actif / non_actif / tous

    fiches = FicheTechnique.objects.all().order_by('code')

    if q:
        fiches = fiches.filter(Q(code__icontains=q) | Q(designation__icontains=q))

    if etat == 'actif':
        fiches = fiches.filter(actif=True)
    elif etat == 'non_actif':
        fiches = fiches.filter(actif=False)

    return render(request, 'fiches/liste_fiches.html', {
        'fiches': fiches,
        'q': q,
        'etat': etat,
    })


def detail_fiche(request, code):
    """Détail d'une fiche + panneau nutritionnel calculé automatiquement."""
    fiche = get_object_or_404(FicheTechnique, code=code)
    totaux, lignes_nutrition = get_nutrition_fiche_sql(code)

    return render(request, 'fiches/detail_fiche.html', {
        'fiche': fiche,
        'totaux': totaux,
        'lignes_nutrition': lignes_nutrition,
    })


def api_nutrition_fiche(request, code):
    """Endpoint JSON, réutilisable par le prototype HTML / futur appel AJAX."""
    totaux, lignes = get_nutrition_fiche_sql(code)
    if not totaux:
        return JsonResponse({'error': 'Fiche introuvable ou sans ingrédient mappé'}, status=404)

    return JsonResponse({
        'code_fiche': totaux.code_fiche,
        'designation': totaux.designation,
        'nombre_personne': float(totaux.nombre_personne),
        'totaux': {
            'calories': float(totaux.calories_total),
            'proteines': float(totaux.proteines_total),
            'lipides': float(totaux.lipides_total),
            'glucides': float(totaux.glucides_total),
            'fibres': float(totaux.fibres_total),
            'sodium': float(totaux.sodium_total),
        },
        'par_personne': {
            'calories': float(totaux.calories_personne),
            'proteines': float(totaux.proteines_personne),
            'lipides': float(totaux.lipides_personne),
            'glucides': float(totaux.glucides_personne),
            'fibres': float(totaux.fibres_personne),
            'sodium': float(totaux.sodium_personne),
        },
        'tous_ingredients_mappes': bool(totaux.tous_ingredients_mappes),
    })
