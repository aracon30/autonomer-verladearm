(* Automatischer Verladeablauf – entspricht tools/plc_simulator.py (sequence, fill_tank).
   Je Füllschritt (Kammer): Job 1 -> über den Dom -> Job 2 -> eintauchen -> Klappe auf, "Arm
   bereit" -> Befüllung durch die Leitstelle, Nachziehen über einen Grenzschalter -> Pumpe aus,
   Klappe zu, abtropfen -> heraus -> nächste Kammer (Job 1 vom Dom aus) oder Job 3 -> Park.
   Die Abtropfsicherung arbeitet rein mechanisch (keine Signale).

   Menge, Pumpe und Füllende steuert die Leitstelle. Schutzebenen
   (docs/fuellstand_ueberfuellsicherung.md):
   1. Leitstelle meldet "Befüllung Ende" (Pumpe aus),
   2. Maximalhöhe aus Armhöhe + Grenzschalter bzw. Arm kann nicht weiter nachziehen
      -> "Befüllung stoppen" an die Leitstelle,
   3. Überfüllsicherung – letzte Ebene, schaltet die Pumpe selbst ab; hier nur Störung.
   Reihenfolge immer: erst Pumpe aus (Rückmeldung + Auslaufzeit), dann Klappe zu.

   Muster: Bausteine werden je Zyklus genau einmal VOR dem CASE aufgerufen. Ein Schritt setzt
   den Startmerker, der nächste Schritt wartet auf Done/Error und nimmt den Merker zurück. *)
PROGRAM PRG_Main
VAR_OUTPUT
    iSchritt    : INT;
    sMeldung    : STRING(80);
END_VAR
VAR
    iKammer     : INT;                 (* Füllschritt 1..iPlsSchritte *)
    iWp         : INT;                 (* aktueller Stützpunkt *)
    fbJob       : FB_VisionJob;
    fbMove      : FB_SyncMove;
    xJobStart   : BOOL;
    iJobNr      : INT;
    iDomNr      : INT;
    xMoveStart  : BOOL;
    aZiel       : ARRAY[1..3] OF REAL;
    rFaktor     : REAL := 1.0;
    xWarten     : BOOL;
    tWarte      : TIME;
    tonWarte    : TON;
    rtStart     : R_TRIG;
    rtQuitt     : R_TRIG;
    (* Nachzieh-Tabelle aus Job 2 *)
    aTab        : ARRAY[1..16, 1..3] OF REAL;
    iTab        : INT;
    rTiefe      : REAL;                (* m unter Domrand *)
    rPosTab     : REAL;                (* 1 = Anfahrpunkt, iTab = eingetaucht *)
    rHoehe      : REAL;                (* Auslassende relativ zum Domrand [m] *)
    rSpiegel    : REAL;                (* Spiegel relativ zum Domrand [m] *)
    xNachStoppStoerung : BOOL;         (* nach dem Pumpenstopp in die Störung statt abtropfen *)
    tonTrocken  : TON;                 (* nach dem Hub muss der Grenzschalter trocken sein *)
    tonOhneSchalten : TON;             (* Pumpe läuft, Grenzschalter schaltet nicht *)
    tonPumpeAus : TON;                 (* Warten auf "Pumpe aus" *)
    tonAuslauf  : TON;                 (* Auslaufzeit der Pumpe *)
    xAuto       : BOOL;
    i           : INT;
END_VAR

rtStart(CLK := GVL_IO.xStartTaster);
rtQuitt(CLK := GVL_IO.xQuittTaster);

(* Bausteine: einmal je Zyklus *)
fbJob(xExecute := xJobStart, iJob := iJobNr, iProdukt := GVL_IO.iPlsProdukt, iDom := iDomNr);
fbMove(xExecute := xMoveStart, aZiel := aZiel, rFaktor := rFaktor, xAbbruch := iSchritt >= 900);
tonWarte(IN := xWarten, PT := tWarte);
tonTrocken(IN := iSchritt = 56, PT := GVL_Param.TROCKEN_ZEIT);
tonOhneSchalten(IN := iSchritt = 51 AND GVL_IO.xPlsPumpeLaeuft AND NOT GVL_IO.xGrenzNass,
                PT := GVL_Param.MAX_OHNE_SCHALTEN);
tonPumpeAus(IN := (iSchritt = 58 OR iSchritt = 900) AND GVL_IO.xPlsPumpeLaeuft,
            PT := GVL_Param.PUMPE_AUS_MAX);
tonAuslauf(IN := (iSchritt = 58 OR iSchritt = 900) AND NOT GVL_IO.xPlsPumpeLaeuft,
           PT := GVL_Param.PUMPE_AUSLAUF);

