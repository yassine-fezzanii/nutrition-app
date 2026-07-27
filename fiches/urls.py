from django.urls import path
from . import views

app_name = 'fiches'

urlpatterns = [
    path('', views.liste_fiches, name='liste'),
    path('fiche/<str:code>/', views.detail_fiche, name='detail'),
    path('api/fiche/<str:code>/nutrition/', views.api_nutrition_fiche, name='api_nutrition'),
]
