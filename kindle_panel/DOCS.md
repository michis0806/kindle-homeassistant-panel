# Kindle Panel einrichten

1. App starten und die Weboberfläche in Home Assistant öffnen.
2. Auf jedem Kindle `http://DEIN_HA_HOST:8098` aufrufen und dessen Code einzeln freigeben.
3. Unter **Kindles und Dashboards** Gerätename und Raum-Dashboard auswählen und speichern. Anschließend lässt sich eine Startansicht wählen.
4. Das Layout direkt im Home-Assistant-Dashboardeditor bearbeiten. Die App zeigt eine Vorschau für jeden Kindle.

Beim ersten Start wird das eigene Dashboard **Kindle** (`kindle-panel`) bei Bedarf aus der bisherigen Auswahl angelegt. Vorhandene Dashboards bleiben unverändert. Weitere Dashboards können in Home Assistant angelegt und getrennt zugeordnet werden. Mehrere Geräte dürfen dasselbe Dashboard verwenden.

Sensoren, binäre Zustände und Lichttasten sind standardmäßig ein Viertel breit, andere Bedienkacheln halb breit und Klimapanels ganz breit. Unterstützt werden einfache Core-Karten und Sections. Benutzerdefinierte Karten, bedingte Sichtbarkeit und spezielle Tipp-Aktionen werden nicht ausgeführt; Hinweise stehen in der App.

Entity-Badges (z. B. Temperatur, Luftfeuchtigkeit und Bewegung) erscheinen als schmale Badges mit Home-Assistant-Icon, Wert und Einheit oberhalb der Panels und werden live aktualisiert. Bedingte oder benutzerdefinierte Badges sowie Attributanzeigen werden mit Hinweis ausgelassen. Eine bereits als Karte vorhandene Entität wird nicht zusätzlich als Badge angezeigt.

Werte aktualisieren sich alle zwei Sekunden ohne Seitenreload. Layout- und Dashboardwechsel lösen einen Reload aus. Gerätefreigaben und Zuordnungen bleiben bei Updates erhalten. Ein Kindle kann nur Entitäten seines zugewiesenen Dashboards bedienen.

Für mehrere Geräte den neuen Kindle-Installer einzeln je Kindle verwenden: Er erzeugt eine eigene Kennung für das Beenden-Signal. Der bisherige Starter funktioniert weiterhin, besitzt aber noch keine unabhängige Gerätekennung. Der durchgestrichene Home-Assistant-Knopf führt mit passendem Starter zurück zur Kindle-Startseite. Die Rückkehr benötigt eine Netzwerkverbindung zur App.

Vollständige Installation und Einschränkungen: [GitHub](https://github.com/michis0806/kindle-homeassistant-panel).

Lichter sind einzelne kompakte Tasten mit Name und Glühbirne (An: ausgefüllt; Aus: durchgestrichen). Ein Tipp setzt den jeweils anderen Zustand. Die Anzeige wartet auf die Bestätigung durch Home Assistant. Sensorwerte übernehmen die in Home Assistant eingestellten Nachkommastellen, auch bei Live-Updates.
