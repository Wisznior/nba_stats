import psycopg2
from configparser import ConfigParser
import os

CONFIG_PATH = 'config/database.ini'

def load_config(filename: str = CONFIG_PATH, section: str ='postgresql') -> dict:
    if not os.path.exists(filename):
        raise Exception(f"{filename} nie znaleziony")
    parser = ConfigParser()
    parser.read(filename)

    db_config = {}
    if parser.has_section(section):
        params = parser.items(section)
        for p in params:
            db_config[p[0]] = p[1]
    else:
        raise Exception("nie znaleziono postgresql w pliku")
    
    return db_config

def get_connection():
    try:
        config = load_config()
        conn = psycopg2.connect(**config, options="-c client_encoding=UTF8")
        return conn
    except(Exception, psycopg2.DatabaseError) as error:
        print("błąd połączenia z bazą")
        raise error