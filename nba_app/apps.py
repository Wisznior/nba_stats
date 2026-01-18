from django.apps import AppConfig
import os
import sys

class NbaAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'nba_app'
    verbose_name = "Aplikacja NBA"

    def ready(self):
        if os.environ.get('RUN_MAIN', None) == 'true':    
            try:
                import updater

                print("Inicjalizacja Harmonogramu NBA")
                
                updater.start()
                
                print("Harmonogram aktywny. Aktualizacja o 06:00.")
                
            except ImportError:
                print("\nNie znaleziono pliku updater.py")
                
            except Exception as e:
                print(f"\nNie udało się uruchomić: {e}\n")
