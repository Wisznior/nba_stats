from nba_api.stats.static import teams, players
from nba_api.stats.endpoints import leaguegamelog, leaguestandings, commonteamroster, leaguedashplayerbiostats, commonplayerinfo
from psycopg2.extras import execute_values
import pandas as pd
import time
import requests
from bs4 import BeautifulSoup
import random
import unicodedata

SEZON_AKTUALNY  = '2025-26'

def time_str_to_seconds(time_str):
    if pd.isna(time_str) or time_str is None:
        return 0
    
    s = str(time_str).strip()
    
    if ':' in s:
        try:
            parts = s.split(':')
            minutes = int(parts[0])
            seconds = int(parts[1])
            return minutes * 60 + seconds
        except:
            return 0
            
    try:
        val = float(s)
        return int(val * 60)
    except:
        return 0

def normalize_name(text):
    if not text: return ""
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
    text = text.lower()
    suffixes = [' jr.', ' sr.', ' ii', ' iii', ' iv', ' jr', ' sr']
    for s in suffixes:
        if text.endswith(s):
            text = text[:-len(s)]
            break
    text = text.replace('.', '').replace(' ', '').replace('-', '').replace("'", "")
    return text

def aktualizuj_zespoly(cursor):
    print("Aktualizacja zespołów")
    nba_teams = teams.get_teams()
    try:
        standings = leaguestandings.LeagueStandings(season=SEZON_AKTUALNY).get_data_frames()[0]
        conf_map = dict(zip(standings['TeamID'], standings['Conference']))
    except Exception:
        print("nie udało się pobrać konferencji z API")
        conf_map = {}
    
    data = []
    for t in nba_teams:
        t_id = t['id']
        conf_ang = conf_map.get(t_id, 'NBA')
        konferencja = 'Wschodnia' if conf_ang == 'East' else 'Zachodnia'
        
        data.append((t_id, t['full_name'], t['city'], t['abbreviation'], konferencja))

    insert = """
        INSERT INTO zespoly (id_zespolu, nazwa, miasto, skrot, konferencja)
        VALUES %s
        ON CONFLICT (id_zespolu) DO UPDATE
        SET konferencja = EXCLUDED.konferencja;
    """
    execute_values(cursor, insert, data)
    print(f"zaktualizowano {len(data)} zespołow")

def aktualizuj_zawodnikow(cursor):
    print("\npobranie zawodnikow")
    
    active_players = players.get_active_players()
    print(f"znaleziono {len(active_players)} zawodnikow")
    data_to_insert = []
    players_with_data = set()
    
    try:
        time.sleep(1)
        bio_stats = leaguedashplayerbiostats.LeagueDashPlayerBioStats(season=SEZON_AKTUALNY).get_data_frames()[0]
        
        country_map = dict(zip(bio_stats['PLAYER_ID'], bio_stats['COUNTRY']))
        
        for player in active_players:
            player_id = player['id']
            first_name = player['first_name']
            last_name = player['last_name']
    
            country = country_map.get(player_id)
            
            if country and not pd.isna(country):
                data_to_insert.append((player_id, first_name, last_name, True, country))
                players_with_data.add(player_id)
        
    except Exception as e:
        print(f"{e}")
    
    players_without_data = [p for p in active_players if p['id'] not in players_with_data]
    
    if players_without_data:
        for i, player in enumerate(players_without_data, 1):
            player_id = player['id']
            first_name = player['first_name']
            last_name = player['last_name']
            
            try:
                time.sleep(0.6)

                player_info = commonplayerinfo.CommonPlayerInfo(player_id=player_id)
                info_df = player_info.get_data_frames()[0]
                
                if not info_df.empty:
                    country = info_df.iloc[0].get('COUNTRY', 'Nieznany')
                    if pd.isna(country) or country == '':
                        country = 'USA'
                else:
                    country = 'Nieznany'
                
                data_to_insert.append((player_id, first_name, last_name, True, country))
                
            except Exception as e:
                print(f"blad {first_name} {last_name}: {e}")
                data_to_insert.append((player_id, first_name, last_name, True, 'Nieznany'))
    
    if data_to_insert:    
        insert = """
            INSERT INTO zawodnicy (id_zawodnika, imie, nazwisko, czy_aktywny, kraj_pochodzenia)
            VALUES %s
            ON CONFLICT (id_zawodnika) DO UPDATE
            SET
                czy_aktywny = EXCLUDED.czy_aktywny,
                kraj_pochodzenia = EXCLUDED.kraj_pochodzenia;
        """
        
        execute_values(cursor, insert, data_to_insert)
        
