# 0.9.1

Vier-Spalten-Grundraster mit Übernahme der Home-Assistant-Kartenbreiten, Zeilenbelegung, Reihenfolge und Abschnittsgrenzen. Große Klimakarte links, Jalousien rechts übereinander und weitere Karten wie im HA-Editor angeordnet; die aktuelle Raumkonfiguration passt auf eine Seite. JavaScript schreibt keine gemessenen Pixelbreiten mehr in die Seite; Kindle-Zoom wird über den Viewport festgesetzt.

# 0.8.0

Cover-Karten mit Auf-/Zu-Pfeilen, direkt auslösbare Skript-Tasten und einfache Lüfter-Ein-/Aus-Bedienung. Aktionen bleiben auf das zugewiesene Dashboard und unterstützte Gerätefunktionen begrenzt. Vollbreite Kindle-Seite ohne Desktop-Breitenlimit und erneute Größenanpassung nach Fensteränderungen ohne Seitenreload.

# 0.7.3

Überschriften und Platzhalter ohne Entität blockieren die Dashboard-Übersetzung nicht mehr.

# 0.7.2

Schmale Badges mit HA-Icon, Wert und Einheit; Anzeigepräzision aus der Home-Assistant-Entitätsregistrierung wird einschließlich nachgestellter Nullen übernommen. Vollständiger MDI-Iconsatz.

Lichter als kompakte einzelne Taste mit Name und Glühbirne: ausgefüllt bei An, durchgestrichen bei Aus. Symbol und nächste Schaltaktion folgen dem bestätigten Home-Assistant-Zustand. Nicht verfügbare Lichter bleiben gesperrt. Standardbreite ein Viertel; explizite Dashboardbreiten bleiben erhalten.

# 0.7.1

Entity-Badges einer Ansicht werden als kompakte Statuskacheln oberhalb der Panels übernommen und live aktualisiert. Unterstützt Temperatur, Luftfeuchtigkeit und binäre Zustände. Bedingte oder benutzerdefinierte Badges werden mit Hinweis ausgelassen. Bereits als Karte vorhandene Entitäten werden nicht doppelt angezeigt.

# 0.7.0

Mehrere Kindles mit eigenem Namen, Dashboard, Startansicht und Beenden-Signal. Home-Assistant-Dashboards als Layoutquelle, Kindle-Vorschau, kompakte Statuskacheln und unterstützte Core-Karten. Bestehende Freigaben bleiben erhalten; ein fehlendes Kindle-Dashboard wird einmalig aus der bisherigen Auswahl angelegt.

# 0.6.1

Unabhängige Zeilen für breite Klimapanels und normale Kacheln. Kompaktere Temperatur- und Modusbedienung; zwei Klimapanels passen auf eine Seite. Keine gemischten Tabellen mit colspan mehr; einzelne Kacheln nutzen die volle Breite statt einer leeren Nachbarzelle.

# 0.6.0

Gemeinsames Klimapanel in Übersicht und Detailseite: große Solltemperatur mit −/+, aktuelle Raumtemperatur und direkte Symboltasten für die unterstützten Betriebsarten. Bestätigter aktiver Modus wird schwarz markiert.

# 0.5.1

Durchgestrichenes Home-Assistant-Symbol als Beendenknopf in Übersicht und Klimaseite; zugänglicher Name und Tooltip bleiben vorhanden.

# 0.5.0

Sichtbarer „Kindle verlassen“-Knopf in Übersicht und Klimaseite. Gerätefreigabe und CSRF schützen die Beenden-Anfrage. Der Kindle beobachtet einen anonymen, rein lesbaren Zähler und beendet lokal den Kiosk mit Wiederherstellung von Licht und Energiesparen.

# 0.4.0

Live-Aktualisierung in Übersicht und Klimaseite ohne Seitenreload. Hintergrundaktionen mit Zustandsbestätigung, Schutz vor Doppeltipps und Erhalt noch nicht abgesendeter Dropdown-Auswahlen. Bestehende Freigaben und Auswahl bleiben erhalten.

# 0.3.0

Optionale Sensor-Live-Ansicht mit Hintergrundabfragen alle zwei Sekunden, Änderungen einzelner Texte und Wiederverbindung nach Fehlern. Bestehende Gerätefreigaben und Auswahl bleiben erhalten.

# 0.2.0

E-Ink-Layout mit sechs Kacheln pro Seite und kurzen Anzeigenamen. Eigene Klimaseite mit Solltemperatur, Betriebsart und Lüfter; alle Aktionen werden gegen die aktuellen Fähigkeiten des Geräts geprüft.

# 0.1.0

HTML-Bedienung, Gerätefreigabe und Entitätsauswahl.
