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

    IF EXTRACT(YEAR FROM NEW.data_meczu) < 2025 THEN
        RAISE EXCEPTION 'Błędny rok meczu';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_walidacja_meczu_przed_insertem
BEFORE INSERT OR UPDATE ON mecze
FOR EACH ROW
EXECUTE FUNCTION func_walidacja_meczu();

--walidacja statystyk
CREATE OR REPLACE FUNCTION func_walidacja_statystyk()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.punkty < 0 OR NEW.asysty < 0 OR NEW.zbiorki < 0 
       OR NEW.przechwyty < 0 OR NEW.bloki < 0 OR NEW.straty < 0 THEN
        RAISE EXCEPTION 'Statystyki nie mogą być ujemne';
    END IF;
    IF NEW.rzuty_celne > NEW.rzuty_oddane THEN
        RAISE EXCEPTION 'Liczba celnych rzutów nie może być większa niż oddanych';
    END IF;
    IF NEW.rzuty_za_3_celne > NEW.rzuty_za_3_oddane THEN
        RAISE EXCEPTION 'Liczba celnych rzutów za 3 nie może być większa niż oddanych';
    END IF;
    IF NEW.rzuty_wolne_celne > NEW.rzuty_wolne_oddane THEN
        RAISE EXCEPTION 'Liczba celnych rzutów wolnych nie może być większa niż oddanych';
    END IF;
    IF NEW.punkty > (NEW.rzuty_celne * 3 + NEW.rzuty_wolne_celne) THEN
        RAISE NOTICE 'Punkty są większe względem rzutów oddanych';
    END IF;
    IF NEW.sekundy_na_parkiecie > 3600 THEN
        RAISE EXCEPTION 'Czas gry przekracza maksymalny możliwy';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_walidacja_statystyk
BEFORE INSERT OR UPDATE ON statystyki_zawodnikow
FOR EACH ROW
EXECUTE FUNCTION func_walidacja_statystyk();

--walidacja statusu kontuzji
CREATE OR REPLACE FUNCTION func_aktualizuj_status_kontuzji()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.przewidywany_powrot IS NOT NULL 
       AND NEW.przewidywany_powrot < CURRENT_DATE 
       AND NEW.status != 'Wyleczony' THEN
        NEW.status = 'Wyleczony';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_aktualizuj_status_kontuzji
BEFORE INSERT OR UPDATE ON kontuzje
FOR EACH ROW
EXECUTE FUNCTION func_aktualizuj_status_kontuzji();