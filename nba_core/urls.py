"""
URL configuration for nba_core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from nba_app import views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('', views.index, name='index'),
    path('zespoly/', views.lista_zespolow, name='lista_zespolow'),
    path('zespoly/<int:id_zespolu>/', views.szczegoly_zespolu, name='szczegoly_zespolu'),
    path('zawodnicy/', views.lista_zawodnikow, name='lista_zawodnikow'),
    path('zawodnik/<int:id_zawodnika>/', views.szczegoly_zawodnika, name = 'szczegoly_zawodnika'),
    path('ranking/', views.tabela_ranking, name='tabela_ranking'),
    path('raporty/', views.raporty_view, name='raporty'),
    path('mecze/', views.lista_meczow, name='lista_meczow'),
    path('mecze/<int:id_meczu>', views.szczegoly_meczu, name = 'szczegoly_meczu'),
]