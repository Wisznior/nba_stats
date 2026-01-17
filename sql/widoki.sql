--ranking 
CREATE OR REPLACE VIEW widok_tabela_ligowa AS
SELECT 
    s.kod_sezonu,
    z.nazwa AS zespol,
    z.konferencja,
    COUNT(CASE 
        WHEN (m.id_zespolu_gospodarz = z.id_zespolu AND m.wynik_gospodarz > m.wynik_gosc) OR 
             (m.id_zespolu_gosc = z.id_zespolu AND m.wynik_gosc > m.wynik_gospodarz) 
        THEN 1 END) AS wygrane,
    COUNT(CASE 
        WHEN (m.id_zespolu_gospodarz = z.id_zespolu AND m.wynik_gospodarz < m.wynik_gosc) OR 
             (m.id_zespolu_gosc = z.id_zespolu AND m.wynik_gosc < m.wynik_gospodarz) 
        THEN 1 END) AS przegrane,
    CASE 
        WHEN COUNT(m.id_meczu) > 0 THEN 
            CAST(COUNT(CASE 
                WHEN (m.id_zespolu_gospodarz = z.id_zespolu AND m.wynik_gospodarz > m.wynik_gosc) OR 
                     (m.id_zespolu_gosc = z.id_zespolu AND m.wynik_gosc > m.wynik_gospodarz) 
                THEN 1 END) AS FLOAT) / COUNT(m.id_meczu)
        ELSE 0 
    END AS procent_zwyciestw

FROM zespoly z
JOIN mecze m ON z.id_zespolu IN (m.id_zespolu_gospodarz, m.id_zespolu_gosc)
JOIN sezony s ON m.id_sezonu = s.id_sezonu
WHERE m.wynik_gospodarz IS NOT NULL 
GROUP BY s.kod_sezonu, z.id_zespolu, z.nazwa, z.konferencja
ORDER BY procent_zwyciestw DESC, wygrane DESC;

--efektywnosc finansowa
CREATE OR REPLACE VIEW raport_efektywnosc_finansowa AS
SELECT 
    z.id_zawodnika,
    z.imie,
    z.nazwisko,
    zes.nazwa AS zespol,
    k.kwota AS kontrakt,
    COALESCE(SUM(s.punkty), 0) AS suma_punktow,
    ROUND(k.kwota / SUM(s.punkty), 2) AS koszt_jednego_punktu
FROM zawodnicy z
JOIN kontrakty k ON z.id_zawodnika = k.id_zawodnika
JOIN sezony sez ON k.id_sezonu = sez.id_sezonu
JOIN zespoly zes ON k.id_zespolu = zes.id_zespolu
LEFT JOIN statystyki_zawodnikow s ON z.id_zawodnika = s.id_zawodnika
WHERE sez.kod_sezonu = '2025-26'
GROUP BY z.id_zawodnika, z.imie, z.nazwisko, zes.nazwa, k.kwota
HAVING SUM(s.punkty) > 0
ORDER BY koszt_jednego_punktu ASC;

--bilans gier domowych
CREATE OR REPLACE VIEW raport_dom_wyjazd AS
SELECT 
    zes.nazwa,
    COUNT(*) FILTER (WHERE m.id_zespolu_gospodarz = zes.id_zespolu) AS mecze_dom,
    COUNT(*) FILTER (WHERE m.id_zespolu_gospodarz = zes.id_zespolu AND m.wynik_gospodarz > m.wynik_gosc) AS wygrane_dom,
    
    COUNT(*) FILTER (WHERE m.id_zespolu_gosc = zes.id_zespolu) AS mecze_wyjazd,
    COUNT(*) FILTER (WHERE m.id_zespolu_gosc = zes.id_zespolu AND m.wynik_gosc > m.wynik_gospodarz) AS wygrane_wyjazd,

    CASE 
        WHEN COUNT(*) FILTER (WHERE m.id_zespolu_gospodarz = zes.id_zespolu) > 0 THEN 
            ROUND(
                (COUNT(*) FILTER (WHERE m.id_zespolu_gospodarz = zes.id_zespolu AND m.wynik_gospodarz > m.wynik_gosc)::numeric / 
                COUNT(*) FILTER (WHERE m.id_zespolu_gospodarz = zes.id_zespolu)::numeric) * 100, 
            2)
        ELSE 0.00 
    END AS procent_wygranych_dom

FROM zespoly zes
JOIN mecze m ON zes.id_zespolu = m.id_zespolu_gospodarz OR zes.id_zespolu = m.id_zespolu_gosc
GROUP BY zes.id_zespolu, zes.nazwa;

--koszty kontuzji
CREATE OR REPLACE VIEW raport_koszt_kontuzji AS
SELECT 
    zes.nazwa,
    COUNT(DISTINCT z.id_zawodnika) AS liczba_kontuzjowanych,
    COALESCE(SUM(DISTINCT k.kwota), 0) AS zamrozone_pieniadze
FROM zespoly zes
JOIN kontrakty k ON zes.id_zespolu = k.id_zespolu
JOIN sezony s ON k.id_sezonu = s.id_sezonu
JOIN zawodnicy z ON k.id_zawodnika = z.id_zawodnika
JOIN kontuzje kon ON z.id_zawodnika = kon.id_zawodnika 
    AND kon.status IN ('Aktywna', 'Out')
WHERE s.kod_sezonu = '2025-26'
GROUP BY zes.id_zespolu, zes.nazwa
ORDER BY zamrozone_pieniadze DESC;