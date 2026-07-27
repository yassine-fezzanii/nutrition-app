from django.contrib import admin
from .models import (
    FicheTechnique, DetailleFicheTechnique, NatureArticleCuisine,
    TableCompositionNutritionnelle, ArticleNutrition,
)


@admin.register(TableCompositionNutritionnelle)
class TableCompositionNutritionnelleAdmin(admin.ModelAdmin):
    list_display = ('code_nutriment', 'libelle', 'calories_100g', 'proteines_100g', 'lipides_100g', 'glucides_100g')
    search_fields = ('code_nutriment', 'libelle')


@admin.register(ArticleNutrition)
class ArticleNutritionAdmin(admin.ModelAdmin):
    list_display = ('codart', 'code_nutriment')
    search_fields = ('codart',)
    autocomplete_fields = ('code_nutriment',)


@admin.register(FicheTechnique)
class FicheTechniqueAdmin(admin.ModelAdmin):
    list_display = ('code', 'designation', 'nombre_personne', 'cout_total_fiche', 'actif', 'valider')
    search_fields = ('code', 'designation')

    def has_add_permission(self, request):
        return False  # les fiches sont créées par l'application métier existante

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(NatureArticleCuisine)
class NatureArticleCuisineAdmin(admin.ModelAdmin):
    list_display = ('code', 'designation', 'unimes')
    search_fields = ('code', 'designation')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