def aktualizuj_trenerow(cursor):
    print("\naktualizacja trenerow")

    rok_pocz = int(SEZON_AKTUALNY.split('-')[0]) 
    cursor.execute(
        "INSERT INTO sezony (kod_sezonu, rok_poczatkowy, opis) VALUES (%s, %s, %s) ON CONFLICT (kod_sezonu) DO NOTHING",
        (SEZON_AKTUALNY, rok_pocz, 'Sezon Regularny')
    )
    
    cursor.execute("SELECT id_sezonu FROM sezony WHERE kod_sezonu = %s", (SEZON_AKTUALNY,))
    db_sezon_id = cursor.fetchone()[0]

    cursor.execute("SELECT id_zespolu FROM zespoly")
    zespoly_ids = [row[0] for row in cursor.fetchall()]
    
    osoby_trenerow = set()
    zatrudnienie_data = []
    bledy = 0
    
    for team_id in zespoly_ids:
        try:            
            time.sleep(0.4)
            roster = commonteamroster.CommonTeamRoster(season=SEZON_AKTUALNY, team_id=team_id)
            frames = roster.get_data_frames()
            if len(frames) < 2: continue

            coaches_df = frames[1] 
            if coaches_df.empty: continue

            for _, row in coaches_df.iterrows():
                coach_id = row.get('COACH_ID')
                if not coach_id: continue
                
                first_name = row.get('FIRST_NAME')
                last_name = row.get('LAST_NAME')
                coach_type = row.get('COACH_TYPE')
                is_head = True if coach_type == 'Head Coach' else False
                
                osoby_trenerow.add((coach_id, first_name, last_name))
                zatrudnienie_data.append((coach_id, team_id, db_sezon_id, is_head))
                        
        except Exception as e:
            bledy += 1
            print(f"Blad dla zespolu {team_id}: {e}")

    if osoby_trenerow:
        q_osoby = """
            INSERT INTO trenerzy (id_trenera, imie, nazwisko)
            VALUES %s
            ON CONFLICT (id_trenera) DO NOTHING;
        """
        execute_values(cursor, q_osoby, list(osoby_trenerow))

    if zatrudnienie_data:
        q_zatrudnienie = """
            INSERT INTO zatrudnienie_trenerow (id_trenera, id_zespolu, id_sezonu, czy_glowny)
            VALUES %s
            ON CONFLICT (id_trenera, id_zespolu, id_sezonu) 
            DO UPDATE SET czy_glowny = EXCLUDED.czy_glowny;
        """
        execute_values(cursor, q_zatrudnienie, zatrudnienie_data)
        print(f"zaktualizowano {len(zatrudnienie_data)} rekordow zatrudnienia")

