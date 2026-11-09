(* Ein- und Ausgänge. Im Gerätebaum (E/A-Abbild der PROFINET-Geräte) diesen Variablen zuordnen.
   Sicherheitssignale kommen als MELDUNG der Sicherheitssteuerung – sie schaltet STO selbst,
   die SPS kann sie nicht überstimmen. *)
{attribute 'qualified_only'}
VAR_GLOBAL
    (* Bedienung am Schaltschrank *)
    xStartTaster      : BOOL;   (* Leuchttaster "Beladen starten" *)
    xQuittTaster      : BOOL;   (* Quittieren *)
    xBetriebsartHand  : BOOL;   (* Schlüsselschalter: TRUE = Hand, FALSE = Automatik *)
    xLampeStart       : BOOL;   (* Lampe im Starttaster *)
    xMeldeGruen       : BOOL;   (* Park / bereit, Fahrzeug darf fahren *)
    xMeldeGelb        : BOOL;   (* Automatik läuft *)
    xMeldeRot         : BOOL;   (* Störung *)

    (* Handbediengerät (Zustimmung wertet die Sicherheitssteuerung aus) *)
    xHandAchse1       : BOOL;
    xHandAchse2       : BOOL;
    xHandAchse3       : BOOL;
    xHandPlus         : BOOL;
    xHandMinus        : BOOL;
    xHandBremseLueften: BOOL;   (* nur J1/J2, Freigabe zusätzlich durch Sicherheitssteuerung *)

    (* Meldungen der Sicherheitssteuerung *)
    xSicherheitOk     : BOOL;   (* kein Not-Halt, STO aufgehoben *)
    xZustimmung       : BOOL;   (* Zustimmtaster Mittelstellung (nur Hand) *)
    xKlapptreppeRuhe  : BOOL;   (* Klapptreppe in Ruhelage *)
    xLichtschranke    : BOOL;   (* Stellplatz belegt *)

    (* Prozess *)
    xGrenzA           : BOOL;   (* Grenzschalter A, ca. 1 cm über Auslassende: nass *)
    xGrenzB           : BOOL;   (* Grenzschalter B, ca. 3 cm über Auslassende: nass *)
    rDurchflussMenge  : REAL;   (* Menge laut Durchflussmesser [m³], zählt ab Klappe auf *)
    xDurchflussOk     : BOOL;   (* Gerät meldet gültigen Messwert *)
    xUeberfuellAus    : BOOL;   (* Überfüllsicherung ausgelöst (schaltet die Pumpe selbst ab) *)
    xKlappeAuf        : BOOL;   (* Absperrklappe Rückmeldung auf *)
    xKlappeZu         : BOOL;   (* Absperrklappe Rückmeldung zu *)
    xKlappeOeffnen    : BOOL;   (* Ausgang Absperrklappe *)
    xPumpeFreigabe    : BOOL;   (* Freigabe Pumpe an PLS / Pumpensteuerung *)

    (* Abtropfsicherung: rein mechanisch, keine Signale (Entscheidung 04.11.2026) *)

    (* Leitstelle (PLS) – Signale mit BASF abstimmen *)
    xPlsFreigabe      : BOOL;
    iPlsProdukt       : INT;
    rPlsSollmenge     : REAL;   (* m³ gesamt *)
    aPlsDome          : ARRAY[1..4] OF INT;    (* Füllschritte: DomeNo, 0 = automatisch *)
    aPlsMenge         : ARRAY[1..4] OF REAL;   (* Menge je Füllschritt [m³] *)
    iPlsSchritte      : INT;    (* Anzahl Füllschritte, 1 = Kammern verbunden *)
    xPlsBeenden       : BOOL;   (* "Verladung beenden" *)
END_VAR