(* Verriegelungen während der Automatik *)
xAuto := GVL_IO.xSicherheitOk AND GVL_IO.xKlapptreppeRuhe AND PRG_Heartbeat.xPcOk
         AND NOT GVL_IO.xBetriebsartHand;
IF iSchritt > 0 AND iSchritt < 900 THEN
    IF NOT xAuto OR (NOT GVL_IO.xLichtschranke AND iSchritt < 80) THEN   (* bei Rückfahrt darf das Fahrzeug weg sein *)
        sMeldung := 'Verriegelung: Sicherheit, Treppe, Lichtschranke, PC oder Betriebsart';
        iSchritt := 900;
    ELSIF GVL_IO.xUeberfuellAus THEN
        sMeldung := 'Überfüllsicherung ausgelöst';
        iSchritt := 900;
    END_IF
END_IF

CASE iSchritt OF
0:  (* bereit *)
    GVL_Vision.ArmState := 0;
    GVL_Achsen.iBesitzer := 0;
    GVL_IO.xKlappeOeffnen := FALSE; GVL_IO.xArmBereit := FALSE; GVL_IO.xBefuellStoppen := FALSE;
    IF rtStart.Q AND F_InPark() AND xAuto AND GVL_IO.xLichtschranke AND GVL_IO.xPlsFreigabe
       AND GVL_Vision.Ready AND GVL_Vision.AxesHomed AND GVL_IO.iPlsSchritte >= 1 THEN
        GVL_Achsen.iBesitzer := 1;
        iKammer := 1;
        sMeldung := '';
        iSchritt := 10;
    END_IF

(* --- Job 1: Dom messen, Bahn planen ------------------------------------------------------- *)
10: iJobNr := 1; iDomNr := GVL_IO.aPlsDome[iKammer]; xJobStart := TRUE; iSchritt := 11;
11: IF fbJob.xDone THEN
        xJobStart := FALSE; iWp := 1; GVL_Vision.ArmState := 1; iSchritt := 20;
    ELSIF fbJob.xError THEN
        xJobStart := FALSE; sMeldung := CONCAT('Job 1: ', fbJob.sFehler); iSchritt := 900;
    END_IF

(* --- Stützpunkte bis über den Dom --------------------------------------------------------- *)
20: FOR i := 1 TO 3 DO aZiel[i] := fbJob.aWp[iWp, i]; END_FOR
    rFaktor := 1.0; xMoveStart := TRUE; iSchritt := 21;
21: IF fbMove.xDone THEN
        xMoveStart := FALSE;
        IF iWp < fbJob.iUeberDom THEN
            iWp := iWp + 1; iSchritt := 20;
        ELSE
            GVL_Vision.ArmState := 2; tWarte := GVL_Param.BERUHIGEN; xWarten := TRUE; iSchritt := 25;
        END_IF
    ELSIF fbMove.xError THEN
        xMoveStart := FALSE; sMeldung := fbMove.sFehler; iSchritt := 900;
    END_IF
25: IF tonWarte.Q THEN xWarten := FALSE; iSchritt := 30; END_IF

(* --- Job 2: Auslass nachmessen, Eintauch-Stützpunkte = Nachzieh-Tabelle ------------------- *)
30: iJobNr := 2; xJobStart := TRUE; iSchritt := 31;
31: IF fbJob.xDone THEN
        xJobStart := FALSE;
        iTab := fbJob.iAnzahl;
        FOR iWp := 1 TO iTab DO
            FOR i := 1 TO 3 DO aTab[iWp, i] := fbJob.aWp[iWp, i]; END_FOR
        END_FOR
        rTiefe := GVL_Param.aEintauchtiefe[LIMIT(0, GVL_IO.iPlsProdukt, 9)];
        iWp := 1; iSchritt := 40;
    ELSIF fbJob.xError THEN
        xJobStart := FALSE; sMeldung := CONCAT('Job 2: ', fbJob.sFehler); iSchritt := 80;
    END_IF

(* --- Eintauchen: Anfahrpunkt normal, danach langsam --------------------------------------- *)
40: FOR i := 1 TO 3 DO aZiel[i] := aTab[iWp, i]; END_FOR
    rFaktor := SEL(iWp = 1, GVL_Param.FAKTOR_LANGSAM, 1.0);
    xMoveStart := TRUE; iSchritt := 41;