def aktualizuj_mecze_i_statystyki(cursor):
    print("\naktualizacja meczów i statystyk")
    
    rok_pocz = int(SEZON_AKTUALNY.split('-')[0]) 
    cursor.execute(
        "INSERT INTO sezony (kod_sezonu, rok_poczatkowy, opis) VALUES (%s, %s, %s) ON CONFLICT (kod_sezonu) DO NOTHING",
        (SEZON_AKTUALNY, rok_pocz, 'Regular Season')
    )
    cursor.execute("SELECT id_sezonu FROM sezony WHERE kod_sezonu = %s", (SEZON_AKTUALNY,))
    db_sezon_id = cursor.fetchone()[0]

    print("pobieranie wyników")
    
    cursor.execute("SELECT id_meczu FROM mecze WHERE id_sezonu = %s AND wynik_gospodarz IS NOT NULL", (db_sezon_id,))
    zakonczone_mecze = set(str(row[0]) for row in cursor.fetchall())

    team_logs = leaguegamelog.LeagueGameLog(season=SEZON_AKTUALNY, player_or_team_abbreviation='T').get_data_frames()[0]
    
    team_logs['GAME_ID'] = team_logs['GAME_ID'].astype(int).astype(str)

    team_logs.drop_duplicates(subset=['GAME_ID', 'TEAM_ID'], inplace=True)
    new_team_logs = team_logs[~team_logs['GAME_ID'].isin(zakonczone_mecze)]

    games_data = []
    
    if not new_team_logs.empty:
        grouped_games = new_team_logs.groupby('GAME_ID')

        for game_id, rows in grouped_games:
            if len(rows) != 2: continue
            
            h_data = None
            a_data = None

            home_candidates = rows[rows['MATCHUP'].str.contains(' vs. ', case=False, regex=False)]
            
            if not home_candidates.empty:
                h_data = home_candidates.iloc[0]
                a_data = rows.drop(h_data.name).iloc[0]
            else:
                away_candidates = rows[rows['MATCHUP'].str.contains(' @ ', case=False, regex=False)]
                if not away_candidates.empty:
                    a_data = away_candidates.iloc[0]
                    h_data = rows.drop(a_data.name).iloc[0]
                else:
                    h_data = rows.iloc[0]
                    a_data = rows.iloc[1]

            games_data.append((
                int(game_id), 
                db_sezon_id, 
                int(h_data['TEAM_ID']), 
                int(a_data['TEAM_ID']), 
                str(h_data['GAME_DATE']), 
                int(h_data['PTS']), 
                int(a_data['PTS'])
            ))

        if games_data:
            insert_games = """
                INSERT INTO mecze (id_meczu, id_sezonu, id_zespolu_gospodarz, id_zespolu_gosc, data_meczu, wynik_gospodarz, wynik_gosc)
                VALUES %s 
                ON CONFLICT (id_meczu) DO UPDATE 
                SET 
                    wynik_gospodarz = EXCLUDED.wynik_gospodarz,
                    wynik_gosc = EXCLUDED.wynik_gosc;
            """
            execute_values(cursor, insert_games, games_data)
            print(f"zaktualizowano {len(games_data)} meczow")
    else:
        print("brak nowych wyników")

    print("\npobieranie statystyk")
    player_logs = leaguegamelog.LeagueGameLog(season=SEZON_AKTUALNY, player_or_team_abbreviation='P').get_data_frames()[0]
    
    player_logs['GAME_ID'] = player_logs['GAME_ID'].astype(int)
    
    player_logs.drop_duplicates(subset=['GAME_ID', 'PLAYER_ID'], inplace=True)
    
    cursor.execute("SELECT DISTINCT id_meczu FROM statystyki_zawodnikow")
    mecze_ze_statystykami = set(row[0] for row in cursor.fetchall())
    
    cursor.execute("SELECT id_meczu FROM mecze")
    mecze_w_bazie = set(row[0] for row in cursor.fetchall())
    
    new_player_logs = player_logs[
        (~player_logs['GAME_ID'].isin(mecze_ze_statystykami)) & 
        (player_logs['GAME_ID'].isin(mecze_w_bazie))
    ]
    
    if new_player_logs.empty:
        print("brak nowych statystyk")
        return

    players_in_logs = new_player_logs[['PLAYER_ID', 'PLAYER_NAME']].drop_duplicates()
    missing_players_data = []
    for _, row in players_in_logs.iterrows():
        p_id = int(row['PLAYER_ID'])
        full_name = row['PLAYER_NAME']
        parts = full_name.split(' ', 1)
        fname = parts[0]
        lname = parts[1] if len(parts) > 1 else ''
        missing_players_data.append((p_id, fname, lname, False, 'Nieznany'))

    insert_missing = """
        INSERT INTO zawodnicy (id_zawodnika, imie, nazwisko, czy_aktywny, kraj_pochodzenia)
        VALUES %s ON CONFLICT (id_zawodnika) DO NOTHING;
    """
    execute_values(cursor, insert_missing, missing_players_data)

    stats_data = []
    for _, row in new_player_logs.iterrows():
        pm = int(row['PLUS_MINUS']) if not pd.isna(row['PLUS_MINUS']) else 0
        stats_data.append((
            int(row['GAME_ID']), 
            int(row['PLAYER_ID']), 
            int(row['TEAM_ID']),
            int(row['PTS']), 
            int(row['AST']), 
            int(row['REB']), 
            int(row['STL']), 
            int(row['BLK']), 
            int(row['TOV']), 
            time_str_to_seconds(row['MIN']),
            pm,
            int(row['FGM']), int(row['FGA']),
            int(row['FG3M']), int(row['FG3A']),
            int(row['FTM']), int(row['FTA'])
        ))

    insert_stats = """
        INSERT INTO statystyki_zawodnikow 
        (id_meczu, id_zawodnika, id_zespolu, punkty, asysty, zbiorki, przechwyty, bloki, straty, 
         sekundy_na_parkiecie, plus_minus, rzuty_celne, rzuty_oddane, rzuty_za_3_celne, rzuty_za_3_oddane, rzuty_wolne_celne, rzuty_wolne_oddane)
        VALUES %s
        ON CONFLICT (id_meczu, id_zawodnika) DO NOTHING;
    """
    execute_values(cursor, insert_stats, stats_data)
    print(f"dodano {len(stats_data)} statystyk")

