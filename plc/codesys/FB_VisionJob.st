(* Auftrag an den Vision-PC (Handshake docs/schnittstelle.md) mit Plausibilitätsprüfung der
   Stützpunkte. Ergebnis bleibt bis zum nächsten Auftrag in den Ausgängen. *)
FUNCTION_BLOCK FB_VisionJob
VAR_INPUT
    xExecute  : BOOL;
    iJob      : INT;
    iProdukt  : INT;
    iDom      : INT;
END_VAR
VAR_OUTPUT
    xBusy     : BOOL;
    xDone     : BOOL;
    xError    : BOOL;
    iFehler   : INT;              (* Fehlercode Vision bzw. 100 + Prüfung SPS *)
    sFehler   : STRING(80);
    iAnzahl   : INT;              (* gültige Stützpunkte *)
    aWp       : ARRAY[1..16, 1..3] OF REAL;
    iUeberDom : INT;              (* ApproachIndex *)
    rDomZ     : REAL;             (* Oberkante Domöffnung [m, Armbasis] *)
    rKorrX, rKorrY : REAL;        (* mm *)
    iDomeCount, iDomeSelected : INT;
END_VAR
VAR
    rtExec    : R_TRIG;
    iSchritt  : INT;
    tonTimeout: TON;
    i, k      : INT;
    aWert     : ARRAY[1..3] OF REAL;
END_VAR

rtExec(CLK := xExecute);
IF rtExec.Q AND iSchritt = 0 THEN
    xDone := FALSE; xError := FALSE; iFehler := 0; sFehler := '';
    iSchritt := 1;
END_IF

CASE iSchritt OF
1:  IF NOT GVL_Vision.Ready THEN
        xError := TRUE; iFehler := 101; sFehler := 'Vision-PC nicht bereit'; iSchritt := 0;
    ELSIF GVL_Vision.InterfaceVersion <> GVL_Param.INTERFACE_VERSION THEN
        xError := TRUE; iFehler := 102; sFehler := 'falsche InterfaceVersion'; iSchritt := 0;
    ELSE
        GVL_Vision.Job := iJob;
        GVL_Vision.ProductId := iProdukt;
        GVL_Vision.DomeNo := iDom;
        GVL_Vision.Trigger := TRUE;
        iSchritt := 2;
    END_IF

2:  IF GVL_Vision.Done THEN
        (* Ergebnis übernehmen *)
        iFehler := GVL_Vision.ErrorCode;
        iAnzahl := LIMIT(0, GVL_Vision.WaypointCount, GVL_Param.MAX_WP);
        FOR i := 1 TO GVL_Param.MAX_WP DO
            aWp[i, 1] := GVL_Vision.WaypointsJ1[i];
            aWp[i, 2] := GVL_Vision.WaypointsJ2[i];
            aWp[i, 3] := GVL_Vision.WaypointsJ3[i];
        END_FOR
        iUeberDom := GVL_Vision.ApproachIndex;
        rDomZ := GVL_Vision.TargetZ / 1000.0;
        rKorrX := GVL_Vision.CorrectionX;
        rKorrY := GVL_Vision.CorrectionY;
        iDomeCount := GVL_Vision.DomeCount;
        iDomeSelected := GVL_Vision.DomeSelected;
        IF GVL_Vision.Error THEN
            xError := TRUE; sFehler := 'Vision-Fehler (Code siehe iFehler)';
        ELSE
            (* Plausibilität: Achsgrenzen jedes Stützpunkts *)
            FOR i := 1 TO iAnzahl DO
                FOR k := 1 TO 3 DO
                    IF aWp[i, k] < GVL_Param.aMin[k] OR aWp[i, k] > GVL_Param.aMax[k] THEN
                        xError := TRUE; iFehler := 103; sFehler := 'Stützpunkt außerhalb der Achsgrenzen';
                    END_IF
                END_FOR
            END_FOR
            IF iJob <> 0 AND iAnzahl = 0 THEN
                xError := TRUE; iFehler := 104; sFehler := 'keine Stützpunkte';
            END_IF
            IF iJob = 2 AND (ABS(rKorrX) > GVL_Param.MAX_KORREKTUR OR ABS(rKorrY) > GVL_Param.MAX_KORREKTUR) THEN
                xError := TRUE; iFehler := 105; sFehler := 'Korrektur Job 2 zu groß';
            END_IF
        END_IF
        GVL_Vision.Trigger := FALSE;
        iSchritt := 3;
    ELSIF tonTimeout.Q THEN
        GVL_Vision.Trigger := FALSE;
        xError := TRUE; iFehler := 106; sFehler := 'Zeitüberschreitung Vision-PC';
        iSchritt := 0;
    END_IF

3:  IF NOT GVL_Vision.Done THEN      (* PC hat Done gelöscht *)
        xDone := NOT xError;
        iSchritt := 0;
    ELSIF tonTimeout.Q THEN
        xError := TRUE; iFehler := 107; sFehler := 'Done wird nicht gelöscht'; iSchritt := 0;
    END_IF
END_CASE

tonTimeout(IN := iSchritt = 2 OR iSchritt = 3, PT := GVL_Param.TIMEOUT_JOB);
xBusy := iSchritt <> 0;
