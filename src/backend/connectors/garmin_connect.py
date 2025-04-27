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
            with open(cache_path, 'w') as f:
                json.dump(data, f)
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
                return pd.DataFrame(cached_data)
        
        try:
            logger.info(f"Rufe Gewichtsdaten von {start_date} bis {end_date} ab...")
            # Konvertiere Strings zu datetime.date für die API
            start = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
            
            weight_data = self.client.get_body_composition(start, end)
            
            # Speichere im Cache
            self._cache_result(weight_data, cache_file)
            
            # Konvertiere zu DataFrame
            df = pd.DataFrame(weight_data)
            
            # Konvertiere Zeitstempel
            for col in df.columns:
                if 'date' in col.lower() or 'time' in col.lower():
                    try:
                        df[col] = pd.to_datetime(df[col])
                    except:
                        pass
            
            logger.info(f"{len(df)} Gewichtsdaten abgerufen.")
            return df
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Gewichtsdaten: {e}")
            raise
    
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
                return pd.DataFrame(cached_data)
        
        try:
            logger.info(f"Rufe Herzfrequenzdaten von {start_date} bis {end_date} ab...")
            # Konvertiere String-Daten in datetime.date-Objekte für die API
            start = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
            
            # Sammle Daten für jeden Tag im Zeitraum
            all_data = []
            current = start
            while current <= end:
                try:
                    day_data = self.client.get_heart_rates(current)
                    if day_data:
                        for entry in day_data:
                            entry['date'] = current.strftime("%Y-%m-%d")
                        all_data.extend(day_data)
                except Exception as e:
                    logger.warning(f"Fehler beim Abrufen der Herzfrequenzdaten für {current}: {e}")
                
                # Nächster Tag
                current += datetime.timedelta(days=1)
            
            # Speichere im Cache
            self._cache_result(all_data, cache_file)
            
            # Konvertiere zu DataFrame
            df = pd.DataFrame(all_data)
            if not df.empty and 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
            
            logger.info(f"{len(df)} Herzfrequenzdaten abgerufen.")
            return df
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Herzfrequenzdaten: {e}")
            raise
    
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
                df = pd.DataFrame(cached_data)
                # Spezielle Behandlung für verschachtelte Daten
                df = self._process_sleep_data(df)
                return df
        
        try:
            logger.info(f"Rufe Schlafdaten von {start_date} bis {end_date} ab...")
            # Konvertiere String-Daten in datetime.date-Objekte für die API
            start = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
            
            # Sammle Daten für jeden Tag im Zeitraum
            all_data = []
            current = start
            while current <= end:
                try:
                    day_data = self.client.get_sleep_data(current)
                    if day_data:
                        for entry in day_data:
                            entry['date'] = current.strftime("%Y-%m-%d")
                        all_data.extend(day_data)
                except Exception as e:
                    logger.warning(f"Fehler beim Abrufen der Schlafdaten für {current}: {e}")
                
                # Nächster Tag
                current += datetime.timedelta(days=1)
            
            # Speichere im Cache
            self._cache_result(all_data, cache_file)
            
            # Konvertiere zu DataFrame
            df = pd.DataFrame(all_data)
            
            # Verarbeite die verschachtelten Schlafdaten
            df = self._process_sleep_data(df)
            
            logger.info(f"{len(df)} Schlafdaten abgerufen.")
            return df
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Schlafdaten: {e}")
            raise
    
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
                return pd.DataFrame(cached_data)
        
        try:
            logger.info(f"Rufe Stressdaten von {start_date} bis {end_date} ab...")
            # Konvertiere String-Daten in datetime.date-Objekte für die API
            start = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
            
            # Sammle Daten für jeden Tag im Zeitraum
            all_data = []
            current = start
            while current <= end:
                try:
                    # Versuche den API-Aufruf für Stressdaten, falls verfügbar
                    if hasattr(self.client, 'get_stress_data'):
                        day_data = self.client.get_stress_data(current)
                    else:
                        # Alternative Methode, falls vorhanden
                        day_data = []
                        
                    if day_data:
                        for entry in day_data:
                            entry['date'] = current.strftime("%Y-%m-%d")
                        all_data.extend(day_data)
                except Exception as e:
                    logger.warning(f"Fehler beim Abrufen der Stressdaten für {current}: {e}")
                
                # Nächster Tag
                current += datetime.timedelta(days=1)
            
            # Speichere im Cache
            self._cache_result(all_data, cache_file)
            
            # Konvertiere zu DataFrame
            df = pd.DataFrame(all_data)
            if not df.empty and 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
            
            logger.info(f"{len(df)} Stressdaten abgerufen.")
            return df
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Stressdaten: {e}")
            raise
    
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
                vo2max_data = self.client.get_max_metrics()
                metrics['vo2max'] = vo2max_data
                logger.info("VO2Max-Daten abgerufen.")
            except Exception as e:
                logger.warning(f"Fehler beim Abrufen der VO2Max-Daten: {e}")
            
            # User Summary
            try:
                user_summary = self.client.get_user_summary(start_date, end_date)
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
            # Stattdessen erstellen wir einen Dummy-Datensatz basierend auf Aktivitäten
            activities = self.get_activities(
                start_date=(datetime.datetime.now() - datetime.timedelta(days=90)).strftime("%Y-%m-%d"),
                end_date=datetime.datetime.now().strftime("%Y-%m-%d"),
                use_cache=use_cache
            )
            
            data = []
            
            # Wenn Aktivitäten verfügbar sind, verwende diese für Approximationen
            if not activities.empty:
                # Gruppiere Aktivitäten nach Tag
                activities['day'] = activities['startTimeLocal'].dt.date
                daily_stats = activities.groupby('day').agg({
                    'startTimeLocal': 'first',  # Erstes Datum des Tages
                    'distance': 'sum',  # Gesamtdistanz
                    'duration': 'sum',  # Gesamtdauer
                    'avgHr': 'mean',  # Durchschnittliche Herzfrequenz
                    'maxHr': 'max',  # Maximale Herzfrequenz
                    'calories': 'sum',  # Gesamtkalorien
                    'minTemperature': 'min',  # Minimale Temperatur
                    'maxTemperature': 'max',  # Maximale Temperatur
                })
                
                # Für jeden Tag einen Datensatz erstellen
                for idx, row in daily_stats.iterrows():
                    # Dummy-Werte für Hitze- und Höhenakklimatisierung
                    heat_acclimatization = 0
                    altitude_acclimatization = 0
                    
                    # Wenn Temperaturwerte vorhanden sind, berücksichtige sie für Hitzeakklimatisierung
                    if not pd.isna(row.get('maxTemperature', None)):
                        max_temp = row['maxTemperature']
                        # Beispiel: Über 25°C trägt zur Hitzeakklimatisierung bei
                        if max_temp > 25:
                            heat_acclimatization = min(100, (max_temp - 25) * 10)  # 10 Punkte pro Grad über 25
                    
                    # Datensatz für diesen Tag
                    entry = {
                        'timestamp': row['startTimeLocal'].strftime("%Y-%m-%d"),
                        'calendarDate': row['startTimeLocal'].strftime("%Y-%m-%d"),
                        'heatAcclimatization': heat_acclimatization,
                        'altitudeAcclimatization': altitude_acclimatization
                    }
                    data.append(entry)
            
            # Wenn keine Aktivitätsdaten verfügbar sind, erstelle einen Dummy-Datensatz
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
            raise