def aktualizuj_kontrakty(cursor):
    print("\naktualizacja kontraktow")
    
    cursor.execute("SELECT id_sezonu FROM sezony WHERE kod_sezonu = %s", (SEZON_AKTUALNY,))
    res = cursor.fetchone()
    if not res:
        print("brak sezonu w bazie")
        return
    db_sezon_id = res[0]

    cursor.execute("SELECT id_zawodnika, imie, nazwisko FROM zawodnicy")
    gracze_db = cursor.fetchall()
    mapa_graczy = {}
    for row in gracze_db:
        klucz = normalize_name(f"{row[1]} {row[2]}")
        mapa_graczy[klucz] = row[0]

    cursor.execute("SELECT id_zespolu, nazwa FROM zespoly")
    zespoly_db = cursor.fetchall()
    mapa_zespolow = {}
    lista_id_zespolow = [] 
    for row in zespoly_db:
        norm_db_name = row[1].lower().replace(' ', '') 
        mapa_zespolow[norm_db_name] = row[0]
        lista_id_zespolow.append(row[0])

    id_clippers = mapa_zespolow.get('losangelesclippers')
    TEAM_ALIASES = {
        'laclippers': id_clippers,
        'lakers': mapa_zespolow.get('losangeleslakers'),
        'nyknicks': mapa_zespolow.get('newyorkknicks'),
        'utah': mapa_zespolow.get('utahjazz'),
        'washington': mapa_zespolow.get('washingtonwizards'),
        'gswarriors': mapa_zespolow.get('goldenstatewarriors'),
        'nopelicans': mapa_zespolow.get('neworleanspelicans'),
        'okthunder': mapa_zespolow.get('oklahomacitythunder'),
        'saspurs': mapa_zespolow.get('sanantoniospurs'),
    }
    for alias_name, team_id in TEAM_ALIASES.items():
        if team_id: mapa_zespolow[alias_name] = team_id

    headers = {'User-Agent': 'Mozilla/5.0'}
    kontrakty_data = []
    
    print("pobieranie z ESPN")
    for page in range(1, 25):
        try:
            url = f"https://www.espn.com/nba/salaries/_/page/{page}"
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200: break
            
            soup = BeautifulSoup(response.content, 'html.parser')
            table = soup.find('table', {'class': 'tablehead'})
            if not table: break
            rows = table.find_all('tr')
            found_on_page = 0
            
            for row in rows:
                if 'colhead' in row.get('class', []) or 'stathead' in row.get('class', []): continue
                cols = row.find_all('td')
                if len(cols) < 4: continue
                
                name_raw = cols[1].get_text()
                team_raw = cols[2].get_text()
                salary_raw = cols[3].get_text()
                
                if ',' in name_raw: name_clean = name_raw.split(',')[0]
                else: name_clean = name_raw
                
                player_key = normalize_name(name_clean)
                team_key = team_raw.lower().replace(' ', '')
                
                if '$' in salary_raw:
                    try:
                        kwota = float(salary_raw.replace('$', '').replace(',', ''))
                        p_id = mapa_graczy.get(player_key)
                        t_id = mapa_zespolow.get(team_key)
                        if p_id and t_id:
                            kontrakty_data.append((p_id, t_id, db_sezon_id, kwota, 'Gwarantowany'))
                            found_on_page += 1
                    except ValueError: continue

            if found_on_page == 0 and page > 15: break
        except Exception: break

    cursor.execute("DELETE FROM kontrakty WHERE id_sezonu = %s", (db_sezon_id,))
    if kontrakty_data:
        execute_values(cursor, "INSERT INTO kontrakty (id_zawodnika, id_zespolu, id_sezonu, kwota, typ_kontraktu) VALUES %s", kontrakty_data)
        print(f"zapisano {len(kontrakty_data)} kontraktow")

    print("uzupełnianie na podstawie statystyk")
    query_missing_stats = """
        SELECT DISTINCT ON (s.id_zawodnika) s.id_zawodnika, s.id_zespolu
        FROM statystyki_zawodnikow s
        LEFT JOIN kontrakty k ON s.id_zawodnika = k.id_zawodnika AND k.id_sezonu = %s
        WHERE k.id_kontraktu IS NULL
        ORDER BY s.id_zawodnika, s.id_meczu DESC;
    """
    cursor.execute(query_missing_stats, (db_sezon_id,))
    missing_via_stats = cursor.fetchall()
    
    data_phase2 = []
    for pid, tid in missing_via_stats:
        data_phase2.append((pid, tid, db_sezon_id, random.randint(400000, 600000), 'Two-Way (Stats)'))
    
    if data_phase2:
        execute_values(cursor, "INSERT INTO kontrakty (id_zawodnika, id_zespolu, id_sezonu, kwota, typ_kontraktu) VALUES %s", data_phase2)
        print(f"dodano {len(data_phase2)} kontraktow z aktywnosci")


