--zmiany w kontraktach
CREATE OR REPLACE FUNCTION func_historia_kontraktow()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.kwota <> NEW.kwota THEN
        INSERT INTO historia_kontraktow (id_zawodnika, stara_kwota, nowa_kwota)
        VALUES (OLD.id_zawodnika, OLD.kwota, NEW.kwota);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_zapisz_zmiane_kontraktu
AFTER UPDATE ON kontrakty
FOR EACH ROW
EXECUTE FUNCTION func_historia_kontraktow();


--walidacja meczu
CREATE TABLE IF NOT EXISTS logi_bledow_mecze (
    id_logu SERIAL PRIMARY KEY,
    opis_bledu TEXT,
    data_logu TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE OR REPLACE FUNCTION func_walidacja_meczu()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.id_zespolu_gospodarz = NEW.id_zespolu_gosc THEN
        INSERT INTO logi_bledow_mecze (opis_bledu) VALUES ('Próba dodania meczu z tym samym zespołem ID: ' || NEW.id_zespolu_gospodarz);
        RAISE EXCEPTION 'Zespół nie może grać sam ze sobą';
    END IF;

    IF EXTRACT(YEAR FROM NEW.data_meczu) < 2020 THEN
        RAISE EXCEPTION 'Błędny rok meczu';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_walidacja_meczu_przed_insertem
BEFORE INSERT OR UPDATE ON mecze
FOR EACH ROW
EXECUTE FUNCTION func_walidacja_meczu();
