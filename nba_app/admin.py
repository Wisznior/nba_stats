from django.contrib import admin
from .models import (
    Sezony, Zespoly, Zawodnicy, Trenerzy, 
    Kontrakty, Mecze, Kontuzje, StatystykiZawodnikow, RankingiZespolow,
    HistoriaKontraktow, LogiBledowMecze,
    RaportEfektywnoscFinansowa, RaportDomWyjazd, RaportKosztKontuzji
)

@admin.register(Sezony)
class SezonyAdmin(admin.ModelAdmin):
    list_display = ('id_sezonu', 'opis', 'rok_poczatkowy')
    ordering = ('-rok_poczatkowy',)

@admin.register(Zespoly)
class ZespolyAdmin(admin.ModelAdmin):
    list_display = ('nazwa', 'miasto', 'skrot', 'konferencja')
    list_filter = ('konferencja',)
    search_fields = ('nazwa', 'miasto', 'skrot')

@admin.register(Zawodnicy)
class ZawodnicyAdmin(admin.ModelAdmin):
    list_display = ('nazwisko', 'imie', 'kraj_pochodzenia', 'czy_aktywny')
    list_filter = ('czy_aktywny', 'kraj_pochodzenia')
    search_fields = ('nazwisko', 'imie')
    list_per_page = 50

@admin.register(Trenerzy)
class TrenerzyAdmin(admin.ModelAdmin):
    list_display = ('id_trenera', 'nazwisko', 'imie')
    search_fields = ('nazwisko', 'imie')

@admin.register(Kontrakty)
class KontraktyAdmin(admin.ModelAdmin):
    list_display = ('id_zawodnika', 'id_zespolu', 'kwota', 'id_sezonu', 'typ_kontraktu')
    
    list_filter = ('id_sezonu', 'typ_kontraktu')
    
    search_fields = ('id_zawodnika__nazwisko', 'id_zespolu__nazwa')

@admin.register(Mecze)
class MeczeAdmin(admin.ModelAdmin):
    list_display = ('data_meczu', 'wyswietl_mecz', 'wynik_gospodarz', 'wynik_gosc')
    list_filter = ('data_meczu', 'id_sezonu')
    search_fields = ('id_zespolu_gospodarz__nazwa', 'id_zespolu_gosc__nazwa')
    date_hierarchy = 'data_meczu'
    
    def wyswietl_mecz(self, obj):
        return f"{obj.id_zespolu_gospodarz} vs {obj.id_zespolu_gosc}"
    wyswietl_mecz.short_description = "Spotkanie"

@admin.register(Kontuzje)
class KontuzjeAdmin(admin.ModelAdmin):
    list_display = ('id_zawodnika', 'status', 'data_zgloszenia', 'przewidywany_powrot')
    list_filter = ('status',)
    search_fields = ('id_zawodnika__nazwisko',)

@admin.register(StatystykiZawodnikow)
class StatystykiAdmin(admin.ModelAdmin):
    list_display = ('id_meczu', 'id_zawodnika', 'punkty', 'asysty', 'zbiorki', 'czas_gry')
    
    list_filter = ('id_zespolu',)
    
    search_fields = ('id_zawodnika__nazwisko', 'id_zawodnika__imie')

@admin.register(RankingiZespolow)
class RankingiAdmin(admin.ModelAdmin):
    list_display = ('zespol', 'konferencja', 'wygrane', 'przegrane', 'kod_sezonu')
    
    list_filter = ('kod_sezonu', 'konferencja')
    
    search_fields = ('zespol',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

class ReadOnlyAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(HistoriaKontraktow)
class HistoriaKontraktowAdmin(ReadOnlyAdmin):
    list_display = ('data_zmiany', 'id_zawodnika', 'stara_kwota', 'nowa_kwota', 'uzytkownik_zmieniajacy')
    ordering = ('-data_zmiany',)

@admin.register(LogiBledowMecze)
class LogiBledowAdmin(ReadOnlyAdmin):
    list_display = ('data_zdarzenia', 'opis_bledu')
    ordering = ('-data_zdarzenia',)

@admin.register(RaportEfektywnoscFinansowa)
class RaportMoneyballAdmin(ReadOnlyAdmin):
    list_display = ('nazwisko', 'imie', 'zespol', 'kontrakt', 'koszt_jednego_punktu')
    search_fields = ('nazwisko', 'zespol')
    ordering = ('koszt_jednego_punktu',)

@admin.register(RaportDomWyjazd)
class RaportTwierdzaAdmin(ReadOnlyAdmin):
    list_display = ('nazwa', 'mecze_dom', 'wygrane_dom', 'mecze_wyjazd', 'wygrane_wyjazd')
    search_fields = ('nazwa',)

@admin.register(RaportKosztKontuzji)
class RaportSzpitalAdmin(ReadOnlyAdmin):
    list_display = ('nazwa', 'liczba_kontuzjowanych', 'zamrozone_pieniadze')
    ordering = ('-zamrozone_pieniadze',)