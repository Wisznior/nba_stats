from django.shortcuts import render, get_object_or_404
from django.db.models import Avg, Sum, Q, Count, Max
from django.core.paginator import Paginator
from .models import Zespoly, Zawodnicy, RankingiZespolow, RaportEfektywnoscFinansowa, RaportDomWyjazd, RaportKosztKontuzji, StatystykiZawodnikow, Mecze, Sezony

def index(request):
    liczba_graczy = Zawodnicy.objects.filter(czy_aktywny=True).count()
    
    liczba_zespolow = Zespoly.objects.count()
    
    top_ranking = RankingiZespolow.objects.all().order_by('-wygrane')[:5]

    context = {
        'liczba_graczy': liczba_graczy,
        'liczba_zespolow': liczba_zespolow,
        'top_ranking': top_ranking
    }
    
    return render(request, 'nba_app/index.html', context)

def lista_zespolow(request):
    zespoly = Zespoly.objects.all().order_by('nazwa')
    konferencja = request.GET.get('konferencja')
    
    if konferencja:
        zespoly = zespoly.filter(konferencja=konferencja)

    return render(request, 'nba_app/zespoly.html', {'zespoly': zespoly, 'aktywna_konf': konferencja})

def lista_zawodnikow(request):
    query = request.GET.get('q', '')
    kraj = request.GET.get('kraj', '')
    klub = request.GET.get('klub', '')

    zawodnicy_list = Zawodnicy.objects.filter(czy_aktywny=True).order_by('nazwisko')

    if query:
        zawodnicy_list = zawodnicy_list.filter(
            Q(nazwisko__icontains=query) | Q(imie__icontains=query)
        )

    if kraj:
        zawodnicy_list = zawodnicy_list.filter(kraj_pochodzenia=kraj)

    if klub:
        zawodnicy_list = [z for z in zawodnicy_list if z.pobierz_zespol() == klub]

    paginator = Paginator(zawodnicy_list, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    kraje = Zawodnicy.objects.values_list('kraj_pochodzenia', flat=True).distinct()
    kluby_set = set(z.pobierz_zespol() for z in Zawodnicy.objects.filter(czy_aktywny=True))
    kluby = sorted(kluby_set)

    context = {
        'page_obj': page_obj,
        'query': query,
        'kraj': kraj,
        'klub': klub,
        'kraje': kraje,
        'kluby': kluby,
    }
    return render(request, 'nba_app/zawodnicy.html', context)


def szczegoly_zawodnika(request, id_zawodnika):
    zawodnik = get_object_or_404(Zawodnicy, id_zawodnika=id_zawodnika)
    
    SEZON_KOD = '2025-26'

    statystyki_qs = StatystykiZawodnikow.objects.filter(
        id_zawodnika=id_zawodnika
    )

    agregacja = statystyki_qs.aggregate(
        mecze_rozegrane=Count('id_statystyki'),
        srednia_pkt=Avg('punkty'),
        srednia_ast=Avg('asysty'),
        srednia_zb=Avg('zbiorki'),
        srednia_blk=Avg('bloki'),
        srednia_stl=Avg('przechwyty')
    )

    mecze_lista = statystyki_qs.select_related(
        'id_meczu', 
        'id_meczu__id_zespolu_gospodarz', 
        'id_meczu__id_zespolu_gosc'
    ).order_by('-id_meczu__data_meczu')

    zespol_info = "Wolny Agent"
    
    try:
        kontrakt = Kontrakty.objects.filter(id_zawodnika=id_zawodnika).order_by('-id_sezonu').first()
        
        if kontrakt:
            kwota_mln = kontrakt.kwota / 1000000
            zespol_info = f"{kontrakt.id_zespolu.nazwa}"
            
            detale = []
            if kontrakt.typ_kontraktu and kontrakt.typ_kontraktu != 'Gwarantowany':
                 detale.append(kontrakt.typ_kontraktu)
            if kontrakt.kwota > 0:
                 detale.append(f"${kwota_mln:.1f}M")
            
            if detale:
                zespol_info += f" ({', '.join(detale)})"
                
    except Exception as e:
        print(f"Błąd kontraktu: {e}")

    if "Wolny Agent" in zespol_info and agregacja['mecze_rozegrane'] > 0:
        ostatni_mecz = mecze_lista.first()
        if ostatni_mecz:
            zespol_info = ostatni_mecz.id_zespolu.nazwa 

    from .models import Kontuzje

    kontuzje_historia = Kontuzje.objects.filter(
        id_zawodnika=id_zawodnika
    ).order_by('-data_zgloszenia')[:10]

    kontuzja_aktualna = None
    if kontuzje_historia.exists():
        pierwsza = kontuzje_historia.first()
        if pierwsza.status and pierwsza.status != 'Wyleczony':
            kontuzja_aktualna = pierwsza

    context = {
        'zawodnik': zawodnik,
        'zespol': zespol_info,
        'statystyki': agregacja,
        'mecze': mecze_lista,
        'kontuzje': kontuzje_historia,
        'kontuzja_aktualna': kontuzja_aktualna,
    }

    return render(request, 'nba_app/zawodnik_szczegoly.html', context)

def tabela_ranking(request):
    ranking_east = RankingiZespolow.objects.filter(
        konferencja='Wschodnia'
    ).order_by('-procent_zwyciestw', '-wygrane')

    ranking_west = RankingiZespolow.objects.filter(
        konferencja='Zachodnia'
    ).order_by('-procent_zwyciestw', '-wygrane')
    
    context = {
        'ranking_east': ranking_east,
        'ranking_west': ranking_west
    }
    return render(request, 'nba_app/tabela_ranking.html', context)

def raporty_view(request):
    moneyball = RaportEfektywnoscFinansowa.objects.all()[:20] 
    
    twierdza = RaportDomWyjazd.objects.all().order_by('-procent_wygranych_dom')
    
    szpital = RaportKosztKontuzji.objects.all().order_by('-zamrozone_pieniadze')

    return render(request, 'nba_app/raporty.html', {
        'moneyball': moneyball,
        'twierdza': twierdza,
        'szpital': szpital
    })

def szczegoly_zespolu(request, id_zespolu):
    """Szczegółowa strona zespołu z zawodnikami, trenerami i statystykami"""
    from django.db.models import Avg, Sum, Count, F

    zespol = get_object_or_404(Zespoly, id_zespolu=id_zespolu)
    
    SEZON_KOD = '2025-26'
    
    try:
        from .models import Kontrakty, Sezony
        sezon_obj = Sezony.objects.filter(kod_sezonu=SEZON_KOD).first()
        
        if sezon_obj:
            kontrakty_zespolu = Kontrakty.objects.filter(
                id_zespolu=id_zespolu,
                id_sezonu=sezon_obj.id_sezonu
            ).select_related('id_zawodnika').order_by('-kwota')
            
            zawodnicy_zespolu = [k.id_zawodnika for k in kontrakty_zespolu]
        else:
            zawodnicy_zespolu = []
    except Exception as e:
        print(f"Błąd pobierania zawodników: {e}")
        zawodnicy_zespolu = []
    
    trenerzy_zespolu = []
    try:
        try:
            from .models import ZatrudnienieTrenerow, Sezony
            sezon_obj = Sezony.objects.filter(kod_sezonu=SEZON_KOD).first()
            
            if sezon_obj:
                zatrudnienia = ZatrudnienieTrenerow.objects.filter(
                    id_zespolu=id_zespolu,
                    id_sezonu=sezon_obj.id_sezonu
                ).select_related('id_trenera').order_by('-czy_glowny')
                
                trenerzy_zespolu = [(z.id_trenera, z.czy_glowny) for z in zatrudnienia]
        except (ImportError, AttributeError):
            from .models import Trenerzy
            trenerzy_z_fk = Trenerzy.objects.filter(
                id_zespolu=id_zespolu
            ).order_by('-czy_glowny')
            
            trenerzy_zespolu = [(t, t.czy_glowny) for t in trenerzy_z_fk]
    except Exception as e:
        print(f"Błąd pobierania trenerów: {e}")
        trenerzy_zespolu = []
    
    try:
        from .models import Mecze, Sezony
        sezon_obj = Sezony.objects.filter(kod_sezonu=SEZON_KOD).first()
        
        if sezon_obj:
            mecze_domowe = Mecze.objects.filter(
                id_zespolu_gospodarz=id_zespolu,
                id_sezonu=sezon_obj.id_sezonu,
                wynik_gospodarz__isnull=False
            )
            
            wygrane_dom = mecze_domowe.filter(
                wynik_gospodarz__gt=F('wynik_gosc')
            ).count()
            
            mecze_wyjazdowe = Mecze.objects.filter(
                id_zespolu_gosc=id_zespolu,
                id_sezonu=sezon_obj.id_sezonu,
                wynik_gosc__isnull=False
            )
            
            wygrane_wyjazd = mecze_wyjazdowe.filter(
                wynik_gosc__gt=F('wynik_gospodarz')
            ).count()
            
            total_mecze = mecze_domowe.count() + mecze_wyjazdowe.count()
            total_wygrane = wygrane_dom + wygrane_wyjazd
            total_przegrane = total_mecze - total_wygrane
            
            mecze_dom_count = mecze_domowe.count()
            mecze_wyjazd_count = mecze_wyjazdowe.count()
            przegrane_dom = mecze_dom_count - wygrane_dom
            przegrane_wyjazd = mecze_wyjazd_count - wygrane_wyjazd

            if total_mecze > 0:
                procent_wygranych = (total_wygrane / total_mecze) * 100
            else:
                procent_wygranych = 0
            
            statystyki_zespolu = {
                'wygrane': total_wygrane,
                'przegrane': total_przegrane,
                'mecze_rozegrane': total_mecze,
                'procent_wygranych': procent_wygranych,
                'wygrane_dom': wygrane_dom,
                'przegrane_dom': przegrane_dom,
                'mecze_dom': mecze_domowe.count(),
                'wygrane_wyjazd': wygrane_wyjazd,
                'przegrane_wyjazd': przegrane_wyjazd,
                'mecze_wyjazd': mecze_wyjazdowe.count()
            }
        else:
            statystyki_zespolu = None
    except Exception as e:
        print(f"Błąd statystyk zespołu: {e}")
        statystyki_zespolu = None
    
    try:
        ostatnie_mecze_gosp = Mecze.objects.filter(
            id_zespolu_gospodarz=id_zespolu,
            wynik_gospodarz__isnull=False
        ).select_related('id_zespolu_gosc').order_by('-data_meczu')[:5]
        
        ostatnie_mecze_gosc = Mecze.objects.filter(
            id_zespolu_gosc=id_zespolu,
            wynik_gosc__isnull=False
        ).select_related('id_zespolu_gospodarz').order_by('-data_meczu')[:5]
        
        ostatnie_mecze = sorted(
            list(ostatnie_mecze_gosp) + list(ostatnie_mecze_gosc),
            key=lambda m: m.data_meczu,
            reverse=True
        )[:5]
    except Exception as e:
        print(f"Błąd ostatnich meczów: {e}")
        ostatnie_mecze = []
    
    try:
        najlepsi_strzelcy = StatystykiZawodnikow.objects.filter(
            id_zespolu=id_zespolu
        ).values(
            'id_zawodnika__imie',
            'id_zawodnika__nazwisko',
            'id_zawodnika__id_zawodnika'
        ).annotate(
            suma_punktow=Sum('punkty'),
            mecze=Count('id_statystyki'),
            srednia=Avg('punkty')
        ).order_by('-suma_punktow')[:5]
    except Exception as e:
        print(f"Błąd strzelców: {e}")
        najlepsi_strzelcy = []
    
    pozycja_w_tabeli = None
    try:
        from .models import RankingiZespolow
        
        zespol_ranking = RankingiZespolow.objects.filter(
            zespol=zespol.nazwa
        ).first()
        
        if zespol_ranking:
            pozycja_konf = RankingiZespolow.objects.filter(
                konferencja=zespol_ranking.konferencja,
                procent_zwyciestw__gt=zespol_ranking.procent_zwyciestw
            ).count() + 1
            
            pozycja_ogolna = RankingiZespolow.objects.filter(
                procent_zwyciestw__gt=zespol_ranking.procent_zwyciestw
            ).count() + 1
            
            pozycja_w_tabeli = {
                'wygrane': zespol_ranking.wygrane,
                'przegrane': zespol_ranking.przegrane,
                'pct': zespol_ranking.pct,
                'konferencja': zespol_ranking.konferencja,
                'pozycja_konf': pozycja_konf,
                'pozycja_ogolna': pozycja_ogolna
            }
        else:
            print(f"Brak rankingu dla zespołu '{zespol.nazwa}' w tabeli RankingiZespolow")
    except Exception as e:
        print(f"Błąd pozycji w tabeli: {e}")
        pozycja_w_tabeli = None
    
    try:
        from .models import Kontuzje
        from datetime import date
        
        zawodnicy_ids = [z.id_zawodnika for z in zawodnicy_zespolu]
        
        kontuzje_aktywne = Kontuzje.objects.filter(
            id_zawodnika__id_zawodnika__in=zawodnicy_ids
        ).exclude(
            status__iexact='Wyleczony'
        ).select_related('id_zawodnika').order_by('-data_zgloszenia')[:10]
        
        print(f"DEBUG: Znaleziono {kontuzje_aktywne.count()} aktywnych kontuzji dla zespołu")
        
    except Exception as e:
        print(f"Błąd pobierania kontuzji: {e}")
        kontuzje_aktywne = []

    context = {
        'zespol': zespol,
        'zawodnicy': zawodnicy_zespolu,
        'trenerzy': trenerzy_zespolu,
        'statystyki': statystyki_zespolu,
        'ostatnie_mecze': ostatnie_mecze,
        'najlepsi_strzelcy': najlepsi_strzelcy,
        'pozycja_w_tabeli': pozycja_w_tabeli,
        'kontuzje': kontuzje_aktywne,
        'sezon': SEZON_KOD
    }
    
    return render(request, 'nba_app/zespol_szczegoly.html', context)

def lista_meczow(request):
    """
    Widok wyświetlający listę wszystkich meczów z możliwością filtrowania.
    
    Dostępne filtry:
    - sezon: filtrowanie po sezonie
    - zespol: filtrowanie po konkretnym zespole (jako gospodarz lub gość)
    - data_od: mecze od określonej daty
    - data_do: mecze do określonej daty
    """
    # Pobieramy wszystkie mecze z rozegranymi wynikami
    mecze_list = Mecze.objects.filter(
        wynik_gospodarz__isnull=False,
        wynik_gosc__isnull=False
    ).select_related(
        'id_sezonu',
        'id_zespolu_gospodarz', 
        'id_zespolu_gosc'
    ).order_by('-data_meczu')
    
    # Filtrowanie po sezonie
    sezon_filter = request.GET.get('sezon', '')
    if sezon_filter:
        mecze_list = mecze_list.filter(id_sezonu__kod_sezonu=sezon_filter)
    
    # Filtrowanie po zespole
    zespol_filter = request.GET.get('zespol', '')
    if zespol_filter:
        try:
            zespol_id = int(zespol_filter)
            # Mecze gdzie zespół był gospodarzem LUB gościem
            mecze_list = mecze_list.filter(
                Q(id_zespolu_gospodarz=zespol_id) | Q(id_zespolu_gosc=zespol_id)
            )
        except ValueError:
            pass
    
    # Filtrowanie po dacie OD
    data_od = request.GET.get('data_od', '')
    if data_od:
        mecze_list = mecze_list.filter(data_meczu__gte=data_od)
    
    # Filtrowanie po dacie DO
    data_do = request.GET.get('data_do', '')
    if data_do:
        mecze_list = mecze_list.filter(data_meczu__lte=data_do)
    
    # Paginacja - 25 meczów na stronę
    paginator = Paginator(mecze_list, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Przygotowanie danych do filtrów
    sezony_dostepne = Sezony.objects.all().order_by('-rok_poczatkowy')
    zespoly_dostepne = Zespoly.objects.all().order_by('nazwa')
    
    context = {
        'page_obj': page_obj,
        'sezony': sezony_dostepne,
        'zespoly': zespoly_dostepne,
        'sezon_filter': sezon_filter,
        'zespol_filter': zespol_filter,
        'data_od': data_od,
        'data_do': data_do,
    }
    
    return render(request, 'nba_app/lista_meczow.html', context)

def szczegoly_meczu(request, id_meczu):
    """
    Widok szczegółów pojedynczego meczu.
    Wyświetla wynik, statystyki wszystkich zawodników obu zespołów.
    """
    mecz = get_object_or_404(Mecze, id_meczu=id_meczu)
    
    # Pobieramy statystyki wszystkich zawodników z tego meczu
    statystyki_gospodarz = StatystykiZawodnikow.objects.filter(
        id_meczu=id_meczu,
        id_zespolu=mecz.id_zespolu_gospodarz
    ).select_related('id_zawodnika').order_by('-punkty')
    
    statystyki_gosc = StatystykiZawodnikow.objects.filter(
        id_meczu=id_meczu,
        id_zespolu=mecz.id_zespolu_gosc
    ).select_related('id_zawodnika').order_by('-punkty')
    
    # Sumujemy statystyki zespołowe
    from django.db.models import Sum
    
    suma_gosp = statystyki_gospodarz.aggregate(
        suma_pkt=Sum('punkty'),
        suma_ast=Sum('asysty'),
        suma_reb=Sum('zbiorki'),
        suma_stl=Sum('przechwyty'),
        suma_blk=Sum('bloki')
    )
    
    suma_gosc = statystyki_gosc.aggregate(
        suma_pkt=Sum('punkty'),
        suma_ast=Sum('asysty'),
        suma_reb=Sum('zbiorki'),
        suma_stl=Sum('przechwyty'),
        suma_blk=Sum('bloki')
    )
    
    context = {
        'mecz': mecz,
        'statystyki_gospodarz': statystyki_gospodarz,
        'statystyki_gosc': statystyki_gosc,
        'suma_gosp': suma_gosp,
        'suma_gosc': suma_gosc,
    }
    
    return render(request, 'nba_app/mecz_szczegoly.html', context)