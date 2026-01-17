from src.db_connect import get_connection
from src import nba_etl
import os
import sys

SQL_FILE_PATH = 'sql/struktura_bazy.sql'

def utworz_strukture_bazy(conn):
    pliki_sql = [
        'sql/struktura_bazy.sql', 
        'sql/logi_historia.sql', 
        'sql/widoki.sql', 
        'sql/funkcje_trigery.sql'
    ]
    
    cursor = conn.cursor()
    for plik in pliki_sql:
        try:
            with open(plik, 'r', encoding='utf-8') as f:
                sql_script = f.read()
                cursor.execute(sql_script)
                conn.commit()
                print(f"    Sukces: {plik}")
        except Exception as e:
            print(f"    Błąd w {plik}: {e}")
            conn.rollback()

def main():
    conn = None
    try:
        conn = get_connection()
        conn.autocommit = False
        cursor = conn.cursor()
        
        utworz_strukture_bazy(conn)
        
        print("\naktualizacja danych NBA")
        
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

        nba_etl.aktualizuj_kontuzje(cursor)
        conn.commit()

        nba_etl.uzupelnij_brakujace_kontrakty(cursor)
        conn.commit()

        print("\nproces zakonczony pomyslnie")

    except KeyboardInterrupt:
        print("\nprzerwano przez użytkownika")
    except Exception as e:
        print(f"\nwystapil blad: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()
            print("połączenie z baza zamkniete")

if __name__ == "__main__":
    main()