41: IF fbMove.xDone THEN
        xMoveStart := FALSE;
        IF iWp < iTab THEN
            iWp := iWp + 1; iSchritt := 40;
        ELSE
            rPosTab := INT_TO_REAL(iTab);
            GVL_Vision.ArmState := 3;
            xNachStoppStoerung := FALSE;
            iSchritt := 50;
        END_IF
    ELSIF fbMove.xError THEN
        xMoveStart := FALSE; sMeldung := fbMove.sFehler; iSchritt := 900;
    END_IF

(* --- Klappe auf, "Arm bereit" an die Leitstelle -------------------------------------------- *)
50: GVL_IO.xKlappeOeffnen := TRUE; GVL_IO.xBefuellStoppen := FALSE;
    IF GVL_IO.xKlappeAuf THEN GVL_IO.xArmBereit := TRUE; iSchritt := 51; END_IF

(* --- Befüllung durch die Leitstelle, Nachziehen über einen Grenzschalter ------------------ *)
51: rHoehe := F_Hoehe(rPosTab, iTab, rTiefe);
    IF GVL_IO.xPlsBefuellEnde THEN                                  (* Ebene 1: Leitstelle *)
        sMeldung := 'Leitstelle: Befüllung Ende'; iSchritt := 58;
    ELSIF tonOhneSchalten.Q THEN
        sMeldung := 'Grenzschalter schaltet nicht (Pumpe läuft zu lange)';
        xNachStoppStoerung := TRUE; iSchritt := 58;
    ELSIF GVL_IO.xGrenzNass THEN                                    (* Spiegel auf Sensorhöhe *)
        rSpiegel := rHoehe + GVL_Param.SENSOR_HOEHE;
        IF rSpiegel >= -GVL_Param.rMaxHoeheUnterRand THEN
            sMeldung := 'Maximalhöhe erreicht – Befüllung stoppen'; iSchritt := 58;   (* Ebene 2 *)
        ELSIF rPosTab <= 1.0 THEN
            sMeldung := 'Arm kann nicht weiter nachziehen – Befüllung stoppen'; iSchritt := 58;
        ELSE                                                        (* Hub um NACHZIEH_SCHRITT *)
            rPosTab := F_PosFuerHoehe(rHoehe + GVL_Param.NACHZIEH_SCHRITT, iTab, rTiefe);
            FOR i := 1 TO 3 DO aZiel[i] := F_TabWinkel(rPosTab, iTab, i, aTab); END_FOR
            rFaktor := GVL_Param.FAKTOR_LANGSAM; xMoveStart := TRUE;
            iSchritt := 55;
        END_IF
    END_IF
55: (* Nachziehen läuft, Klappe bleibt auf, Pumpe läuft weiter *)
    IF fbMove.xDone THEN
        xMoveStart := FALSE; iSchritt := 56;
    ELSIF fbMove.xError THEN
        xMoveStart := FALSE; sMeldung := fbMove.sFehler; iSchritt := 900;
    END_IF
56: (* nach dem Hub muss der Grenzschalter trocken werden *)
    IF NOT GVL_IO.xGrenzNass THEN
        iSchritt := 51;
    ELSIF tonTrocken.Q THEN
        sMeldung := 'Grenzschalter nach dem Nachziehen weiter nass (Belag/Defekt)';
        xNachStoppStoerung := TRUE; iSchritt := 58;
    ELSIF GVL_IO.xPlsBefuellEnde THEN
        sMeldung := 'Leitstelle: Befüllung Ende'; iSchritt := 58;
    END_IF

(* --- erst Pumpe aus (Leitstelle), dann Klappe zu ----------------------------------------- *)
58: GVL_IO.xArmBereit := FALSE;
    GVL_IO.xBefuellStoppen := TRUE;                                 (* bei "Ende" ohnehin aus *)
    IF tonAuslauf.Q THEN
        iSchritt := 60;
    ELSIF tonPumpeAus.Q THEN
        sMeldung := 'Pumpe meldet nicht aus – Klappe zu'; xNachStoppStoerung := TRUE; iSchritt := 60;
    END_IF

(* --- Klappe zu, abtropfen ----------------------------------------------------------------- *)
60: GVL_IO.xKlappeOeffnen := FALSE; GVL_IO.xArmBereit := FALSE;
    IF GVL_IO.xKlappeZu THEN
        GVL_IO.xBefuellStoppen := FALSE;
        IF xNachStoppStoerung THEN
            iSchritt := 900;
        ELSE
            tWarte := GVL_Param.ABTROPFEN; xWarten := TRUE; iSchritt := 62;
        END_IF
    END_IF
62: IF tonWarte.Q THEN xWarten := FALSE; iSchritt := 65; END_IF

