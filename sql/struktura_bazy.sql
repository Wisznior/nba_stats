CREATE TABLE IF NOT EXISTS sezony (
    id_sezonu SERIAL PRIMARY KEY,
    kod_sezonu VARCHAR(20) NOT NULL UNIQUE,
    rok_poczatkowy INT,
    opis VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS zespoly (
    id_zespolu SERIAL PRIMARY KEY,
    nazwa VARCHAR(100) NOT NULL,
    miasto VARCHAR(100) NOT NULL,
    skrot VARCHAR(10) NOT NULL,
    konferencja VARCHAR(20) NOT NULL
);

CREATE TABLE IF NOT EXISTS zawodnicy (
    id_zawodnika SERIAL PRIMARY KEY,
    imie VARCHAR(50) NOT NULL,
    nazwisko VARCHAR(50) NOT NULL,
    czy_aktywny BOOLEAN DEFAULT TRUE,
    kraj_pochodzenia VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS trenerzy (
    id_trenera SERIAL PRIMARY KEY,
    imie VARCHAR(50) NOT NULL,
    nazwisko VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS zatrudnienie_trenerow (
    id_zatrudnienia SERIAL PRIMARY KEY,
    id_trenera INT REFERENCES trenerzy(id_trenera),
    id_zespolu INT REFERENCES zespoly(id_zespolu),
    id_sezonu INT REFERENCES sezony(id_sezonu),
    czy_glowny BOOLEAN DEFAULT TRUE,
    CONSTRAINT unikalny_trener_w_sezonie UNIQUE (id_trenera, id_zespolu, id_sezonu)
);

CREATE TABLE IF NOT EXISTS kontrakty (
    id_kontraktu SERIAL PRIMARY KEY,
    id_zawodnika INT REFERENCES zawodnicy(id_zawodnika),
    id_zespolu INT REFERENCES zespoly(id_zespolu),
    id_sezonu INT REFERENCES sezony(id_sezonu),
    kwota NUMERIC(15,2) NOT NULL,
    typ_kontraktu VARCHAR(50),
    data_podpisania DATE DEFAULT CURRENT_DATE,
    CONSTRAINT unique_kontrakt_zawodnik_sezon UNIQUE (id_zawodnika, id_sezonu)
);

CREATE TABLE IF NOT EXISTS mecze (
    id_meczu SERIAL PRIMARY KEY,
    id_sezonu INT REFERENCES sezony(id_sezonu),
    id_zespolu_gospodarz INT REFERENCES zespoly(id_zespolu),
    id_zespolu_gosc INT REFERENCES zespoly(id_zespolu),
    data_meczu DATE NOT NULL,
    wynik_gospodarz INT,
    wynik_gosc INT,
    CONSTRAINT rozne_zespoly CHECK (id_zespolu_gospodarz != id_zespolu_gosc)
);

CREATE TABLE IF NOT EXISTS kontuzje (
    id_kontuzji SERIAL PRIMARY KEY,
    id_zawodnika INT REFERENCES zawodnicy(id_zawodnika),
    data_zgloszenia DATE DEFAULT CURRENT_DATE,
    opis_kontuzji TEXT,
    status VARCHAR(50),
    przewidywany_powrot DATE,
    CONSTRAINT unique_kontuzja_zawodnik_data_opis UNIQUE (id_zawodnika, data_zgloszenia, opis_kontuzji)
);

CREATE TABLE IF NOT EXISTS statystyki_zawodnikow (
    id_statystyki SERIAL PRIMARY KEY,
    id_meczu INT REFERENCES mecze(id_meczu) ON DELETE CASCADE,
    id_zawodnika INT REFERENCES zawodnicy(id_zawodnika),
    id_zespolu INT REFERENCES zespoly(id_zespolu),
    
    punkty INT DEFAULT 0,
    asysty INT DEFAULT 0,
    zbiorki INT DEFAULT 0,
    przechwyty INT DEFAULT 0,
    bloki INT DEFAULT 0,
    straty INT DEFAULT 0,
    plus_minus INT DEFAULT 0,
    
    sekundy_na_parkiecie INT DEFAULT 0, 

    rzuty_celne INT DEFAULT 0,
    rzuty_oddane INT DEFAULT 0,
    rzuty_za_3_celne INT DEFAULT 0,
    rzuty_za_3_oddane INT DEFAULT 0,
    rzuty_wolne_celne INT DEFAULT 0,
    rzuty_wolne_oddane INT DEFAULT 0,

    CONSTRAINT unikalna_statystyka_w_meczu UNIQUE (id_meczu, id_zawodnika)
);

CREATE INDEX IF NOT EXISTS idx_kontrakty_zawodnik_sezon ON kontrakty(id_zawodnika, id_sezonu);
CREATE INDEX IF NOT EXISTS idx_kontrakty_zespol_sezon ON kontrakty(id_zespolu, id_sezonu);

CREATE INDEX IF NOT EXISTS idx_kontuzje_zawodnik ON kontuzje(id_zawodnika);
CREATE INDEX IF NOT EXISTS idx_kontuzje_status ON kontuzje(status);
CREATE INDEX IF NOT EXISTS idx_kontuzje_data ON kontuzje(data_zgloszenia DESC);

CREATE INDEX IF NOT EXISTS idx_statystyki_zawodnik ON statystyki_zawodnikow(id_zawodnika);
CREATE INDEX IF NOT EXISTS idx_statystyki_mecz ON statystyki_zawodnikow(id_meczu);

CREATE INDEX IF NOT EXISTS idx_mecze_sezon ON mecze(id_sezonu);
CREATE INDEX IF NOT EXISTS idx_mecze_data ON mecze(data_meczu DESC);