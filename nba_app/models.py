# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Sezony(models.Model):
    id_sezonu = models.AutoField(primary_key=True)
    
    kod_sezonu = models.CharField(max_length=20) 
    
    rok_poczatkowy = models.IntegerField(blank=True, null=True)
    opis = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sezony'
        verbose_name = "Sezon"
        verbose_name_plural = "Sezony"

    def __str__(self):
        return f"{self.kod_sezonu}"

class Zespoly(models.Model):
    id_zespolu = models.BigIntegerField(primary_key=True)
    nazwa = models.CharField(max_length=100)
    miasto = models.CharField(max_length=100)
    skrot = models.CharField(max_length=10)
    konferencja = models.CharField(max_length=20)
    
    class Meta:
        managed = False
        db_table = 'zespoly'
        verbose_name = "Zespół"
        verbose_name_plural = "Zespoły"

    def __str__(self):
        return self.nazwa


class Zawodnicy(models.Model):
    id_zawodnika = models.BigIntegerField(primary_key=True)
    imie = models.CharField(max_length=50)
    nazwisko = models.CharField(max_length=50)
    czy_aktywny = models.BooleanField(default=True, verbose_name="Aktywny")
    kraj_pochodzenia = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'zawodnicy'
        verbose_name = "Zawodnik"
        verbose_name_plural = "Zawodnicy"

    def __str__(self):
        return f"{self.imie} {self.nazwisko}"
    
    def pobierz_zespol(self):
        from .models import Kontrakty
        try:
            kontrakt = Kontrakty.objects.filter(id_zawodnika=self.id_zawodnika).first()
            if kontrakt and kontrakt.id_zespolu:
                return kontrakt.id_zespolu.nazwa
        except Exception:
            pass
        return "Brak kontraktu / Wolny Agent"


class Trenerzy(models.Model):
    id_trenera = models.AutoField(primary_key=True)
    imie = models.CharField(max_length=50)
    nazwisko = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'trenerzy'
        verbose_name = "Trener"
        verbose_name_plural = "Trenerzy"

    def __str__(self):
        return f"{self.imie} {self.nazwisko}"

class ZatrudnienieTrenerow(models.Model):
    id_zatrudnienia = models.AutoField(primary_key=True)
    id_trenera = models.ForeignKey(
        Trenerzy, 
        models.DO_NOTHING, 
        db_column='id_trenera',
        verbose_name="Trener",
        related_name='zatrudnienia'
    )
    id_zespolu = models.ForeignKey(
        Zespoly, 
        models.DO_NOTHING, 
        db_column='id_zespolu',
        verbose_name="Zespół",
        related_name='zatrudnienia_trenerow'
    )
    id_sezonu = models.ForeignKey(
        Sezony, 
        models.DO_NOTHING, 
        db_column='id_sezonu',
        verbose_name="Sezon",
        related_name='zatrudnienia_trenerow'
    )
    czy_glowny = models.BooleanField(default=True, verbose_name="Trener główny")

    class Meta:
        managed = False
        db_table = 'zatrudnienie_trenerow'
        verbose_name = "Zatrudnienie trenera"
        verbose_name_plural = "Zatrudnienia trenerów"
        unique_together = [['id_trenera', 'id_zespolu', 'id_sezonu']]

    def __str__(self):
        glowny = "Główny" if self.czy_glowny else "Asystent"
        return f"{self.id_trenera} - {self.id_zespolu} ({glowny})"

class Kontrakty(models.Model):
    id_kontraktu = models.AutoField(primary_key=True)
    id_zawodnika = models.ForeignKey(Zawodnicy, models.DO_NOTHING, db_column='id_zawodnika')
    id_zespolu = models.ForeignKey(Zespoly, models.DO_NOTHING, db_column='id_zespolu')
    id_sezonu = models.ForeignKey(Sezony, models.DO_NOTHING, db_column='id_sezonu')    
    kwota = models.DecimalField(max_digits=15, decimal_places=2)
    typ_kontraktu = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'kontrakty'
        verbose_name = "Kontrakt"
        verbose_name_plural = "Kontrakty"

    def __str__(self):
        return f"{self.id_zawodnika} - {self.kwota}$"


class Mecze(models.Model):
    id_meczu = models.AutoField(primary_key=True) 
    
    id_sezonu = models.ForeignKey(Sezony, models.DO_NOTHING, db_column='id_sezonu')
    id_zespolu_gospodarz = models.ForeignKey(Zespoly, models.DO_NOTHING, db_column='id_zespolu_gospodarz', related_name='mecze_domowe')
    id_zespolu_gosc = models.ForeignKey(Zespoly, models.DO_NOTHING, db_column='id_zespolu_gosc', related_name='mecze_wyjazdowe')
    data_meczu = models.DateField()
    wynik_gospodarz = models.IntegerField(blank=True, null=True)
    wynik_gosc = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'mecze'
        verbose_name = "Mecz"
        verbose_name_plural = "Mecze"

    def __str__(self):
        return f"{self.data_meczu}: {self.id_zespolu_gospodarz} vs {self.id_zespolu_gosc}"