(* --- senkrecht heraus bis zum Anfahrpunkt ------------------------------------------------- *)
65: rPosTab := 1.0;
    FOR i := 1 TO 3 DO aZiel[i] := aTab[1, i]; END_FOR
    rFaktor := GVL_Param.FAKTOR_LANGSAM; xMoveStart := TRUE; iSchritt := 66;
66: IF fbMove.xDone THEN
        xMoveStart := FALSE; GVL_Vision.ArmState := 2; iSchritt := 70;
    ELSIF fbMove.xError THEN
        xMoveStart := FALSE; sMeldung := fbMove.sFehler; iSchritt := 900;
    END_IF

(* --- nächste Kammer oder Rückfahrt ------------------------------------------------------- *)
70: IF iKammer < GVL_IO.iPlsSchritte THEN
        iKammer := iKammer + 1; iSchritt := 10;
    ELSE
        iSchritt := 80;
    END_IF

(* --- Job 3: Rückfahrt in die Parkstellung ------------------------------------------------- *)
80: GVL_IO.xKlappeOeffnen := FALSE; GVL_IO.xArmBereit := FALSE;
    GVL_Achsen.iBesitzer := 1;
    iJobNr := 3; iDomNr := 0; xJobStart := TRUE; iSchritt := 81;
81: IF fbJob.xDone THEN
        xJobStart := FALSE; iWp := 1; GVL_Vision.ArmState := 1; iSchritt := 85;
    ELSIF fbJob.xError THEN
        xJobStart := FALSE; sMeldung := CONCAT('Job 3: ', fbJob.sFehler); iSchritt := 900;
    END_IF
85: FOR i := 1 TO 3 DO aZiel[i] := fbJob.aWp[iWp, i]; END_FOR
    rFaktor := SEL(iWp <= 2, 1.0, GVL_Param.FAKTOR_LANGSAM);     (* erst langsam heraus *)
    xMoveStart := TRUE; iSchritt := 86;
86: IF fbMove.xDone THEN
        xMoveStart := FALSE;
        IF iWp < fbJob.iAnzahl THEN
            iWp := iWp + 1; iSchritt := 85;
        ELSE
            GVL_Vision.ArmState := 0; GVL_Achsen.iBesitzer := 0;
            sMeldung := 'Parkstellung – Fahrzeug darf wegfahren'; iSchritt := 0;
        END_IF
    ELSIF fbMove.xError THEN
        xMoveStart := FALSE; sMeldung := fbMove.sFehler; iSchritt := 900;
    END_IF

(* --- Störung ------------------------------------------------------------------------------ *)
900: GVL_Achsen.xCmdStop := TRUE;
    (* Störung: Pumpe abschalten lassen, Klappe erst nach Pumpe aus (bzw. nach PUMPE_AUS_MAX) zu *)
    GVL_IO.xArmBereit := FALSE;
    GVL_IO.xBefuellStoppen := GVL_IO.xPlsPumpeLaeuft OR NOT GVL_IO.xKlappeZu;
    IF tonAuslauf.Q OR tonPumpeAus.Q OR NOT GVL_IO.xKlappeAuf THEN
        GVL_IO.xKlappeOeffnen := FALSE;
    END_IF
    GVL_Vision.ArmState := 9;
    xJobStart := FALSE; xMoveStart := FALSE; xWarten := FALSE;
    GVL_Achsen.xCmdReset := GVL_IO.xQuittTaster;
    IF rtQuitt.Q THEN iSchritt := 910; END_IF
910: (* quittiert: Start = "Automatisch in Parkstellung" (Job 3) oder Handbetrieb *)
    GVL_Achsen.xCmdStop := FALSE; GVL_Achsen.xCmdReset := FALSE;
    GVL_Achsen.iBesitzer := 0;
    GVL_IO.xKlappeOeffnen := FALSE;
    GVL_IO.xBefuellStoppen := GVL_IO.xPlsPumpeLaeuft;
    IF F_InPark() THEN
        GVL_Vision.ArmState := 0; iSchritt := 0;
    ELSIF rtStart.Q AND GVL_IO.xSicherheitOk AND NOT GVL_IO.xBetriebsartHand THEN
        iSchritt := 80;
    END_IF
END_CASE

(* Leuchtmelder *)
GVL_IO.xMeldeRot := iSchritt >= 900;
GVL_IO.xMeldeGelb := iSchritt > 0 AND iSchritt < 900;
GVL_IO.xMeldeGruen := iSchritt = 0 AND F_InPark();
GVL_IO.xLampeStart := iSchritt = 0 AND F_InPark() AND GVL_IO.xPlsFreigabe;
