# Kindle Panel einrichten

1. App starten und die Weboberfläche in Home Assistant öffnen.
2. Auf jedem Kindle `http://DEIN_HA_HOST:8098` aufrufen und dessen Code einzeln freigeben.
3. Unter **Kindles und Dashboards** Gerätename und Raum-Dashboard auswählen und speichern. Anschließend lässt sich eine Startansicht wählen.
4. Das Layout direkt im Home-Assistant-Dashboardeditor bearbeiten. Die App zeigt eine Vorschau für jeden Kindle.

Beim ersten Start wird das eigene Dashboard **Kindle** (`kindle-panel`) bei Bedarf aus der bisherigen Auswahl angelegt. Vorhandene Dashboards bleiben unverändert. Weitere Dashboards können in Home Assistant angelegt und getrennt zugeordnet werden. Mehrere Geräte dürfen dasselbe Dashboard verwenden.

Die Kindle-Ansicht nutzt ein Vier-Spalten-Grundraster und übernimmt die Kartenbreiten, Zeilenbelegung, Reihenfolge und Abschnittsgrenzen aus Home Assistant. Eine Klimakarte mit sechs HA-Spalten und vier Zeilen steht über die halbe Breite; zwei halbbreite Cover mit je zwei Zeilen können rechts daneben stehen. Weitere Karten folgen deiner Anordnung. Größere Abschnitte werden bei Bedarf an vollständigen Zeilengrenzen auf Seiten verteilt. Unterstützt werden einfache Core-Karten und Sections. Benutzerdefinierte Karten, bedingte Sichtbarkeit und spezielle Tipp-Aktionen werden nicht ausgeführt; Hinweise stehen in der App.

Entity-Badges (z. B. Temperatur, Luftfeuchtigkeit und Bewegung) erscheinen als schmale Badges mit Home-Assistant-Icon, Wert und Einheit oberhalb der Panels und werden live aktualisiert. Bedingte oder benutzerdefinierte Badges sowie Attributanzeigen werden mit Hinweis ausgelassen. Eine bereits als Karte vorhandene Entität wird nicht zusätzlich als Badge angezeigt.

Werte aktualisieren sich alle zwei Sekunden ohne Seitenreload. Layout- und Dashboardwechsel lösen einen Reload aus. Gerätefreigaben und Zuordnungen bleiben bei Updates erhalten. Ein Kindle kann nur Entitäten seines zugewiesenen Dashboards bedienen.

Für mehrere Geräte den neuen Kindle-Installer einzeln je Kindle verwenden: Er erzeugt eine eigene Kennung für das Beenden-Signal. Der bisherige Starter funktioniert weiterhin, besitzt aber noch keine unabhängige Gerätekennung. Der durchgestrichene Home-Assistant-Knopf führt mit passendem Starter zurück zur Kindle-Startseite. Die Rückkehr benötigt eine Netzwerkverbindung zur App.

Vollständige Installation und Einschränkungen: [GitHub](https://github.com/michis0806/kindle-homeassistant-panel).

Lichter sind einzelne kompakte Tasten mit Name und Glühbirne (An: ausgefüllt; Aus: durchgestrichen). Ein Tipp setzt den jeweils anderen Zustand. Die Anzeige wartet auf die Bestätigung durch Home Assistant. Sensorwerte übernehmen die in Home Assistant eingestellten Nachkommastellen, auch bei Live-Updates.

Cover-Karten bieten ↑ Öffnen und ↓ Schließen entsprechend den Gerätefähigkeiten. Skripte starten bei Berührung direkt ohne zusätzliche Parameter; bereits laufende Skripte sind gesperrt. Der Lüfter ist über eine Ein-/Aus-Taste bedienbar. Die Kindle-Seite nutzt die verfügbare Breite ohne fortlaufende JavaScript-Pixelbreitenkorrektur. Der Viewport bleibt für die Touchbedienung auf einer festen Skalierung.

Live-Ansicht und Vorschau bestimmen einmalig die verfügbare Fensterhöhe und wählen dazu passende Tastenhöhen. Karten werden mit berechneten Positionen angeordnet; die Breite bleibt unverändert. Die Vorschau verwendet nach Möglichkeit die gemeldete Fenstergröße des ausgewählten Kindle. Zur Layoutdiagnose erscheinen nur Zahlen zu Fenstermaßen und Tastenhöhen im lokalen App-Log, keine Entitätswerte oder Zugangsdaten.

Das HA-Dashboard bleibt die Quelle für Anordnung, Namen, Icons und Aktionen. Explizites „more-info“ öffnet lokale Details; „navigate“ kann Ansichten desselben Dashboards öffnen. Freie Service-/URL-Aktionen, Bestätigungen und abweichende Icon-Aktionen bleiben mit Hinweis gesperrt. Halten und Doppeltippen werden noch nicht übersetzt. Verschachtelte Stapel und Darstellungsoptionen werden teilweise angenähert.
