import datetime
import logging
import os
import json
import pandas as pd
from pathlib import Path
from garminconnect import Garmin

# Setup logging
logger = logging.getLogger("GarminConnector")

class GarminConnector:
    """
    Client für die Verbindung mit Garmin Connect API und das Abrufen von Fitnessdaten.
    
    Die Klasse nutzt die inoffizielle Garmin Connect API, um die folgenden Daten abzurufen:
    - Aktivitäten
    - Trainingshistorie
    - Rennprognosen
    - Hitze- und Höhenakklimatisierung
    """
    
    def __init__(self, username=None, password=None, cache_dir=None):
        """
        Initialisiert den GarminConnector.
        
        Args:
            username (str, optional): Garmin Connect Benutzername (E-Mail).
            password (str, optional): Garmin Connect Passwort.
            cache_dir (str, optional): Verzeichnis zum Cachen von API-Ergebnissen.
        """
        self.username = username
        self.password = password
        self.client = None
        self.connected = False
        
        # Cache-Einstellungen
        self.cache_dir = cache_dir
        if cache_dir:
            os.makedirs(cache_dir, exist_ok=True)
    
    def connect(self, username=None, password=None):
        """
        Stellt eine Verbindung zu Garmin Connect her.
        
        Args:
            username (str, optional): Garmin Connect Benutzername (E-Mail).
            password (str, optional): Garmin Connect Passwort.
            
        Returns:
            GarminConnector: Die Connector-Instanz für Method Chaining.
            
        Raises:
            ValueError: Wenn Benutzername oder Passwort fehlen.
            Exception: Bei Fehlern bei der Verbindung mit Garmin Connect.
        """
        if username:
            self.username = username
        if password:
            self.password = password
            
        if not self.username or not self.password:
            raise ValueError("Garmin Connect Benutzername und Passwort werden benötigt")
            
        try:
            logger.info(f"Verbinde mit Garmin Connect als {self.username}...")
            self.client = Garmin(self.username, self.password)
            self.client.login()
            self.connected = True
            logger.info("Verbindung zu Garmin Connect hergestellt!")
            return self
        except Exception as e:
            self.connected = False
            logger.error(f"Fehler bei der Verbindung zu Garmin Connect: {e}")
            raise
    
    def _check_connection(self):
        """Überprüft, ob eine Verbindung besteht, und wirft eine Exception, wenn nicht."""
        if not self.client or not self.connected:
            raise ValueError("Nicht mit Garmin Connect verbunden. Bitte zuerst connect() aufrufen.")
    
    def _cache_result(self, data, cache_file):
        """Speichert Ergebnisse im Cache-Verzeichnis, wenn aktiviert."""
        if self.cache_dir:
            cache_path = os.path.join(self.cache_dir, cache_file)
            
            # Klasse zum Serialisieren von Pandas-Timestamps
            class DateTimeEncoder(json.JSONEncoder):
                def default(self, obj):
                    if isinstance(obj, (pd.Timestamp, datetime.datetime, datetime.date)):
                        return obj.isoformat()
                    return super(DateTimeEncoder, self).default(obj)
            
            with open(cache_path, 'w') as f:
                json.dump(data, f, cls=DateTimeEncoder)
            logger.info(f"Daten im Cache gespeichert: {cache_path}")
    
    def _get_from_cache(self, cache_file):
        """Versucht, Daten aus dem Cache zu laden."""
        if self.cache_dir:
            cache_path = os.path.join(self.cache_dir, cache_file)
            if os.path.exists(cache_path):
                try:
                    with open(cache_path, 'r') as f:
                        data = json.load(f)
                    logger.info(f"Daten aus Cache geladen: {cache_path}")
                    return data
                except Exception as e:
                    logger.warning(f"Fehler beim Laden aus Cache: {e}")
        return None
    
    def get_activities(self, start_date=None, end_date=None, limit=None, use_cache=True):
        """
        Ruft Aktivitäten für einen bestimmten Zeitraum ab.
        
        Args:
            start_date (str, optional): Startdatum im Format 'YYYY-MM-DD'.
            end_date (str, optional): Enddatum im Format 'YYYY-MM-DD'.
            limit (int, optional): Maximale Anzahl von Aktivitäten.
            use_cache (bool, optional): Cache für Ergebnisse verwenden.
            
        Returns:
            pandas.DataFrame: DataFrame mit Aktivitätsdaten.
        """
        self._check_connection()
        
        # Standardwerte: Letzten 90 Tage
        if not end_date:
            end_date = datetime.datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.datetime.now() - datetime.timedelta(days=90)).strftime("%Y-%m-%d")
        
        cache_file = f"activities_{start_date}_{end_date}_{limit}.json"
        
        # Versuche aus Cache zu laden
        if use_cache:
            cached_data = self._get_from_cache(cache_file)
            if cached_data:
                return pd.DataFrame(cached_data)
        
        try:
            logger.info(f"Rufe Aktivitäten von {start_date} bis {end_date} ab...")
            activities = self.client.get_activities_by_date(start_date, end_date, limit)
            
            # Speichere im Cache
            self._cache_result(activities, cache_file)
            
            # Konvertiere zu DataFrame
            df = pd.DataFrame(activities)
            
            # Konvertiere Zeitstempel
            for col in df.columns:
                if 'Date' in col or 'date' in col or 'time' in col or 'Time' in col:
                    try:
                        df[col] = pd.to_datetime(df[col])
                    except:
                        pass
            
            logger.info(f"{len(df)} Aktivitäten abgerufen.")
            return df
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Aktivitäten: {e}")
            raise
    
    def get_activity_details(self, activity_id, use_cache=True):
        """
        Ruft Details zu einer bestimmten Aktivität ab.
        
        Args:
            activity_id (int): ID der Aktivität.
            use_cache (bool, optional): Cache für Ergebnisse verwenden.
            
        Returns:
            dict: Detaillierte Informationen zur Aktivität.
        """
        self._check_connection()
        
        cache_file = f"activity_details_{activity_id}.json"
        
        # Versuche aus Cache zu laden
        if use_cache:
            cached_data = self._get_from_cache(cache_file)
            if cached_data:
                return cached_data
        
        try:
            logger.info(f"Rufe Details für Aktivität {activity_id} ab...")
            activity_details = self.client.get_activity_details(activity_id)
            
            # Speichere im Cache
            self._cache_result(activity_details, cache_file)
            
            return activity_details
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Aktivitätsdetails: {e}")
            raise
    
    def get_weight_data(self, start_date=None, end_date=None, use_cache=True):
        """
        Ruft Gewichtsdaten für einen bestimmten Zeitraum ab.
        
        Args:
            start_date (str, optional): Startdatum im Format 'YYYY-MM-DD'.
            end_date (str, optional): Enddatum im Format 'YYYY-MM-DD'.
            use_cache (bool, optional): Cache für Ergebnisse verwenden.
            
        Returns:
            pandas.DataFrame: DataFrame mit Gewichtsdaten.
        """
        self._check_connection()
        
        # Standardwerte: Letzten 30 Tage
        if not end_date:
            end_date = datetime.datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime("%Y-%m-%d")
        
        cache_file = f"weight_data_{start_date}_{end_date}.json"
        
        # Versuche aus Cache zu laden
        if use_cache:
            cached_data = self._get_from_cache(cache_file)
            if cached_data:
                try:
                    if isinstance(cached_data, dict):
                        return pd.DataFrame([cached_data])
                    else:
                        return pd.DataFrame(cached_data)
                except Exception as e:
                    logger.warning(f"Fehler beim Konvertieren der Cache-Daten: {e}")
        
        try:
            logger.info(f"Rufe Gewichtsdaten von {start_date} bis {end_date} ab...")
            # Konvertiere Strings zu datetime.date für die API
            start = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
            
            weight_data = self.client.get_body_composition(start, end)
            
            # Debug-Ausgabe
            logger.info(f"Gewichtsdaten-Typ: {type(weight_data)}")
            if isinstance(weight_data, dict):
                logger.info(f"Gewichtsdaten-Schlüssel: {list(weight_data.keys())}")
            elif isinstance(weight_data, list):
                logger.info(f"Anzahl der Gewichtsdaten-Einträge: {len(weight_data)}")
                if weight_data:
                    if isinstance(weight_data[0], dict):
                        logger.info(f"Erster Eintrag Schlüssel: {list(weight_data[0].keys())}")
                    else:
                        logger.info(f"Erster Eintrag Typ: {type(weight_data[0])}")
            else:
                logger.info(f"Unerwarteter Gewichtsdaten-Typ: {type(weight_data)}")
            
            # Speichere im Cache
            self._cache_result(weight_data, cache_file)
            
            # Konvertiere zu DataFrame - robust gegen verschiedene Formate
            if isinstance(weight_data, dict):
                # Einzelnes Dictionary in ein DataFrame konvertieren
                df = pd.DataFrame([weight_data])
            elif isinstance(weight_data, list):
                if weight_data:
                    # Liste von Dictionaries
                    all_entries = []
                    for entry in weight_data:
                        if isinstance(entry, dict):
                            all_entries.append(entry)
                        else:
                            # Fallback für nicht-Dictionary-Elemente
                            all_entries.append({'raw_value': str(entry)})
                    df = pd.DataFrame(all_entries)
                else:
                    # Leere Liste
                    df = pd.DataFrame()
            else:
                # Unbekanntes Format
                logger.warning(f"Unbekanntes Format der Gewichtsdaten: {type(weight_data)}")
                df = pd.DataFrame([{'raw_data': str(weight_data)}])
            
            # Konvertiere Zeitstempel für nicht-verschachtelte Spalten
            for col in df.columns:
                if 'date' in col.lower() or 'time' in col.lower():
                    if col != 'dateWeightList' and not df[col].empty:  # Überspringe die Liste
                        try:
                            df[col] = pd.to_datetime(df[col])
                        except Exception as e:
                            logger.warning(f"Fehler beim Konvertieren der Spalte {col}: {e}")
            
            logger.info(f"{len(df)} Gewichtsdaten abgerufen.")
            return df
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Gewichtsdaten: {e}")
            # Leeren DataFrame zurückgeben
            return pd.DataFrame()
    
    def get_stats(self, start_date=None, end_date=None, use_cache=True):
        """
        Ruft Trainingsstatistiken für einen Zeitraum ab.
        
        Args:
            start_date (str, optional): Startdatum im Format 'YYYY-MM-DD'.
            end_date (str, optional): Enddatum im Format 'YYYY-MM-DD'.
            use_cache (bool, optional): Cache für Ergebnisse verwenden.
            
        Returns:
            dict: Trainingsstatistiken.
        """
        self._check_connection()
        
        # Standardwerte: Letzten 30 Tage
        if not end_date:
            end_date = datetime.datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime("%Y-%m-%d")
        
        cache_file = f"stats_{start_date}_{end_date}.json"
        
        # Versuche aus Cache zu laden
        if use_cache:
            cached_data = self._get_from_cache(cache_file)
            if cached_data:
                return cached_data
        
        try:
            logger.info(f"Rufe Statistiken von {start_date} bis {end_date} ab...")
            stats = self.client.get_stats(start_date, end_date)
            
            # Speichere im Cache
            self._cache_result(stats, cache_file)
            
            return stats
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Statistiken: {e}")
            raise
    
    def get_heart_rates(self, start_date=None, end_date=None, use_cache=True):
        """
        Ruft Herzfrequenzdaten für einen bestimmten Zeitraum ab.
        
        Args:
            start_date (str, optional): Startdatum im Format 'YYYY-MM-DD'.
            end_date (str, optional): Enddatum im Format 'YYYY-MM-DD'.
            use_cache (bool, optional): Cache für Ergebnisse verwenden.
            
        Returns:
            pandas.DataFrame: DataFrame mit Herzfrequenzdaten.
        """
        self._check_connection()
        
        # Standardwerte: Letzten 7 Tage
        if not end_date:
            end_date = datetime.datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
        
        cache_file = f"heart_rates_{start_date}_{end_date}.json"
        
        # Versuche aus Cache zu laden
        if use_cache:
            cached_data = self._get_from_cache(cache_file)
            if cached_data:
                logger.info(f"Herzfrequenzdaten aus Cache geladen: {len(cached_data)} Einträge")
                return pd.DataFrame(cached_data)
        
        try:
            logger.info(f"Rufe Herzfrequenzdaten von {start_date} bis {end_date} ab...")
            # Konvertiere String-Daten in datetime.date-Objekte für die API
            start = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
            
            # Sammle Daten für jeden Tag im Zeitraum
            all_data = []
            current = start
            day_count = 0
            
            while current <= end:
                day_count += 1
                try:
                    # Rufe Herzfrequenzdaten ab
                    logger.info(f"Rufe Herzfrequenzdaten für Tag {day_count}/{(end-start).days+1}: {current} ab...")
                    day_data = self.client.get_heart_rates(current)
                    
                    # Debug-Info für den zurückgegebenen Datentyp
                    logger.info(f"Herzfrequenzdaten für {current} sind vom Typ: {type(day_data)}")
                    
                    # Verarbeite basierend auf dem tatsächlichen Typ
                    if day_data is None:
                        logger.warning(f"Keine Herzfrequenzdaten für {current}")
                    elif isinstance(day_data, str):
                        # Wenn es ein String ist, versuche ihn als JSON zu parsen
                        logger.info(f"Herzfrequenzdaten als String (Anfang): {day_data[:100]}...")
                        try:
                            json_data = json.loads(day_data)
                            if isinstance(json_data, list):
                                logger.info(f"Geparste JSON-Liste mit {len(json_data)} Elementen")
                                for item in json_data:
                                    if isinstance(item, dict):
                                        item_with_date = item.copy()
                                        item_with_date['date'] = current.strftime("%Y-%m-%d")
                                        all_data.append(item_with_date)
                            elif isinstance(json_data, dict):
                                logger.info(f"Geparste JSON-Dict mit Schlüsseln: {list(json_data.keys())}")
                                json_data_with_date = json_data.copy()
                                json_data_with_date['date'] = current.strftime("%Y-%m-%d")
                                all_data.append(json_data_with_date)
                        except json.JSONDecodeError:
                            # Wenn es kein JSON ist, speichere als Rohtext
                            logger.warning(f"Herzfrequenzdaten für {current} ist kein gültiges JSON")
                            all_data.append({
                                'date': current.strftime("%Y-%m-%d"),
                                'raw_data': day_data[:100] + '...' if len(day_data) > 100 else day_data
                            })
                    elif isinstance(day_data, list):
                        # Liste von Objekten
                        logger.info(f"Herzfrequenzdaten als Liste mit {len(day_data)} Elementen")
                        if day_data and len(day_data) > 0:
                            logger.info(f"Beispiel für erstes Element: {type(day_data[0])}")
                            if isinstance(day_data[0], dict):
                                logger.info(f"Schlüssel des ersten Elements: {list(day_data[0].keys())}")
                        
                        for item in day_data:
                            if isinstance(item, dict):
                                item_with_date = item.copy()
                                item_with_date['date'] = current.strftime("%Y-%m-%d")
                                all_data.append(item_with_date)
                            else:
                                # Nicht-Dictionary-Element
                                all_data.append({
                                    'date': current.strftime("%Y-%m-%d"),
                                    'value': item if not isinstance(item, (str, bytes)) else str(item)
                                })
                    elif isinstance(day_data, dict):
                        # Ein einzelnes Dictionary
                        logger.info(f"Herzfrequenzdaten als Dictionary mit Schlüsseln: {list(day_data.keys())}")
                        
                        # Untersuche die Struktur des Dictionaries für häufige Garmin-Formate
                        if 'heartRateValues' in day_data:
                            hr_values = day_data['heartRateValues']
                            logger.info(f"heartRateValues gefunden: {type(hr_values)}, Länge: {len(hr_values) if isinstance(hr_values, list) else 'N/A'}")
                            if isinstance(hr_values, list) and hr_values:
                                logger.info(f"Beispiel für heartRateValues (erste 3): {hr_values[:3]}")
                                
                                # Extraktion einzelner Messwerte in separate Einträge
                                for hr_entry in hr_values:
                                    if isinstance(hr_entry, dict):
                                        entry_with_date = hr_entry.copy()
                                        entry_with_date['date'] = current.strftime("%Y-%m-%d")
                                        all_data.append(entry_with_date)
                                    elif isinstance(hr_entry, list) and len(hr_entry) >= 2:
                                        # Vermutlich [timestamp, wert] Format
                                        all_data.append({
                                            'date': current.strftime("%Y-%m-%d"),
                                            'timestamp': hr_entry[0],
                                            'value': hr_entry[1]
                                        })
                                    else:
                                        all_data.append({
                                            'date': current.strftime("%Y-%m-%d"),
                                            'value': hr_entry
                                        })
                            else:
                                # Wenn heartRateValues nicht als Liste vorliegt
                                day_data_with_date = day_data.copy()
                                day_data_with_date['date'] = current.strftime("%Y-%m-%d")
                                all_data.append(day_data_with_date)
                        elif 'values' in day_data:
                            # Alternative Struktur
                            values = day_data['values']
                            logger.info(f"values gefunden: {type(values)}, Länge: {len(values) if isinstance(values, list) else 'N/A'}")
                            if isinstance(values, list) and values:
                                logger.info(f"Beispiel für values (erste 3): {values[:3]}")
                                
                                for value_entry in values:
                                    if isinstance(value_entry, dict):
                                        entry_with_date = value_entry.copy()
                                        entry_with_date['date'] = current.strftime("%Y-%m-%d")
                                        all_data.append(entry_with_date)
                                    else:
                                        all_data.append({
                                            'date': current.strftime("%Y-%m-%d"),
                                            'value': value_entry
                                        })
                            else:
                                day_data_with_date = day_data.copy()
                                day_data_with_date['date'] = current.strftime("%Y-%m-%d")
                                all_data.append(day_data_with_date)
                        else:
                            # Standardverarbeitung für andere Dictionary-Strukturen
                            day_data_with_date = day_data.copy()
                            day_data_with_date['date'] = current.strftime("%Y-%m-%d")
                            all_data.append(day_data_with_date)
                    else:
                        # Unbekannter Typ
                        logger.warning(f"Unbekannter Typ für Herzfrequenzdaten: {type(day_data)}")
                        all_data.append({
                            'date': current.strftime("%Y-%m-%d"),
                            'unknown_type_data': str(type(day_data))
                        })
                except Exception as e:
                    logger.warning(f"Fehler beim Abrufen der Herzfrequenzdaten für {current}: {e}")
                    import traceback
                    logger.debug(traceback.format_exc())
                
                # Nächster Tag
                current += datetime.timedelta(days=1)
            
            # Log Zusammenfassung
            logger.info(f"Herzfrequenzdaten für {day_count} Tage abgefragt, {len(all_data)} Datenpunkte gefunden")
            
            # Speichere im Cache
            self._cache_result(all_data, cache_file)
            logger.info(f"Herzfrequenzdaten im Cache gespeichert: {cache_file}")
            
            # Konvertiere zu DataFrame
            df = pd.DataFrame(all_data)
            if df.empty:
                logger.warning("Keine Herzfrequenzdaten gefunden - leerer DataFrame")
            else:
                logger.info(f"Herzfrequenzdaten DataFrame erstellt mit {len(df)} Zeilen und Spalten: {list(df.columns)}")
                if 'date' in df.columns:
                    try:
                        df['date'] = pd.to_datetime(df['date'])
                        logger.info("Datum-Spalte erfolgreich in datetime konvertiert")
                    except Exception as e:
                        logger.warning(f"Fehler beim Konvertieren des Datums: {e}")
            
            logger.info(f"{len(df)} Herzfrequenzdaten abgerufen.")
            return df
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Herzfrequenzdaten: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # Leeren DataFrame zurückgeben
            return pd.DataFrame()
    
    def get_sleep_data(self, start_date=None, end_date=None, use_cache=True):
        """
        Ruft Schlafdaten für einen bestimmten Zeitraum ab.
        
        Args:
            start_date (str, optional): Startdatum im Format 'YYYY-MM-DD'.
            end_date (str, optional): Enddatum im Format 'YYYY-MM-DD'.
            use_cache (bool, optional): Cache für Ergebnisse verwenden.
            
        Returns:
            pandas.DataFrame: DataFrame mit Schlafdaten.
        """
        self._check_connection()
        
        # Standardwerte: Letzten 7 Tage
        if not end_date:
            end_date = datetime.datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
        
        cache_file = f"sleep_data_{start_date}_{end_date}.json"
        
        # Versuche aus Cache zu laden
        if use_cache:
            cached_data = self._get_from_cache(cache_file)
            if cached_data:
                logger.info(f"Schlafdaten aus Cache geladen: {len(cached_data)} Einträge")
                return pd.DataFrame(cached_data)
        
        try:
            logger.info(f"Rufe Schlafdaten von {start_date} bis {end_date} ab...")
            # Konvertiere String-Daten in datetime.date-Objekte für die API
            start = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
            
            # Sammle Daten für jeden Tag im Zeitraum
            all_data = []
            current = start
            day_count = 0
            
            while current <= end:
                day_count += 1
                try:
                    logger.info(f"Rufe Schlafdaten für Tag {day_count}/{(end-start).days+1}: {current} ab...")
                    # Rufe Schlafdaten ab
                    day_data = self.client.get_sleep_data(current)
                    
                    # Debug-Info
                    logger.info(f"Schlafdaten für {current} sind vom Typ: {type(day_data)}")
                    
                    # Verarbeite je nach Datentyp
                    if day_data is None:
                        logger.warning(f"Keine Schlafdaten für {current}")
                    elif isinstance(day_data, str):
                        logger.info(f"Schlafdaten als String (Anfang): {day_data[:100]}...")
                        try:
                            # Versuche, als JSON zu parsen
                            json_data = json.loads(day_data)
                            if isinstance(json_data, list):
                                for item in json_data:
                                    if isinstance(item, dict):
                                        entry_copy = item.copy()
                                        entry_copy['date'] = current.strftime("%Y-%m-%d")
                                        all_data.append(entry_copy)
                            elif isinstance(json_data, dict):
                                entry_copy = json_data.copy()
                                entry_copy['date'] = current.strftime("%Y-%m-%d")
                                all_data.append(entry_copy)
                        except json.JSONDecodeError:
                            all_data.append({
                                'date': current.strftime("%Y-%m-%d"),
                                'raw_data': day_data[:100] + '...' if len(day_data) > 100 else day_data
                            })
                    elif isinstance(day_data, list):
                        logger.info(f"Schlafdaten als Liste mit {len(day_data)} Elementen")
                        if day_data and len(day_data) > 0:
                            logger.info(f"Beispiel für erstes Element: {type(day_data[0])}")
                            if isinstance(day_data[0], dict):
                                logger.info(f"Schlüssel des ersten Elements: {list(day_data[0].keys())}")
                        
                        for item in day_data:
                            if isinstance(item, dict):
                                entry_copy = item.copy()
                                entry_copy['date'] = current.strftime("%Y-%m-%d")
                                all_data.append(entry_copy)
                            else:
                                all_data.append({
                                    'date': current.strftime("%Y-%m-%d"),
                                    'value': str(item)
                                })
                    elif isinstance(day_data, dict):
                        logger.info(f"Schlafdaten als Dictionary mit Schlüsseln: {list(day_data.keys())}")
                        
                        # Versuche spezifische Schlüssel zu finden und zu extrahieren
                        sleep_data_entry = day_data.copy()
                        sleep_data_entry['date'] = current.strftime("%Y-%m-%d")
                        all_data.append(sleep_data_entry)
                        
                        # Wenn es verschachtelte Schlafphasen gibt, extrahiere sie
                        if 'sleepLevels' in day_data:
                            logger.info(f"sleepLevels gefunden: {type(day_data['sleepLevels'])}")
                    else:
                        logger.warning(f"Unbekannter Typ für Schlafdaten: {type(day_data)}")
                        all_data.append({
                            'date': current.strftime("%Y-%m-%d"),
                            'unknown_type_data': str(type(day_data))
                        })
                except Exception as e:
                    logger.warning(f"Fehler beim Abrufen der Schlafdaten für {current}: {e}")
                    import traceback
                    logger.debug(traceback.format_exc())
                
                # Nächster Tag
                current += datetime.timedelta(days=1)
            
            # Log Zusammenfassung
            logger.info(f"Schlafdaten für {day_count} Tage abgefragt, {len(all_data)} Datenpunkte gefunden")
            
            # Speichere im Cache
            self._cache_result(all_data, cache_file)
            logger.info(f"Schlafdaten im Cache gespeichert: {cache_file}")
            
            # Konvertiere zu DataFrame
            df = pd.DataFrame(all_data)
            if df.empty:
                logger.warning("Keine Schlafdaten gefunden - leerer DataFrame")
            else:
                logger.info(f"Schlafdaten DataFrame erstellt mit {len(df)} Zeilen und Spalten: {list(df.columns)}")
                if 'date' in df.columns:
                    try:
                        df['date'] = pd.to_datetime(df['date'])
                        logger.info("Datum-Spalte erfolgreich in datetime konvertiert")
                    except Exception as e:
                        logger.warning(f"Fehler beim Konvertieren des Datums: {e}")
            
            logger.info(f"{len(df)} Schlafdaten abgerufen.")
            return df
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Schlafdaten: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # Leeren DataFrame zurückgeben
            return pd.DataFrame()
    
    def _process_sleep_data(self, df):
        """
        Verarbeitet ein DataFrame mit Schlafdaten, um verschachtelte Daten zu extrahieren.
        """
        if df.empty:
            return df
            
        # Konvertiere Zeitstempel
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            
        # Extrahiere Schlafphasen, falls vorhanden
        if 'sleepLevels' in df.columns:
            # Versuche, die verschachtelten Schlafphasen zu extrahieren
            try:
                for idx, row in df.iterrows():
                    if pd.isna(row['sleepLevels']):
                        continue
                        
                    sleep_levels = row['sleepLevels']
                    if isinstance(sleep_levels, list):
                        for level in sleep_levels:
                            level_name = level.get('nameType', 'unknown')
                            duration_seconds = level.get('seconds', 0)
                            df.at[idx, f'sleep_{level_name}_seconds'] = duration_seconds
            except Exception as e:
                logger.warning(f"Fehler beim Verarbeiten der Schlafphasen: {e}")
                
        return df
    
    def get_stress_data(self, start_date=None, end_date=None, use_cache=True):
        """
        Ruft Stressdaten für einen bestimmten Zeitraum ab.
        
        Args:
            start_date (str, optional): Startdatum im Format 'YYYY-MM-DD'.
            end_date (str, optional): Enddatum im Format 'YYYY-MM-DD'.
            use_cache (bool, optional): Cache für Ergebnisse verwenden.
            
        Returns:
            pandas.DataFrame: DataFrame mit Stressdaten.
        """
        self._check_connection()
        
        # Standardwerte: Letzten 7 Tage
        if not end_date:
            end_date = datetime.datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
        
        cache_file = f"stress_data_{start_date}_{end_date}.json"
        
        # Versuche aus Cache zu laden
        if use_cache:
            cached_data = self._get_from_cache(cache_file)
            if cached_data:
                logger.info(f"Stressdaten aus Cache geladen: {len(cached_data)} Einträge")
                return pd.DataFrame(cached_data)
        
        try:
            logger.info(f"Rufe Stressdaten von {start_date} bis {end_date} ab...")
            # Konvertiere String-Daten in datetime.date-Objekte für die API
            start = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
            
            # Sammle Daten für jeden Tag im Zeitraum
            all_data = []
            current = start
            day_count = 0
            
            while current <= end:
                day_count += 1
                try:
                    logger.info(f"Rufe Stressdaten für Tag {day_count}/{(end-start).days+1}: {current} ab...")
                    # Versuche den API-Aufruf für Stressdaten, falls verfügbar
                    if hasattr(self.client, 'get_stress_data'):
                        day_data = self.client.get_stress_data(current)
                    else:
                        # Alternative Methode, falls vorhanden
                        logger.warning("get_stress_data Methode nicht verfügbar in der API")
                        day_data = None
                    
                    # Debug-Info für den Datentyp
                    logger.info(f"Stressdaten für {current} sind vom Typ: {type(day_data)}")
                    
                    # Verarbeite je nach Datentyp
                    if day_data is None:
                        logger.warning(f"Keine Stressdaten für {current}")
                    elif isinstance(day_data, str):
                        logger.info(f"Stressdaten als String (Anfang): {day_data[:100]}...")
                        try:
                            # Versuche als JSON zu parsen
                            json_data = json.loads(day_data)
                            if isinstance(json_data, list):
                                logger.info(f"Geparste JSON-Liste mit {len(json_data)} Elementen")
                                for item in json_data:
                                    if isinstance(item, dict):
                                        entry_copy = item.copy()
                                        entry_copy['date'] = current.strftime("%Y-%m-%d")
                                        all_data.append(entry_copy)
                                    else:
                                        all_data.append({
                                            'date': current.strftime("%Y-%m-%d"),
                                            'value': str(item)
                                        })
                            elif isinstance(json_data, dict):
                                logger.info(f"Geparste JSON-Dict mit Schlüsseln: {list(json_data.keys())}")
                                entry_copy = json_data.copy()
                                entry_copy['date'] = current.strftime("%Y-%m-%d")
                                all_data.append(entry_copy)
                        except json.JSONDecodeError:
                            # Kein gültiges JSON
                            all_data.append({
                                'date': current.strftime("%Y-%m-%d"),
                                'raw_data': day_data[:100] + '...' if len(day_data) > 100 else day_data
                            })
                    elif isinstance(day_data, list):
                        logger.info(f"Stressdaten als Liste mit {len(day_data)} Elementen")
                        if day_data and len(day_data) > 0:
                            logger.info(f"Beispiel für erstes Element: {type(day_data[0])}")
                            if isinstance(day_data[0], dict):
                                logger.info(f"Schlüssel des ersten Elements: {list(day_data[0].keys())}")
                        
                        for item in day_data:
                            if isinstance(item, dict):
                                entry_copy = item.copy()
                                entry_copy['date'] = current.strftime("%Y-%m-%d")
                                all_data.append(entry_copy)
                            else:
                                all_data.append({
                                    'date': current.strftime("%Y-%m-%d"),
                                    'value': str(item)
                                })
                    elif isinstance(day_data, dict):
                        logger.info(f"Stressdaten als Dictionary mit Schlüsseln: {list(day_data.keys())}")
                        
                        # Typisches Format für Stressdaten untersuchen
                        if 'stressValues' in day_data:
                            stress_values = day_data['stressValues']
                            logger.info(f"stressValues gefunden: {type(stress_values)}, Länge: {len(stress_values) if isinstance(stress_values, list) else 'N/A'}")
                            if isinstance(stress_values, list) and stress_values:
                                logger.info(f"Beispiel für stressValues (erste 3): {stress_values[:3]}")
                                
                                # Extrahiere einzelne Stresswerte
                                for stress_entry in stress_values:
                                    if isinstance(stress_entry, dict):
                                        entry_copy = stress_entry.copy()
                                        entry_copy['date'] = current.strftime("%Y-%m-%d")
                                        all_data.append(entry_copy)
                                    elif isinstance(stress_entry, list) and len(stress_entry) >= 2:
                                        # Vermutlich [timestamp, wert] Format
                                        all_data.append({
                                            'date': current.strftime("%Y-%m-%d"),
                                            'timestamp': stress_entry[0],
                                            'value': stress_entry[1]
                                        })
                                    else:
                                        all_data.append({
                                            'date': current.strftime("%Y-%m-%d"),
                                            'value': stress_entry
                                        })
                            else:
                                # Wenn stressValues nicht als Liste vorliegt
                                entry_copy = day_data.copy()
                                entry_copy['date'] = current.strftime("%Y-%m-%d")
                                all_data.append(entry_copy)
                        else:
                            # Standard-Verarbeitung für andere Dictionary-Strukturen
                            entry_copy = day_data.copy()
                            entry_copy['date'] = current.strftime("%Y-%m-%d")
                            all_data.append(entry_copy)
                    else:
                        logger.warning(f"Unbekannter Typ für Stressdaten: {type(day_data)}")
                        all_data.append({
                            'date': current.strftime("%Y-%m-%d"),
                            'unknown_type_data': str(type(day_data))
                        })
                except Exception as e:
                    logger.warning(f"Fehler beim Abrufen der Stressdaten für {current}: {e}")
                    import traceback
                    logger.debug(traceback.format_exc())
                
                # Nächster Tag
                current += datetime.timedelta(days=1)
            
            # Log Zusammenfassung
            logger.info(f"Stressdaten für {day_count} Tage abgefragt, {len(all_data)} Datenpunkte gefunden")
            
            # Speichere im Cache
            self._cache_result(all_data, cache_file)
            logger.info(f"Stressdaten im Cache gespeichert: {cache_file}")
            
            # Konvertiere zu DataFrame
            df = pd.DataFrame(all_data)
            if df.empty:
                logger.warning("Keine Stressdaten gefunden - leerer DataFrame")
            else:
                logger.info(f"Stressdaten DataFrame erstellt mit {len(df)} Zeilen und Spalten: {list(df.columns)}")
                if 'date' in df.columns:
                    try:
                        df['date'] = pd.to_datetime(df['date'])
                        logger.info("Datum-Spalte erfolgreich in datetime konvertiert")
                    except Exception as e:
                        logger.warning(f"Fehler beim Konvertieren des Datums: {e}")
            
            logger.info(f"{len(df)} Stressdaten abgerufen.")
            return df
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Stressdaten: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # Leeren DataFrame zurückgeben
            return pd.DataFrame()
    
    def get_metrics_data(self, start_date=None, end_date=None, use_cache=True):
        """
        Ruft verschiedene Fitnessdaten (VO2Max, Training Status, etc.) für einen Zeitraum ab.
        
        Args:
            start_date (str, optional): Startdatum im Format 'YYYY-MM-DD'.
            end_date (str, optional): Enddatum im Format 'YYYY-MM-DD'.
            use_cache (bool, optional): Cache für Ergebnisse verwenden.
            
        Returns:
            dict: Dictionary mit verschiedenen Metrikdaten.
        """
        self._check_connection()
        
        # Standardwerte: Letzten 30 Tage
        if not end_date:
            end_date = datetime.datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime("%Y-%m-%d")
        
        cache_file = f"metrics_data_{start_date}_{end_date}.json"
        
        # Versuche aus Cache zu laden
        if use_cache:
            cached_data = self._get_from_cache(cache_file)
            if cached_data:
                return cached_data
        
        try:
            logger.info(f"Rufe Fitnessdaten von {start_date} bis {end_date} ab...")
            
            metrics = {}
            
            # VO2Max-Daten
            try:
                # Wenn cdate benötigt wird, verwende das aktuelle Datum
                today = datetime.datetime.now().date()
                vo2max_data = self.client.get_max_metrics(cdate=today)
                metrics['vo2max'] = vo2max_data
                logger.info("VO2Max-Daten abgerufen.")
            except Exception as e:
                logger.warning(f"Fehler beim Abrufen der VO2Max-Daten: {e}")

            # User Summary - mit cdate Parameter
            try:
                today = datetime.datetime.now().date()
                user_summary = self.client.get_user_summary(cdate=today)
                metrics['user_summary'] = user_summary
                logger.info("Benutzerzusammenfassung abgerufen.")
            except Exception as e:
                logger.warning(f"Fehler beim Abrufen der Benutzerzusammenfassung: {e}")
                        
            # GCM (Garmin Connect Metrics) - falls verfügbar
            try:
                if hasattr(self.client, 'get_metrics_data'):
                    gcm_data = self.client.get_metrics_data(start_date, end_date)
                    metrics['gcm_data'] = gcm_data
                    logger.info("GCM-Daten abgerufen.")
            except Exception as e:
                logger.warning(f"Fehler beim Abrufen der GCM-Daten: {e}")
            
            # Speichere im Cache
            self._cache_result(metrics, cache_file)
            
            return metrics
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Fitnessdaten: {e}")
            raise
    
    def _extract_metrics_to_dataframe(self, metrics_dict):
        """
        Extrahiert spezifische Trainingsdaten aus dem Metrics-Dictionary.
        
        Returns:
            pandas.DataFrame: DataFrame mit Trainingsdaten für das Backend-Format.
        """
        data = []
        
        # Versuche, VO2Max-Daten zu extrahieren
        if 'vo2max' in metrics_dict:
            vo2max = metrics_dict['vo2max']
            for entry in vo2max:
                if isinstance(entry, dict):
                    record = {
                        'timestamp': datetime.datetime.now().strftime("%Y-%m-%d"),
                        'calendarDate': datetime.datetime.now().strftime("%Y-%m-%d"),
                        'trainingStatus': 'unknown',  # Standard
                        'vo2max': entry.get('vo2maxValue', 0)
                    }
                    data.append(record)
        
        # Versuche, Zusammenfassungsdaten zu extrahieren
        if 'user_summary' in metrics_dict:
            user_summary = metrics_dict['user_summary']
            # Implementierung hängt von der tatsächlichen Struktur ab
            
        # GCM-Daten
        if 'gcm_data' in metrics_dict:
            gcm_data = metrics_dict['gcm_data']
            # Implementierung hängt von der tatsächlichen Struktur ab
            
        return pd.DataFrame(data)
    
    def get_training_history(self, use_cache=True):
        """
        Erstellt einen DataFrame mit Trainingshistorie im Format des Backends.
        
        Args:
            use_cache (bool, optional): Cache für Ergebnisse verwenden.
            
        Returns:
            pandas.DataFrame: DataFrame mit Trainingshistorie-Daten.
        """
        self._check_connection()
        
        cache_file = "training_history.json"
        
        # Versuche aus Cache zu laden
        if use_cache:
            cached_data = self._get_from_cache(cache_file)
            if cached_data:
                return pd.DataFrame(cached_data)
        
        try:
            logger.info("Erstelle Trainingshistorie aus verfügbaren Daten...")
            
            # Sammle Daten aus verschiedenen Quellen
            metrics_data = self.get_metrics_data(
                start_date=(datetime.datetime.now() - datetime.timedelta(days=90)).strftime("%Y-%m-%d"),
                end_date=datetime.datetime.now().strftime("%Y-%m-%d"),
                use_cache=use_cache
            )
            
            # Extrahiere Trainingsdaten in das richtige Format
            df = self._extract_metrics_to_dataframe(metrics_data)
            
            if df.empty:
                # Erstelle einen Datensatz mit Standarddaten
                today = datetime.datetime.now().strftime("%Y-%m-%d")
                df = pd.DataFrame([{
                    'timestamp': today,
                    'calendarDate': today,
                    'trainingStatus': 'unknown'
                }])
            
            # Konvertiere Zeitstempel-Spalten
            for col in ['timestamp', 'calendarDate']:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col])
            
            # Speichere im Cache
            self._cache_result(df.to_dict('records'), cache_file)
            
            logger.info(f"{len(df)} Trainingshistorie-Einträge erstellt.")
            return df
        except Exception as e:
            logger.error(f"Fehler beim Erstellen der Trainingshistorie: {e}")
            raise
    
    def get_race_predictions(self, use_cache=True):
        """
        Erstellt einen DataFrame mit Rennprognosen im Format des Backends.
        
        Args:
            use_cache (bool, optional): Cache für Ergebnisse verwenden.
            
        Returns:
            pandas.DataFrame: DataFrame mit Rennprognosen.
        """
        self._check_connection()
        
        cache_file = "race_predictions.json"
        
        # Versuche aus Cache zu laden
        if use_cache:
            cached_data = self._get_from_cache(cache_file)
            if cached_data:
                return pd.DataFrame(cached_data)
        
        try:
            logger.info("Erstelle Rennprognosen aus verfügbaren Daten...")
            
            # Sammle Aktivitätsdaten der letzten 90 Tage
            activities = self.get_activities(
                start_date=(datetime.datetime.now() - datetime.timedelta(days=90)).strftime("%Y-%m-%d"),
                end_date=datetime.datetime.now().strftime("%Y-%m-%d"),
                use_cache=use_cache
            )
            
            # Extrahiere Laufaktivitäten
            running_activities = activities[activities['activityType'].str.contains('running', case=False, na=False)]
            
            # Erstelle ein standardisiertes Format für Rennprognosen
            # Dies ist eine einfache Annäherung - tatsächliche Prognosen würden eine komplexere Analyse erfordern
            data = []
            
            if not running_activities.empty:
                # Gruppiere Aktivitäten nach Wochen
                running_activities['week'] = running_activities['startTimeLocal'].dt.isocalendar().week
                weekly_stats = running_activities.groupby('week').agg({
                    'startTimeLocal': 'last',  # Letztes Datum der Woche
                    'distance': 'sum',  # Gesamtdistanz
                    'duration': 'sum',  # Gesamtdauer
                    'avgSpeed': 'mean',  # Durchschnittsgeschwindigkeit
                })
                
                # Für jede Woche eine Prognose erstellen
                for idx, row in weekly_stats.iterrows():
                    # Einfache Annäherungen basierend auf Durchschnittsgeschwindigkeit
                    avg_pace = row['duration'] / row['distance'] if row['distance'] > 0 else 0  # Sekunden pro Meter
                    
                    # Umrechnen in Sekunden für verschiedene Distanzen (vereinfacht)
                    race_time_5k = int(5000 * avg_pace * 1.05)  # 5% langsamer für längere Distanz
                    race_time_10k = int(10000 * avg_pace * 1.08)  # 8% langsamer für längere Distanz
                    race_time_half = int(21097 * avg_pace * 1.1)  # 10% langsamer für längere Distanz
                    race_time_marathon = int(42195 * avg_pace * 1.15)  # 15% langsamer für längere Distanz
                    
                    # Datensatz für diese Woche
                    entry = {
                        'timestamp': row['startTimeLocal'].strftime("%Y-%m-%d"),
                        'raceTime5K': race_time_5k,
                        'raceTime10K': race_time_10k,
                        'raceTimeHalf': race_time_half,
                        'raceTimeMarathon': race_time_marathon
                    }
                    data.append(entry)
            
            # Wenn keine Laufdaten verfügbar sind, erstelle einen Dummy-Datensatz
            if not data:
                today = datetime.datetime.now().strftime("%Y-%m-%d")
                data = [{
                    'timestamp': today,
                    'raceTime5K': 1500,  # 25:00 für 5K
                    'raceTime10K': 3000,  # 50:00 für 10K
                    'raceTimeHalf': 6300,  # 1:45:00 für Halbmarathon
                    'raceTimeMarathon': 14400  # 4:00:00 für Marathon
                }]
            
            # Konvertiere zu DataFrame
            df = pd.DataFrame(data)
            
            # Konvertiere Zeitstempel
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Erstelle formatierte Zeitfelder
            for col in ['raceTime5K', 'raceTime10K', 'raceTimeHalf', 'raceTimeMarathon']:
                if col in df.columns:
                    df[f'{col}_formatted'] = df[col].apply(lambda x: f"{x // 60}:{x % 60:02d}")
            
            # Speichere im Cache
            self._cache_result(df.to_dict('records'), cache_file)
            
            logger.info(f"{len(df)} Rennprognosen erstellt.")
            return df
        except Exception as e:
            logger.error(f"Fehler beim Erstellen der Rennprognosen: {e}")
            raise

    # Folgende Methoden zur GarminConnector-Klasse hinzufügen

    def get_activity_details_for_all(self, activities_df=None, use_cache=True, limit=None):
        """
        Ruft detaillierte Daten für alle Aktivitäten ab.
        
        Args:
            activities_df (pandas.DataFrame, optional): DataFrame mit Aktivitäten (muss 'activityId' enthalten)
            use_cache (bool, optional): Cache für Ergebnisse verwenden
            limit (int, optional): Maximale Anzahl von Aktivitäten
            
        Returns:
            dict: Dictionary mit detaillierten Daten zu jeder Aktivität
        """
        self._check_connection()
        
        cache_file = "activity_details_all.json"
        
        # Versuche aus Cache zu laden
        if use_cache:
            cached_data = self._get_from_cache(cache_file)
            if cached_data:
                logger.info(f"Aktivitätsdetails aus Cache geladen: {len(cached_data)} Einträge")
                return cached_data
        
        # Wenn kein activities_df bereitgestellt wurde, lade es
        if activities_df is None:
            activities_df = self.get_activities(
                start_date=(datetime.datetime.now() - datetime.timedelta(days=365)).strftime("%Y-%m-%d"),
                end_date=datetime.datetime.now().strftime("%Y-%m-%d"),
                use_cache=use_cache
            )
        
        if activities_df.empty:
            logger.warning("Keine Aktivitäten gefunden")
            return {}
        
        # Limit die Anzahl der Aktivitäten, falls angegeben
        if limit and limit < len(activities_df):
            activities_df = activities_df.head(limit)
        
        # Sammle Daten für jede Aktivität
        all_details = {}
        total = len(activities_df)
        
        for idx, row in activities_df.iterrows():
            if 'activityId' not in row:
                logger.warning(f"Aktivität ohne ID gefunden: {row}")
                continue
                
            activity_id = row['activityId']
            try:
                logger.info(f"Rufe Details für Aktivität {idx+1}/{total}: ID {activity_id} ab...")
                
                # Prüfe auf Cache für diese spezifische Aktivität
                specific_cache = f"activity_detail_{activity_id}.json"
                cached_details = self._get_from_cache(specific_cache)
                
                if cached_details and use_cache:
                    details = cached_details
                    logger.info(f"Details für Aktivität {activity_id} aus Cache geladen")
                else:
                    details = self.client.get_activity_details(activity_id)
                    # Cache spezifische Aktivitätsdetails
                    self._cache_result(details, specific_cache)
                    logger.info(f"Details für Aktivität {activity_id} abgerufen und gecacht")
                
                # Füge zum Gesamtergebnis hinzu
                all_details[str(activity_id)] = details
                
            except Exception as e:
                logger.warning(f"Fehler beim Abrufen der Details für Aktivität {activity_id}: {e}")
        
        # Speichere alle Details im Cache
        self._cache_result(all_details, cache_file)
        logger.info(f"Alle Aktivitätsdetails im Cache gespeichert: {len(all_details)} Aktivitäten")
        
        return all_details

    def get_body_composition_detailed(self, start_date=None, end_date=None, use_cache=True):
        """
        Ruft detaillierte Körperkompositionsdaten für einen Zeitraum ab.
        
        Args:
            start_date (str, optional): Startdatum im Format 'YYYY-MM-DD'
            end_date (str, optional): Enddatum im Format 'YYYY-MM-DD'
            use_cache (bool, optional): Cache für Ergebnisse verwenden
            
        Returns:
            pandas.DataFrame: DataFrame mit Körperkompositionsdaten
        """
        self._check_connection()
        
        # Standardwerte
        if not end_date:
            end_date = datetime.datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.datetime.now() - datetime.timedelta(days=365)).strftime("%Y-%m-%d")
        
        cache_file = f"body_composition_{start_date}_{end_date}.json"
        
        # Versuche aus Cache zu laden
        if use_cache:
            cached_data = self._get_from_cache(cache_file)
            if cached_data:
                logger.info(f"Körperkompositionsdaten aus Cache geladen: {len(cached_data)} Einträge")
                return pd.DataFrame(cached_data)
        
        try:
            logger.info(f"Rufe Körperkompositionsdaten von {start_date} bis {end_date} ab...")
            
            # Konvertiere zu datetime.date für API
            start = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
            
            # Rufe Standard-Gewichtsdaten ab
            weight_data = self.client.get_body_composition(start, end)
            
            # Versuche, zusätzliche Körpermetriken abzurufen, falls verfügbar
            try:
                if hasattr(self.client, 'get_body_stats'):
                    body_stats = self.client.get_body_stats(start, end)
                    logger.info(f"Zusätzliche Körperstatistiken abgerufen")
                else:
                    body_stats = None
            except Exception as e:
                logger.warning(f"Fehler beim Abrufen erweiterter Körperstatistiken: {e}")
                body_stats = None
            
            # Kombiniere alle Daten
            combined_data = []
            
            # Verarbeite Gewichtsdaten
            if isinstance(weight_data, dict):
                # Einzelner Eintrag
                combined_data.append(weight_data)
            elif isinstance(weight_data, list):
                combined_data.extend(weight_data)
            
            # Füge body_stats hinzu, falls vorhanden
            if body_stats:
                # Die Struktur kann je nach API variieren, daher versuchen wir verschiedene Ansätze
                if isinstance(body_stats, dict):
                    if 'dateBodyStatsList' in body_stats:
                        stats_list = body_stats['dateBodyStatsList']
                        for stat in stats_list:
                            # Finde passenden Eintrag in combined_data
                            found = False
                            for entry in combined_data:
                                if entry.get('date') == stat.get('date'):
                                    # Ergänze bestehenden Eintrag
                                    entry.update(stat)
                                    found = True
                                    break
                            if not found:
                                combined_data.append(stat)
                    else:
                        # Füge als einzelnen Eintrag hinzu
                        combined_data.append(body_stats)
                elif isinstance(body_stats, list):
                    for stat in body_stats:
                        # Finde passenden Eintrag in combined_data
                        found = False
                        for entry in combined_data:
                            if entry.get('date') == stat.get('date'):
                                # Ergänze bestehenden Eintrag
                                entry.update(stat)
                                found = True
                                break
                        if not found:
                            combined_data.append(stat)
            
            # Speichere im Cache
            self._cache_result(combined_data, cache_file)
            
            # Konvertiere zu DataFrame
            df = pd.DataFrame(combined_data)
            logger.info(f"{len(df)} Körperkompositionsdaten abgerufen")
            return df
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Körperkompositionsdaten: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return pd.DataFrame()

    def get_user_stats_history(self, use_cache=True):
        """
        Ruft Langzeittrends und Statistiken des Benutzers ab.
        
        Args:
            use_cache (bool, optional): Cache für Ergebnisse verwenden
            
        Returns:
            dict: Dictionary mit verschiedenen langfristigen Statistiken
        """
        self._check_connection()
        
        cache_file = "user_stats_history.json"
        
        # Versuche aus Cache zu laden
        if use_cache:
            cached_data = self._get_from_cache(cache_file)
            if cached_data:
                logger.info(f"Langzeitstatistiken aus Cache geladen")
                return cached_data
        
        try:
            logger.info("Rufe Langzeitstatistiken ab...")
            
            stats = {}
            
            # Versuche verschiedene Statistiken abzurufen
            try:
                # Gesamtstatistiken (wenn verfügbar)
                if hasattr(self.client, 'get_user_summary'):
                    try:
                        # Versuche mit aktuellem Datum
                        today = datetime.datetime.now().date()
                        user_summary = self.client.get_user_summary(cdate=today)
                        stats['user_summary'] = user_summary
                        logger.info("Benutzerübersicht abgerufen")
                    except TypeError:
                        # Falls cdate nicht unterstützt wird
                        user_summary = self.client.get_user_summary()
                        stats['user_summary'] = user_summary
                        logger.info("Benutzerübersicht ohne Datum abgerufen")
            except Exception as e:
                logger.warning(f"Fehler beim Abrufen der Benutzerübersicht: {e}")
            
            try:
                # Persönliche Rekorde (wenn verfügbar)
                if hasattr(self.client, 'get_personal_records'):
                    personal_records = self.client.get_personal_records()
                    stats['personal_records'] = personal_records
                    logger.info("Persönliche Rekorde abgerufen")
            except Exception as e:
                logger.warning(f"Fehler beim Abrufen persönlicher Rekorde: {e}")
            
            try:
                # Jahresstatistiken (wenn verfügbar)
                if hasattr(self.client, 'get_stats'):
                    current_year = datetime.datetime.now().year
                    yearly_stats = {}
                    
                    # Versuche die letzten 5 Jahre abzurufen
                    for year in range(current_year - 4, current_year + 1):
                        try:
                            year_start = f"{year}-01-01"
                            year_end = f"{year}-12-31"
                            year_stats = self.client.get_stats(year_start, year_end)
                            yearly_stats[str(year)] = year_stats
                            logger.info(f"Statistiken für {year} abgerufen")
                        except Exception as e:
                            logger.warning(f"Fehler beim Abrufen der Statistiken für {year}: {e}")
                    
                    stats['yearly_stats'] = yearly_stats
            except Exception as e:
                logger.warning(f"Fehler beim Abrufen von Jahresstatistiken: {e}")
            
            # Speichere im Cache
            self._cache_result(stats, cache_file)
            logger.info(f"Langzeitstatistiken abgerufen und im Cache gespeichert")
            
            return stats
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Langzeitstatistiken: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {}
        
    def get_body_composition_detailed(self, start_date=None, end_date=None, use_cache=True):
        """
        Ruft detaillierte Körperkompositionsdaten für einen Zeitraum ab.
        
        Args:
            start_date (str, optional): Startdatum im Format 'YYYY-MM-DD'
            end_date (str, optional): Enddatum im Format 'YYYY-MM-DD'
            use_cache (bool, optional): Cache für Ergebnisse verwenden
            
        Returns:
            pandas.DataFrame: DataFrame mit Körperkompositionsdaten
        """
        self._check_connection()
        
        # Standardwerte
        if not end_date:
            end_date = datetime.datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.datetime.now() - datetime.timedelta(days=365)).strftime("%Y-%m-%d")
        
        cache_file = f"body_composition_{start_date}_{end_date}.json"
        
        # Versuche aus Cache zu laden
        if use_cache:
            cached_data = self._get_from_cache(cache_file)
            if cached_data:
                logger.info(f"Körperkompositionsdaten aus Cache geladen: {len(cached_data)} Einträge")
                return pd.DataFrame(cached_data)
        
        try:
            logger.info(f"Rufe Körperkompositionsdaten von {start_date} bis {end_date} ab...")
            
            # Konvertiere zu datetime.date für API
            start = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
            
            # Rufe Standard-Gewichtsdaten ab
            weight_data = self.client.get_body_composition(start, end)
            
            # Versuche, zusätzliche Körpermetriken abzurufen, falls verfügbar
            try:
                if hasattr(self.client, 'get_body_stats'):
                    body_stats = self.client.get_body_stats(start, end)
                    logger.info(f"Zusätzliche Körperstatistiken abgerufen")
                else:
                    body_stats = None
            except Exception as e:
                logger.warning(f"Fehler beim Abrufen erweiterter Körperstatistiken: {e}")
                body_stats = None
            
            # Kombiniere alle Daten
            combined_data = []
            
            # Verarbeite Gewichtsdaten
            if isinstance(weight_data, dict):
                # Einzelner Eintrag
                combined_data.append(weight_data)
            elif isinstance(weight_data, list):
                combined_data.extend(weight_data)
            
            # Füge body_stats hinzu, falls vorhanden
            if body_stats:
                # Die Struktur kann je nach API variieren, daher versuchen wir verschiedene Ansätze
                if isinstance(body_stats, dict):
                    if 'dateBodyStatsList' in body_stats:
                        stats_list = body_stats['dateBodyStatsList']
                        for stat in stats_list:
                            # Finde passenden Eintrag in combined_data
                            found = False
                            for entry in combined_data:
                                if entry.get('date') == stat.get('date'):
                                    # Ergänze bestehenden Eintrag
                                    entry.update(stat)
                                    found = True
                                    break
                            if not found:
                                combined_data.append(stat)
                    else:
                        # Füge als einzelnen Eintrag hinzu
                        combined_data.append(body_stats)
                elif isinstance(body_stats, list):
                    for stat in body_stats:
                        # Finde passenden Eintrag in combined_data
                        found = False
                        for entry in combined_data:
                            if entry.get('date') == stat.get('date'):
                                # Ergänze bestehenden Eintrag
                                entry.update(stat)
                                found = True
                                break
                        if not found:
                            combined_data.append(stat)
            
            # Speichere im Cache
            self._cache_result(combined_data, cache_file)
            
            # Konvertiere zu DataFrame
            df = pd.DataFrame(combined_data)
            logger.info(f"{len(df)} Körperkompositionsdaten abgerufen")
            return df
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Körperkompositionsdaten: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return pd.DataFrame()
    def get_user_stats_history(self, use_cache=True):
        """
        Ruft Langzeittrends und Statistiken des Benutzers ab.
        
        Args:
            use_cache (bool, optional): Cache für Ergebnisse verwenden
            
        Returns:
            dict: Dictionary mit verschiedenen langfristigen Statistiken
        """
        self._check_connection()
        
        cache_file = "user_stats_history.json"
        
        # Versuche aus Cache zu laden
        if use_cache:
            cached_data = self._get_from_cache(cache_file)
            if cached_data:
                logger.info(f"Langzeitstatistiken aus Cache geladen")
                return cached_data
        
        try:
            logger.info("Rufe Langzeitstatistiken ab...")
            
            stats = {}
            
            # Versuche verschiedene Statistiken abzurufen
            try:
                # Gesamtstatistiken (wenn verfügbar)
                if hasattr(self.client, 'get_user_summary'):
                    user_summary = self.client.get_user_summary()
                    stats['user_summary'] = user_summary
                    logger.info("Benutzerübersicht abgerufen")
            except Exception as e:
                logger.warning(f"Fehler beim Abrufen der Benutzerübersicht: {e}")
            
            try:
                # Persönliche Rekorde (wenn verfügbar)
                if hasattr(self.client, 'get_personal_records'):
                    personal_records = self.client.get_personal_records()
                    stats['personal_records'] = personal_records
                    logger.info("Persönliche Rekorde abgerufen")
            except Exception as e:
                logger.warning(f"Fehler beim Abrufen persönlicher Rekorde: {e}")
            
            try:
                # Jahresstatistiken (wenn verfügbar)
                if hasattr(self.client, 'get_yearly_stats'):
                    current_year = datetime.datetime.now().year
                    yearly_stats = {}
                    
                    # Versuche die letzten 5 Jahre abzurufen
                    for year in range(current_year - 4, current_year + 1):
                        try:
                            year_stats = self.client.get_yearly_stats(year)
                            yearly_stats[str(year)] = year_stats
                            logger.info(f"Statistiken für {year} abgerufen")
                        except Exception as e:
                            logger.warning(f"Fehler beim Abrufen der Statistiken für {year}: {e}")
                    
                    stats['yearly_stats'] = yearly_stats
            except Exception as e:
                logger.warning(f"Fehler beim Abrufen von Jahresstatistiken: {e}")
            
            # Speichere im Cache
            self._cache_result(stats, cache_file)
            logger.info(f"Langzeitstatistiken abgerufen und im Cache gespeichert")
            
            return stats
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Langzeitstatistiken: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {}
        
    def get_heat_altitude_metrics(self, use_cache=True):
        """
        Erstellt einen DataFrame mit Hitze- und Höhenakklimatisierungsdaten im Format des Backends.
        
        Args:
            use_cache (bool, optional): Cache für Ergebnisse verwenden.
            
        Returns:
            pandas.DataFrame: DataFrame mit Hitze- und Höhenakklimatisierungsdaten.
        """
        self._check_connection()
        
        cache_file = "heat_altitude_metrics.json"
        
        # Versuche aus Cache zu laden
        if use_cache:
            cached_data = self._get_from_cache(cache_file)
            if cached_data:
                return pd.DataFrame(cached_data)
        
        try:
            logger.info("Erstelle Hitze- und Höhenakklimatisierungsdaten aus verfügbaren Daten...")
            
            # Für diesen Datentyp gibt es keine direkte Quelle in der aktuellen API
            # Stattdessen erstellen wir einen Datensatz basierend auf Aktivitäten
            activities = self.get_activities(
                start_date=(datetime.datetime.now() - datetime.timedelta(days=90)).strftime("%Y-%m-%d"),
                end_date=datetime.datetime.now().strftime("%Y-%m-%d"),
                use_cache=use_cache
            )
            
            data = []
            
            # Wenn Aktivitäten verfügbar sind, verwende diese für Approximationen
            if not activities.empty:
                # Prüfe, welche Spalten tatsächlich vorhanden sind
                available_columns = set(activities.columns)
                logger.info(f"Verfügbare Spalten in Aktivitätsdaten: {', '.join(sorted(available_columns))}")
                
                # Identifiziere Spalten für Datum/Zeit
                date_columns = [col for col in available_columns 
                            if any(term in col.lower() for term in ['date', 'time', 'timestamp'])]
                logger.info(f"Gefundene Datumsspalten: {date_columns}")
                
                # Wähle die erste verfügbare Datumsspalte
                date_column = None
                for col in ['startTimeLocal', 'beginTimestamp', 'startTimeGmt', 'startTimeLocal', 'calendarDate']:
                    if col in available_columns:
                        date_column = col
                        break
                
                if date_column:
                    logger.info(f"Verwende {date_column} als Datumsspalte")
                    
                    # Sicherstellen, dass die Spalte als datetime vorliegt
                    try:
                        activities[date_column] = pd.to_datetime(activities[date_column])
                        activities['day'] = activities[date_column].dt.date
                        
                        # Dynamisch aggregieren basierend auf verfügbaren Spalten
                        agg_dict = {date_column: 'first'}  # Immer das Datum aggregieren
                        
                        # Füge verfügbare numerische Spalten hinzu
                        numeric_columns = {
                            'distance': 'sum',
                            'duration': 'sum',
                            'avgHr': 'mean',
                            'heartRate': 'mean',
                            'maxHr': 'max',
                            'calories': 'sum',
                            'minTemperature': 'min',
                            'maxTemperature': 'max',
                            'elevationGain': 'sum',
                            'avgTemperature': 'mean'
                        }
                        
                        for col, agg_func in numeric_columns.items():
                            if col in available_columns:
                                agg_dict[col] = agg_func
                        
                        # Gruppiere nach Tag und aggregiere
                        daily_stats = activities.groupby('day').agg(agg_dict)
                        
                        # Für jeden Tag einen Datensatz erstellen
                        for idx, row in daily_stats.iterrows():
                            # Dummy-Werte für Hitze- und Höhenakklimatisierung
                            heat_acclimatization = 0
                            altitude_acclimatization = 0
                            
                            # Wenn Temperaturwerte vorhanden sind, berücksichtige sie für Hitzeakklimatisierung
                            temp_value = None
                            for temp_col in ['maxTemperature', 'avgTemperature']:
                                if temp_col in row and not pd.isna(row[temp_col]):
                                    temp_value = row[temp_col]
                                    break
                            
                            if temp_value is not None:
                                # Beispiel: Über 25°C trägt zur Hitzeakklimatisierung bei
                                if temp_value > 25:
                                    heat_acclimatization = min(100, (temp_value - 25) * 10)  # 10 Punkte pro Grad über 25
                            
                            # Wenn Höhendaten vorhanden sind, berücksichtige sie für Höhenakklimatisierung
                            if 'elevationGain' in row and not pd.isna(row['elevationGain']):
                                # Beispiel: Über 500m Höhengewinn trägt zur Höhenakklimatisierung bei
                                elev_gain = row['elevationGain']
                                if elev_gain > 500:
                                    altitude_acclimatization = min(100, elev_gain / 50)  # 2 Punkte pro 100m über 500
                            
                            # Datensatz für diesen Tag
                            entry = {
                                'timestamp': str(idx),  # Datum als String
                                'calendarDate': str(idx),
                                'heatAcclimatization': heat_acclimatization,
                                'altitudeAcclimatization': altitude_acclimatization
                            }
                            data.append(entry)
                    except Exception as e:
                        logger.error(f"Fehler bei der Datumsverarbeitung: {e}")
                        import traceback
                        logger.error(traceback.format_exc())
            
            # Wenn keine Daten erstellt wurden, erstelle einen Dummy-Datensatz
            if not data:
                today = datetime.datetime.now().strftime("%Y-%m-%d")
                data = [{
                    'timestamp': today,
                    'calendarDate': today,
                    'heatAcclimatization': 0,
                    'altitudeAcclimatization': 0
                }]
            
            # Konvertiere zu DataFrame
            df = pd.DataFrame(data)
            
            # Konvertiere Zeitstempel
            for col in ['timestamp', 'calendarDate']:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col])
            
            # Speichere im Cache
            self._cache_result(df.to_dict('records'), cache_file)
            
            logger.info(f"{len(df)} Hitze- und Höhenakklimatisierungseinträge erstellt.")
            return df
        except Exception as e:
            logger.error(f"Fehler beim Erstellen der Hitze- und Höhenakklimatisierungsdaten: {e}")
            # Erstelle einen Notfall-Datensatz
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            return pd.DataFrame([{
                'timestamp': today,
                'calendarDate': today,
                'heatAcclimatization': 0,
                'altitudeAcclimatization': 0
            }])