class Kontuzje(models.Model):
    id_kontuzji = models.AutoField(primary_key=True)
    id_zawodnika = models.ForeignKey(Zawodnicy, models.DO_NOTHING, db_column='id_zawodnika')
    data_zgloszenia = models.DateField(blank=True, null=True)
    opis_kontuzji = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=50, blank=True, null=True)
    przewidywany_powrot = models.DateField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'kontuzje'
        verbose_name = "Kontuzja"
        verbose_name_plural = "Kontuzje"


class StatystykiZawodnikow(models.Model):
    id_statystyki = models.AutoField(primary_key=True)
    id_meczu = models.ForeignKey(Mecze, models.DO_NOTHING, db_column='id_meczu')
    id_zawodnika = models.ForeignKey(Zawodnicy, models.DO_NOTHING, db_column='id_zawodnika')
    id_zespolu = models.ForeignKey(Zespoly, models.DO_NOTHING, db_column='id_zespolu')
    
    punkty = models.IntegerField(default=0)
    asysty = models.IntegerField(default=0)
    zbiorki = models.IntegerField(default=0)
    przechwyty = models.IntegerField(default=0)
    bloki = models.IntegerField(default=0)
    straty = models.IntegerField(default=0)

    sekundy_na_parkiecie = models.IntegerField(default=0)

    plus_minus = models.IntegerField(blank=True, null=True)
    
    rzuty_celne = models.IntegerField(default=0)
    rzuty_oddane = models.IntegerField(default=0)
    rzuty_za_3_celne = models.IntegerField(default=0)
    rzuty_za_3_oddane = models.IntegerField(default=0)
    rzuty_wolne_celne = models.IntegerField(default=0)
    rzuty_wolne_oddane = models.IntegerField(default=0)

    class Meta:
        managed = False
        db_table = 'statystyki_zawodnikow'
        verbose_name = "Statystyka"
        verbose_name_plural = "Statystyki"

    @property
    def czas_gry(self):
        if not self.sekundy_na_parkiecie:
            return "0:00"
        m = self.sekundy_na_parkiecie // 60
        s = self.sekundy_na_parkiecie % 60
        return f"{m}:{s:02d}"

class RankingiZespolow(models.Model):
    kod_sezonu = models.CharField(max_length=20)
    zespol = models.CharField(max_length=100, primary_key=True, db_column='zespol')
    konferencja = models.CharField(max_length=20)
    wygrane = models.IntegerField()
    przegrane = models.IntegerField()
    procent_zwyciestw = models.FloatField() 

    class Meta:
        managed = False
        db_table = 'widok_tabela_ligowa'
        verbose_name = "Tabela Ligowa"
        ordering = ['-procent_zwyciestw', '-wygrane']

    @property
    def pct(self):
        if self.procent_zwyciestw is None:
            return ".000"
        
        s = f"{self.procent_zwyciestw:.3f}"
        
        if s.startswith("1"):
            return s
        
        return s.lstrip('0')
    
class HistoriaKontraktow(models.Model):
    id_logu = models.AutoField(primary_key=True)
    id_zawodnika = models.BigIntegerField(blank=True, null=True)
    stara_kwota = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    nowa_kwota = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    data_zmiany = models.DateTimeField(blank=True, null=True)
    uzytkownik_zmieniajacy = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'historia_kontraktow'
        verbose_name = "Log: Zmiana Kontraktu"
        verbose_name_plural = "Logi: Zmiany Kontraktów"


class LogiBledowMecze(models.Model):
    id_logu = models.AutoField(primary_key=True)
    opis_bledu = models.TextField(blank=True, null=True)
    data_zdarzenia = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'logi_bledow_mecze'
        verbose_name = "Log: Błąd Meczu"
        verbose_name_plural = "Logi: Błędy Meczów"


class RaportEfektywnoscFinansowa(models.Model):
    id_zawodnika = models.BigIntegerField(primary_key=True, db_column='id_zawodnika') 
    imie = models.CharField(max_length=50)
    nazwisko = models.CharField(max_length=50)
    zespol = models.CharField(max_length=100)
    kontrakt = models.DecimalField(max_digits=15, decimal_places=2)
    koszt_jednego_punktu = models.DecimalField(max_digits=15, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'raport_efektywnosc_finansowa'
        verbose_name = "Raport: Moneyball"
        verbose_name_plural = "Raporty: Moneyball"

class RaportDomWyjazd(models.Model):
    nazwa = models.CharField(max_length=100, primary_key=True)
    mecze_dom = models.IntegerField()
    wygrane_dom = models.IntegerField()
    mecze_wyjazd = models.IntegerField()
    wygrane_wyjazd = models.IntegerField()
    procent_wygranych_dom = models.DecimalField(max_digits=5, decimal_places=2) 

    class Meta:
        managed = False
        db_table = 'raport_dom_wyjazd'
        verbose_name = "Raport: Twierdza"
        verbose_name_plural = "Raporty: Twierdza"

class RaportKosztKontuzji(models.Model):
    nazwa = models.CharField(max_length=100, primary_key=True)
    liczba_kontuzjowanych = models.IntegerField()
    zamrozone_pieniadze = models.DecimalField(max_digits=20, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'raport_koszt_kontuzji'
        verbose_name = "Raport: Szpital"
        verbose_name_plural = "Raporty: Szpital"