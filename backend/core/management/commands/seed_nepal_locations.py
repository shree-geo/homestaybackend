import csv
import json
import os
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from core.models import Country, State, District, Municipality


class Command(BaseCommand):
    help = 'Seed Nepal country, states (provinces). Optionally load districts and municipalities from CSV or JSON.'

    def add_arguments(self, parser):
        parser.add_argument('--load-districts', help='Path to CSV/JSON file with districts', default=None)
        parser.add_argument('--load-municipalities', help='Path to CSV/JSON file with municipalities', default=None)
        parser.add_argument('--use-json', help='Path to combined provinces JSON (provinces->districts->local_levels)', default=None)
        parser.add_argument('--force', help='Delete existing Nepal data before seeding', action='store_true')

    def handle(self, *args, **options):
        load_districts = options.get('load_districts')
        load_municipalities = options.get('load_municipalities')
        use_json = options.get('use_json')
        force = options.get('force')

        with transaction.atomic():
            nepal, created = Country.objects.get_or_create(name='Nepal', defaults={'code': 'NP'})
            if created:
                self.stdout.write(self.style.SUCCESS('Created country: Nepal'))
            else:
                self.stdout.write('Country Nepal already exists')

            # If force, remove states/districts/municipalities tied to Nepal
            if force:
                State.objects.filter(country=nepal).delete()
                District.objects.filter(state__country=nepal).delete()
                Municipality.objects.filter(district__state__country=nepal).delete()
                self.stdout.write(self.style.WARNING('Existing Nepal location data deleted'))

            # Nepal provinces (7) - keep as fallback in case JSON not provided
            provinces = [
                'Province No. 1',
                'Madhesh Province',
                'Bagmati Province',
                'Gandaki Province',
                'Lumbini Province',
                'Karnali Province',
                'Sudurpashchim Province',
            ]

            # If using combined JSON, prefer that path
            if use_json:
                self._load_from_json(nepal, use_json)
            else:
                for name in provinces:
                    state, screated = State.objects.get_or_create(country=nepal, name=name)
                    if screated:
                        self.stdout.write(self.style.SUCCESS(f'Created state: {name}'))

                # Optionally load districts
                if load_districts:
                    self._load_districts(nepal, load_districts)

                # Optionally load municipalities
                if load_municipalities:
                    self._load_municipalities(nepal, load_municipalities)

            self.stdout.write(self.style.SUCCESS('Seeding complete'))

    def _load_districts(self, country, path):
        path = os.path.abspath(path)
        if not os.path.exists(path):
            raise CommandError(f'Districts file not found: {path}')

        ext = os.path.splitext(path)[1].lower()
        items = []
        if ext == '.csv':
            with open(path, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Expecting columns: state_name,district_name,code?
                    items.append(row)
        elif ext in ('.json', '.ndjson'):
            with open(path, encoding='utf-8') as f:
                items = json.load(f)
        else:
            raise CommandError('Unsupported file type for districts; use CSV or JSON')

        created = 0
        for row in items:
            state_name = row.get('state') or row.get('state_name') or row.get('province')
            district_name = row.get('district') or row.get('district_name') or row.get('name')
            if not state_name or not district_name:
                continue
            state = State.objects.filter(country=country, name__icontains=state_name).first()
            if not state:
                self.stdout.write(self.style.ERROR(f'State not found for district row: {state_name}'))
                continue
            d, dcreated = District.objects.get_or_create(state=state, name=district_name)
            if dcreated:
                created += 1
        self.stdout.write(self.style.SUCCESS(f'Imported {created} districts'))

    def _load_municipalities(self, country, path):
        path = os.path.abspath(path)
        if not os.path.exists(path):
            raise CommandError(f'Municipalities file not found: {path}')

        ext = os.path.splitext(path)[1].lower()
        items = []
        if ext == '.csv':
            with open(path, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Expecting columns: district_name,municipality_name,code?
                    items.append(row)
        elif ext in ('.json', '.ndjson'):
            with open(path, encoding='utf-8') as f:
                items = json.load(f)
        else:
            raise CommandError('Unsupported file type for municipalities; use CSV or JSON')

        created = 0
        for row in items:
            district_name = row.get('district') or row.get('district_name') or row.get('district_raw')
            municipality_name = row.get('municipality') or row.get('municipality_name') or row.get('name')
            code = row.get('muni_code') or row.get('code')
            if not district_name or not municipality_name:
                continue
            district = District.objects.filter(name__icontains=district_name, state__country=country).first()
            if not district:
                self.stdout.write(self.style.ERROR(f'District not found for municipality row: {district_name}'))
                continue
            m, mcreated = Municipality.objects.get_or_create(district=district, name=municipality_name, defaults={'code': code})
            if mcreated:
                created += 1
        self.stdout.write(self.style.SUCCESS(f'Imported {created} municipalities'))

    def _load_from_json(self, country, path):
        path = os.path.abspath(path)
        if not os.path.exists(path):
            raise CommandError(f'JSON file not found: {path}')

        with open(path, encoding='utf-8') as f:
            try:
                data = json.load(f)
            except Exception as e:
                raise CommandError(f'Failed to parse JSON: {e}')

        created_states = 0
        created_districts = 0
        created_munis = 0

        for province in data:
            # province name: try English title, else Nepali title
            p_name = province.get('title_en') or province.get('title') or province.get('name')
            if not p_name:
                continue
            state, screated = State.objects.get_or_create(country=country, name=p_name)
            if screated:
                created_states += 1

            for district in province.get('districts', []):
                d_name = district.get('title_en') or district.get('title') or district.get('name')
                if not d_name:
                    continue
                d, dcreated = District.objects.get_or_create(state=state, name=d_name)
                if dcreated:
                    created_districts += 1

                for ll in district.get('local_levels', []) or []:
                    m_name = ll.get('title_en') or ll.get('title') or ll.get('name')
                    m_code = ll.get('muni_code') or ll.get('ll_id') or ll.get('code')
                    if not m_name:
                        continue
                    m, mcreated = Municipality.objects.get_or_create(district=d, name=m_name, defaults={'code': m_code})
                    if mcreated:
                        created_munis += 1

        self.stdout.write(self.style.SUCCESS(f'Imported states: {created_states}, districts: {created_districts}, municipalities: {created_munis}'))
