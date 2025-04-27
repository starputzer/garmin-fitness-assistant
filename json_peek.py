#!/usr/bin/env python
"""
Ein einfaches Skript zum Auslesen der ersten Teile einer großen JSON-Datei.
Nutze: python json_peek.py pfad/zur/datei.json
"""

import sys
import json

def peek_json(file_path, bytes_to_read=10000):
    """Liest den Anfang einer JSON-Datei und versucht, die Struktur zu analysieren."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # Lese die ersten X Bytes
            start_content = f.read(bytes_to_read)
            
            # Prüfe, ob es ein JSON-Array ist
            if start_content.strip().startswith('['):
                print("JSON-Datei beginnt mit einem Array")
                
                # Suche nach der ersten schließenden Klammer
                bracket_level = 0
                for i, char in enumerate(start_content):
                    if char == '[':
                        bracket_level += 1
                    elif char == ']':
                        bracket_level -= 1
                        if bracket_level == 0:
                            # Ende des ersten Arrays gefunden
                            break
                
                # Wenn kein Ende gefunden, nutze so viel wie wir haben
                # Entferne Komma am Ende, wenn vorhanden
                if bracket_level > 0:
                    # Finde das letzte Komma vor Ende
                    last_obj_end = max(start_content.rfind('},'), start_content.rfind('}]'))
                    if last_obj_end > 0:
                        # Schließe das Array manuell
                        complete_json = start_content[:last_obj_end+1] + "]"
                    else:
                        print("Konnte kein vollständiges Objekt im Array finden")
                        return
                else:
                    complete_json = start_content
                
                # Parse das JSON
                try:
                    data = json.loads(complete_json)
                    if isinstance(data, list) and len(data) > 0:
                        # Zeige die Struktur des ersten Elements
                        print("\nStruktur des ersten Elements:")
                        first_item = data[0]
                        if isinstance(first_item, dict):
                            print(f"Schlüssel: {list(first_item.keys())}")
                            print("\nBeispielwerte:")
                            for key, value in first_item.items():
                                print(f"  {key}: {value}")
                        else:
                            print(f"Typ: {type(first_item)}")
                            print(f"Wert: {first_item}")
                except json.JSONDecodeError as e:
                    print(f"Fehler beim Parsen des teilweise gelesenen JSON: {e}")
            
            # Wenn es ein JSON-Objekt ist
            elif start_content.strip().startswith('{'):
                print("JSON-Datei beginnt mit einem Objekt")
                try:
                    # Versuche, das erste Objekt zu laden
                    obj_end = start_content.find('}')
                    if obj_end > 0:
                        obj_json = start_content[:obj_end+1]
                        data = json.loads(obj_json)
                        print("\nGefundene Schlüssel:")
                        print(list(data.keys()))
                    else:
                        print("Konnte Ende des Objekts nicht finden")
                except json.JSONDecodeError as e:
                    print(f"Fehler beim Parsen des teilweise gelesenen JSON: {e}")
            else:
                print("Unbekanntes JSON-Format")
                print(start_content[:100] + "...")
    except Exception as e:
        print(f"Fehler beim Öffnen oder Lesen der Datei: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Verwendung: python json_peek.py pfad/zur/datei.json [bytes_to_read]")
        sys.exit(1)
    
    file_path = sys.argv[1]
    bytes_to_read = int(sys.argv[2]) if len(sys.argv) > 2 else 10000
    
    peek_json(file_path, bytes_to_read)
