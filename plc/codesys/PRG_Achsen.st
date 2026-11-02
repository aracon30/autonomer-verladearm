(* Jeden Zyklus: drei Achsen bedienen, Istwerte an den Vision-PC. Vor PRG_Main aufrufen. *)
PROGRAM PRG_Achsen
VAR
    fbAchse : ARRAY[1..3] OF FB_PdAxis;
    i       : INT;
END_VAR

GVL_Achsen.xAlleBereit := TRUE;
GVL_Achsen.xAlleInPos := TRUE;
GVL_Achsen.xAchsFehler := FALSE;
FOR i := 1 TO 3 DO
    fbAchse[i](
        xEnable := GVL_IO.xSicherheitOk,
        xStart  := GVL_Achsen.xCmdStart,
        xStop   := GVL_Achsen.xCmdStop,
        xReset  := GVL_Achsen.xCmdReset,
        rZiel   := GVL_Achsen.aCmdZiel[i],
        rV      := GVL_Achsen.aCmdV[i],
        rA      := GVL_Achsen.aCmdA[i],
        stPd    := GVL_Achsen.aPd[i]);
    GVL_Achsen.aIst[i] := fbAchse[i].rIst;
    GVL_Achsen.xAlleBereit := GVL_Achsen.xAlleBereit AND fbAchse[i].xBereit;
    GVL_Achsen.xAlleInPos := GVL_Achsen.xAlleInPos AND fbAchse[i].xInPos;
    GVL_Achsen.xAchsFehler := GVL_Achsen.xAchsFehler OR fbAchse[i].xFehler;
END_FOR

(* Multiturn-Absolutgeber: Lage gilt sofort, keine Referenzfahrt *)
GVL_Vision.ActualJ1 := GVL_Achsen.aIst[1];
GVL_Vision.ActualJ2 := GVL_Achsen.aIst[2];
GVL_Vision.ActualJ3 := GVL_Achsen.aIst[3];
GVL_Vision.AxesHomed := GVL_Achsen.xAlleBereit AND NOT GVL_Achsen.xAchsFehler;
