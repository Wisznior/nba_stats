import schedule
import time
import threading
import sys
import os
from src import nba_etl, db_connect 

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def zadanie_etl():
    print("\n06:00 - auto pobieranie danych z NBA")
    conn = None
    try:
        conn = db_connect.get_connection()
        conn.autocommit = False
        cursor = conn.cursor()

        nba_etl.aktualizuj_zespoly(cursor)
        conn.commit()
        
        nba_etl.aktualizuj_zawodnikow(cursor)
        conn.commit()
        
        nba_etl.aktualizuj_trenerow(cursor)
        conn.commit()

        nba_etl.aktualizuj_mecze_i_statystyki(cursor)
        conn.commit()
        
        nba_etl.aktualizuj_kontrakty(cursor)
        conn.commit()

        print("baza danych zaktualizowana pomyślnie")

    except Exception as e:
        print(f"błąd {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

def run_schedule_loop():
    while True:
        schedule.run_pending()
        time.sleep(60)

def start():
    schedule.every().day.at("06:00").do(zadanie_etl)
    
    scheduler_thread = threading.Thread(target=run_schedule_loop)
    scheduler_thread.daemon = True
    scheduler_thread.start()