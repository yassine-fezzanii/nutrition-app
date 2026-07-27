"""
Commande : python manage.py import_ciqual chemin/vers/ciqual.csv

Importe un extrait CIQUAL (export CSV, séparateur ';', encodage
Windows-1252 comme les exports officiels ANSES) dans
Table_Composition_Nutritionnelle. Adapter les noms de colonnes
`COL_MAP` selon le fichier CIQUAL téléchargé (le nom des colonnes
change légèrement selon les millésimes du fichier).
"""
import csv

from django.core.management.base import BaseCommand
from fiches.models import TableCompositionNutritionnelle

# Nom des colonnes attendues dans le CSV CIQUAL -> champ du modèle
COL_MAP = {
    'alim_nom_fr': 'libelle',
    'energie_kcal_100g': 'calories_100g',
    'proteines_100g': 'proteines_100g',
    'lipides_100g': 'lipides_100g',
    'glucides_100g': 'glucides_100g',
    'fibres_100g': 'fibres_100g',
    'sodium_100g': 'sodium_100g',
}


class Command(BaseCommand):
    help = "Importe un extrait CIQUAL (CSV) dans Table_Composition_Nutritionnelle"

    def add_arguments(self, parser):
        parser.add_argument('csv_path', type=str)
        parser.add_argument('--encoding', type=str, default='cp1252')

    def handle(self, *args, **options):
        path = options['csv_path']
        created, updated = 0, 0

        with open(path, encoding=options['encoding']) as f:
            reader = csv.DictReader(f, delimiter=';')
            for i, row in enumerate(reader, start=1):
                try:
                    def to_float(v):
                        v = (v or '0').replace(',', '.').replace('traces', '0').strip()
                        try:
                            return float(v)
                        except ValueError:
                            return 0.0

                    code = f'CIQ{i:05d}'
                    obj, was_created = TableCompositionNutritionnelle.objects.update_or_create(
                        code_nutriment=code,
                        defaults={
                            'libelle': row.get('alim_nom_fr', '')[:150],
                            'calories_100g': to_float(row.get('energie_kcal_100g')),
                            'proteines_100g': to_float(row.get('proteines_100g')),
                            'lipides_100g': to_float(row.get('lipides_100g')),
                            'glucides_100g': to_float(row.get('glucides_100g')),
                            'fibres_100g': to_float(row.get('fibres_100g')),
                            'sodium_100g': to_float(row.get('sodium_100g')),
                            'source': 'CIQUAL',
                        }
                    )
                    created += was_created
                    updated += not was_created
                except Exception as e:
                    self.stderr.write(f'Ligne {i} ignorée : {e}')

        self.stdout.write(self.style.SUCCESS(
            f'Import terminé : {created} créés, {updated} mis à jour.'
        ))
