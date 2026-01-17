CREATE TABLE IF NOT EXISTS historia_kontraktow (
    id_logu SERIAL PRIMARY KEY,
    id_zawodnika BIGINT,
    stara_kwota NUMERIC(15,2),
    nowa_kwota NUMERIC(15,2),
    data_zmiany TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    uzytkownik_zmieniajacy VARCHAR(50) DEFAULT current_user
);

CREATE TABLE IF NOT EXISTS logi_bledow_mecze (
    id_logu SERIAL PRIMARY KEY,
    opis_bledu TEXT,
    data_zdarzenia TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);