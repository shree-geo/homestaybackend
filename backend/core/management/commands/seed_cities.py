import uuid
from django.core.management.base import BaseCommand
from core.models import City, District

class Command(BaseCommand):
    help = "Seed cities based on districts"

    def handle(self, *args, **kwargs):
        # Define your district -> cities mapping
        district_cities = {
            # Mountain & Trekking Tourism
            "Solukhumbu": ["Namche Bazaar", "Lukla"],
            "Manang": ["Manang Village", "Pisang"],
            "Mustang": ["Jomsom", "Kagbeni", "Lo-Manthang"],
            "Dolpa": ["Dunai"],
            "Rasuwa": ["Dhunche"],

            # Hill & Cultural Tourism
            "Kathmandu": ["Kathmandu", "Kirtipur", "Budhanilkantha"],
            "Lalitpur": ["Patan"],
            "Bhaktapur": ["Bhaktapur"],
            "Kaski": ["Pokhara"],
            "Lamjung": ["Besisahar"],
            "Gorkha": ["Gorkha Bazaar"],
            "Syangja": ["Putalibazar"],
            "Palpa": ["Tansen"],
            "Ilam": ["Ilam Bazaar"],
            "Dhankuta": ["Dhankuta Bazaar"],

            # Terai & Wildlife / Nature Tourism
            "Chitwan": ["Bharatpur", "Sauraha"],
            "Bardiya": ["Gulariya", "Thakurdwara"],
            "Jhapa": ["Birtamod", "Damak"],
            "Sunsari": ["Dharan", "Itahari"],
            "Rupandehi": ["Butwal", "Lumbini"],
            "Kanchanpur": ["Mahendranagar (Bhimdatta)"],

            "Kapilvastu": ["Taulihawa"],
            "Sindhupalchowk": ["Chautara"],
            "Makwanpur": ["Hetauda"],
        }

        created_count = 0

        for district_name, cities in district_cities.items():
            try:
                district = District.objects.get(name=district_name)
            except District.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"District '{district_name}' not found. Skipping."))
                continue

            for city_name in cities:
                city, created = City.objects.get_or_create(
                    district=district,
                    name=city_name
                )
                if created:
                    created_count += 1
                    self.stdout.write(self.style.SUCCESS(f"Created city: {city_name}"))

        self.stdout.write(self.style.SUCCESS(f"Seeding complete! Total cities created: {created_count}"))