def aktualizuj_kontuzje(cursor):
    print("\naktualizowanie kontuzji")
    
    cursor.execute("SELECT id_zawodnika, imie, nazwisko FROM zawodnicy")
    gracze_db = cursor.fetchall()
    mapa_graczy = {}
    
    for row in gracze_db:
        klucz = normalize_name(f"{row[1]} {row[2]}")
        mapa_graczy[klucz] = row[0]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    kontuzje_data = []
    matched_players = 0
    unmatched_players = []
    
    try:
        url = "https://www.espn.com/nba/injuries"

        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            print(f"Bladd HTTP: {response.status_code}")
            return
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        try:
            with open('espn_injuries_backup.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
        except:
            pass
        
        injury_sections = soup.find_all('div', class_='ResponsiveTable')
        
        if not injury_sections:
            injury_sections = soup.find_all('table')
        
        for section in injury_sections:
            rows = section.find_all('tr')
            
            for row in rows:
                cells = row.find_all('td')
                
                if len(cells) >= 4:
                    try:
                        name_cell = cells[0].get_text(strip=True)
                        position = cells[1].get_text(strip=True) if len(cells) > 1 else ''
                        injury_desc = cells[2].get_text(strip=True) if len(cells) > 2 else 'Unknown'
                        status = cells[3].get_text(strip=True) if len(cells) > 3 else 'Out'
                        date_info = cells[4].get_text(strip=True) if len(cells) > 4 else ''
                        
                        if name_cell.lower() in ['name', 'player', '', 'position']:
                            continue
                        
                        player_key = normalize_name(name_cell)
                        player_id = mapa_graczy.get(player_key)
                        
                        if player_id:
                            matched_players += 1
                            
                            status_map = {
                                'out': 'Out',
                                'doubtful': 'Doubtful',
                                'questionable': 'Questionable',
                                'probable': 'Probable',
                                'day to day': 'Day-to-Day',
                                'day-to-day': 'Day-to-Day',
                                'gtd': 'Game Time Decision',
                                'out indefinitely': 'Out',
                                'out for season': 'Out'
                            }
                            
                            mapped_status = status_map.get(status.lower(), status)
                            
                            expected_return = None
                            if date_info and date_info.lower() not in ['', '-', 'unknown', 'n/a']:
                                try:
                                    from datetime import datetime, timedelta
                                    
                                    if 'week' in date_info.lower():
                                        weeks_str = date_info.split()[0]
                                        if '-' in weeks_str:
                                            weeks = int(weeks_str.split('-')[0])
                                        else:
                                            weeks = int(weeks_str)
                                        expected_return = (datetime.now() + timedelta(weeks=weeks)).date()
                                    
                                    elif 'day' in date_info.lower():
                                        days_str = date_info.split()[0]
                                        if '-' in days_str:
                                            days = int(days_str.split('-')[0])
                                        else:
                                            days = int(days_str)
                                        expected_return = (datetime.now() + timedelta(days=days)).date()
                                    
                                    elif 'month' in date_info.lower():
                                        months_str = date_info.split()[0]
                                        if '-' in months_str:
                                            months = int(months_str.split('-')[0])
                                        else:
                                            months = int(months_str)
                                        expected_return = (datetime.now() + timedelta(days=months*30)).date()
                                
                                except Exception as e:
                                    expected_return = None
                            
                            kontuzje_data.append((
                                player_id,
                                pd.Timestamp.now().date(),
                                f"{injury_desc} ({position})",
                                mapped_status,
                                expected_return
                            ))
                        else:
                            unmatched_players.append(name_cell)
                    
                    except Exception as e:
                        print(f"blad: {e}")
                        continue
        
        if kontuzje_data:
            cursor.execute("""
                UPDATE kontuzje 
                SET status = 'Wyleczony' 
                WHERE status IS NOT NULL 
                  AND status != 'Wyleczony'
            """)
            wyleczonych = cursor.rowcount
            print(f"wyleczonych: {wyleczonych} starych kontuzji")

            insert_query = """
                INSERT INTO kontuzje (id_zawodnika, data_zgloszenia, opis_kontuzji, status, przewidywany_powrot)
                VALUES %s
                ON CONFLICT ON CONSTRAINT unique_kontuzja_zawodnik_data_opis
                DO UPDATE SET
                    status = EXCLUDED.status,
                    przewidywany_powrot = EXCLUDED.przewidywany_powrot;
            """
            
            try:
                execute_values(cursor, insert_query, kontuzje_data)
                print(f"dodano {len(kontuzje_data)} kontuzji")
            except Exception as e:
                print(f"\nblad przy zapisywaniu kontuzji {e}")
                return
    
    except requests.exceptions.RequestException as e:
        print(f"\n{e}")
    
    except Exception as e:
        print(f"\nbladd przy pobieraniu kontuzji{e}")
        import traceback
        traceback.print_exc()

def uzupelnij_brakujace_kontrakty(cursor):
    print("\nbrakujace kontrakty")
    
    cursor.execute("SELECT id_sezonu FROM sezony WHERE kod_sezonu = %s", (SEZON_AKTUALNY,))
    res = cursor.fetchone()
    if not res:
        return
    db_sezon_id = res[0]
    
    cursor.execute("""
        SELECT z.id_zawodnika, z.imie, z.nazwisko
        FROM zawodnicy z
        WHERE z.czy_aktywny = TRUE
          AND NOT EXISTS (
              SELECT 1 FROM kontrakty k 
              WHERE k.id_zawodnika = z.id_zawodnika 
                AND k.id_sezonu = %s
          )
        ORDER BY z.nazwisko
    """, (db_sezon_id,))
    
    zawodnicy_bez_kontraktu = cursor.fetchall()
    
    if not zawodnicy_bez_kontraktu:
        return
    
    
    cursor.execute("SELECT id_zespolu FROM zespoly")
    zespoly_ids = [row[0] for row in cursor.fetchall()]
    
    zawodnicy_mapa = {z[0]: (z[1], z[2]) for z in zawodnicy_bez_kontraktu}
    
    kontrakty_do_dodania = []
    znalezieni_gracze = set()
    
    for i, team_id in enumerate(zespoly_ids, 1):
        try:
            time.sleep(0.5)
            
            roster = commonteamroster.CommonTeamRoster(
                season=SEZON_AKTUALNY, 
                team_id=team_id
            )
            
            frames = roster.get_data_frames()
            if len(frames) < 1 or frames[0].empty:
                continue
            
            players_df = frames[0]
            
            for _, row in players_df.iterrows():
                player_id = row.get('PLAYER_ID')
                
                if player_id in zawodnicy_mapa:
                    imie, nazwisko = zawodnicy_mapa[player_id]
                    
                    kontrakty_do_dodania.append((
                        player_id,
                        team_id,
                        db_sezon_id,
                        1000000,
                        'Roster (z API)'
                    ))
                    
                    znalezieni_gracze.add(player_id)
            
        except Exception as e:
            continue
    
    if kontrakty_do_dodania:
        insert_query = """
            INSERT INTO kontrakty (id_zawodnika, id_zespolu, id_sezonu, kwota, typ_kontraktu)
            VALUES %s
            ON CONFLICT ON CONSTRAINT unique_kontrakt_zawodnik_sezon 
            DO UPDATE SET 
                id_zespolu = EXCLUDED.id_zespolu,
                kwota = EXCLUDED.kwota,
                typ_kontraktu = EXCLUDED.typ_kontraktu;
        """
        
        execute_values(cursor, insert_query, kontrakty_do_dodania)
        print(f"\nzaktualizowano {len(kontrakty_do_dodania)} kontraktow")
    
    nieznalezieni = len(zawodnicy_bez_kontraktu) - len(znalezieni_gracze)
    if nieznalezieni > 0:
        print(f"\n{nieznalezieni} zawodników nadal bez kontraktu")
