(* Synchrone Fahrt aller drei Achsen zu einem Stützpunkt (docs/schnittstelle.md):
   Die langsamste Achse bestimmt die Fahrzeit; jede Achse bekommt Geschwindigkeit und
   Beschleunigung proportional zu ihrem Weg, gleiche Ruckzeit auf allen Achsen -> alle starten
   und kommen gleichzeitig an, der Arm fährt die geprüfte Gerade im Gelenkraum.
   Gleiche Rechnung wie Drives.sync() in vision/src/verladearm_vision/drives.py. *)
FUNCTION_BLOCK FB_SyncMove
VAR_INPUT
    xExecute : BOOL;                   (* steigende Flanke startet *)
    aZiel    : ARRAY[1..3] OF REAL;    (* ° *)
    rFaktor  : REAL := 1.0;            (* Geschwindigkeitsfaktor, z. B. 0,3 beim Eintauchen *)
    xAbbruch : BOOL;                   (* Halt mit Verzögerung *)
END_VAR
VAR_OUTPUT
    xBusy    : BOOL;
    xDone    : BOOL;
    xError   : BOOL;
    sFehler  : STRING(80);
    rDauer   : REAL;                   (* s, berechnete Fahrzeit *)
END_VAR
VAR
    rtExec   : R_TRIG;
    iSchritt : INT;
    tonZeit  : TON;
    i        : INT;
    d        : ARRAY[1..3] OF REAL;
    rCruise, rPush, rRamp : REAL;
    rFak     : REAL;
END_VAR

rtExec(CLK := xExecute);
IF rtExec.Q THEN
    xDone := FALSE; xError := FALSE; sFehler := '';
    rFak := LIMIT(0.01, rFaktor, 1.0);
    rCruise := 0.0; rPush := 0.0;
    FOR i := 1 TO 3 DO
        aZiel[i] := LIMIT(GVL_Param.aMin[i], aZiel[i], GVL_Param.aMax[i]);   (* Software-Endlagen *)
        d[i] := ABS(aZiel[i] - GVL_Achsen.aIst[i]);
        rCruise := MAX(rCruise, d[i] / (GVL_Param.aVmax[i] * rFak));
        rPush := MAX(rPush, d[i] / GVL_Param.aAmax[i]);
    END_FOR
    IF rPush < 1.0E-6 THEN
        xDone := TRUE; iSchritt := 0;       (* schon am Ziel *)
    ELSE
        IF SQRT(rPush) >= rCruise THEN      (* Dreieck: Höchstgeschwindigkeit nicht erreicht *)
            rCruise := SQRT(rPush); rRamp := rCruise;
        ELSE
            rRamp := rPush / rCruise;
        END_IF
        rDauer := rCruise + rRamp + GVL_Param.rRuckzeit;
        FOR i := 1 TO 3 DO
            GVL_Achsen.aCmdZiel[i] := aZiel[i];
            GVL_Achsen.aCmdV[i] := MAX(d[i] / rCruise, 0.001);
            GVL_Achsen.aCmdA[i] := MAX(d[i] / rCruise / rRamp, 0.001);
        END_FOR
        GVL_Achsen.xCmdStart := FALSE;      (* ein Zyklus FALSE, damit die Flanke kommt *)
        GVL_Achsen.xCmdStop := FALSE;
        iSchritt := 1;
    END_IF
END_IF

CASE iSchritt OF
1:  GVL_Achsen.xCmdStart := TRUE;
    iSchritt := 2;
2:  (* warten bis alle Achsen am Ziel; Zeitüberwachung *)
    IF xAbbruch THEN
        GVL_Achsen.xCmdStop := TRUE;
        xError := TRUE; sFehler := 'Fahrt abgebrochen'; iSchritt := 0;
    ELSIF GVL_Achsen.xAchsFehler THEN
        xError := TRUE; sFehler := 'Achsfehler (Umrichter)'; iSchritt := 0;
    ELSIF tonZeit.Q THEN
        GVL_Achsen.xCmdStop := TRUE;
        xError := TRUE; sFehler := 'Zeitüberschreitung Fahrt'; iSchritt := 0;
    ELSIF GVL_Achsen.xAlleInPos AND tonZeit.ET > T#200MS THEN
        xDone := TRUE; iSchritt := 0;
    END_IF
END_CASE

tonZeit(IN := iSchritt = 2,
        PT := REAL_TO_TIME(rDauer * 1000.0) + GVL_Param.TIMEOUT_MOVE_ADD);
xBusy := iSchritt <> 0;
