(* Prozessdaten eines MOVITRAC advanced mit MOVIKIT Positioning Drive (Applikationslevel 1, 8 PD).
   Belegung nach Handbuch 33350930 (11/2025), Kap. 8 – im E/A-Abbild des PROFINET-Geräts auf
   diese Felder legen. *)
TYPE ST_PdAxis :
STRUCT
    aPA : ARRAY[1..8] OF WORD;   (* SPS -> Umrichter *)
        (* PA1 Steuerwort, PA2 Geschwindigkeit, PA3 Beschleunigung, PA4 Verzögerung,
           PA5 Ausgänge, PA6 Betriebsart (400 = absolut), PA7/PA8 Zielposition (32 Bit, High/Low) *)
    aPE : ARRAY[1..8] OF WORD;   (* Umrichter -> SPS *)
        (* PE1 Statuswort, PE2 Geschwindigkeit, PE3 Fehlercode, PE4 Moment, PE5 Eingänge,
           PE6 aktive Betriebsart, PE7/PE8 Istposition (32 Bit, High/Low) *)
END_STRUCT
END_TYPE
