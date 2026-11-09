(* Ein- und Ausgänge. Im Gerätebaum (TwinCAT: E/A-Abbild der EtherCAT-Klemmen bzw. PROFINET-
   Geräte) diesen Variablen zuordnen. Sicherheitssignale kommen als MELDUNG der Sicherheits-
   steuerung (TwinSAFE) – sie schaltet STO selbst, die SPS kann sie nicht überstimmen.
   Not-Halt am Arm schaltet die Pumpe festverdrahtet über die Sicherheitssteuerung ab (nicht hier). *)
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

    (* Prozess am Arm *)
    xGrenzNass        : BOOL;   (* Grenzschalter Nachziehen, ca. 10–15 cm über Auslassende: nass *)
    xUeberfuellAus    : BOOL;   (* Überfüllsicherung ausgelöst (schaltet die Pumpe selbst ab) *)
    xKlappeAuf        : BOOL;   (* Absperrklappe Rückmeldung auf *)
    xKlappeZu         : BOOL;   (* Absperrklappe Rückmeldung zu *)
    xKlappeOeffnen    : BOOL;   (* Ausgang Absperrklappe (gehört zum Arm) *)

    (* Abtropfsicherung: rein mechanisch, keine Signale (Entscheidung 04.11.2026) *)

    (* Leitstelle (PLS) – Menge, Pumpe und Füllende steuert die Leitstelle; Signale mit BASF
       abstimmen (Mail an BASF 09.11.2026) *)
    xPlsFreigabe      : BOOL;   (* Verladung freigegeben (Auftrag liegt vor) *)
    iPlsProdukt       : INT;
    aPlsDome          : ARRAY[1..4] OF INT;    (* Füllschritte: DomeNo, 0 = automatisch *)
    iPlsSchritte      : INT;    (* Anzahl Füllschritte (Kammern), 1 = Kammern verbunden *)
    xPlsPumpeLaeuft   : BOOL;   (* Rückmeldung: Pumpe läuft *)
    xPlsBefuellEnde   : BOOL;   (* "Befüllung Ende" für den aktuellen Füllschritt (Pumpe aus) *)
    xArmBereit        : BOOL;   (* an PLS: Arm im Tank, Klappe offen – Befüllung freigegeben *)
    xBefuellStoppen   : BOOL;   (* an PLS: Pumpe abschalten (Störung, Maximalhöhe, Arm am Ende) *)
END_VAR
