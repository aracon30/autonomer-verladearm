(* Hilfsfunktionen für den Ablauf. In CODESYS je Funktion ein eigenes Objekt (POU) anlegen. *)

(* ---------------------------------------------------------------------------------------- *)
(* Arm in Parkstellung? *)
FUNCTION F_InPark : BOOL
VAR
    i : INT;
END_VAR
F_InPark := TRUE;
FOR i := 1 TO 3 DO
    IF ABS(GVL_Achsen.aIst[i] - GVL_Param.aPark[i]) > GVL_Param.TOL_PARK THEN
        F_InPark := FALSE;
    END_IF
END_FOR
END_FUNCTION

(* ---------------------------------------------------------------------------------------- *)
(* Höhe des Auslassendes relativ zum Domrand [m] für eine Lage in der Nachzieh-Tabelle.
   Tabelle = Eintauch-Stützpunkte aus Job 2, gleichmäßig von ANFAHRHOEHE über dem Rand (Lage 1)
   bis rTiefe unter dem Rand (Lage iTab). *)
FUNCTION F_Hoehe : REAL
VAR_INPUT
    rPos   : REAL;   (* 1 .. iTab *)
    iTab   : INT;
    rTiefe : REAL;
END_VAR
IF iTab < 2 THEN
    F_Hoehe := GVL_Param.ANFAHRHOEHE;
ELSE
    F_Hoehe := GVL_Param.ANFAHRHOEHE
               - (rPos - 1.0) / INT_TO_REAL(iTab - 1) * (GVL_Param.ANFAHRHOEHE + rTiefe);
END_IF
END_FUNCTION

(* ---------------------------------------------------------------------------------------- *)
(* Umkehrung: Lage in der Tabelle für eine Höhe relativ zum Domrand. *)
FUNCTION F_PosFuerHoehe : REAL
VAR_INPUT
    rHoehe : REAL;
    iTab   : INT;
    rTiefe : REAL;
END_VAR
IF iTab < 2 THEN
    F_PosFuerHoehe := 1.0;
ELSE
    F_PosFuerHoehe := LIMIT(1.0,
        1.0 + (GVL_Param.ANFAHRHOEHE - rHoehe) / (GVL_Param.ANFAHRHOEHE + rTiefe) * INT_TO_REAL(iTab - 1),
        INT_TO_REAL(iTab));
END_IF
END_FUNCTION

(* ---------------------------------------------------------------------------------------- *)
(* Servowinkel einer Achse für eine Lage in der Tabelle: zwischen den Stützpunkten linear im
   Gelenkraum (wie tools/plc_simulator.py table_at). *)
FUNCTION F_TabWinkel : REAL
VAR_INPUT
    rPos   : REAL;
    iTab   : INT;
    iAchse : INT;
END_VAR
VAR_IN_OUT
    aTab   : ARRAY[1..16, 1..3] OF REAL;
END_VAR
VAR
    k : INT;
    u : REAL;
END_VAR
k := LIMIT(1, DINT_TO_INT(TRUNC(rPos)), MAX(iTab - 1, 1));
u := LIMIT(0.0, rPos - INT_TO_REAL(k), 1.0);
IF iTab < 2 THEN
    F_TabWinkel := aTab[1, iAchse];
ELSE
    F_TabWinkel := aTab[k, iAchse] + u * (aTab[k + 1, iAchse] - aTab[k, iAchse]);
END_IF
END_FUNCTION
