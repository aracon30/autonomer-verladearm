(* Handbetrieb (Schlüsselschalter Hand) mit dem Handbediengerät: eine Achse wählen, mit + / −
   tippen, solange Zustimmtaster (Mittelstellung) gehalten wird. Reduzierte Geschwindigkeit,
   Software-Endlagen bleiben aktiv. Zustimmung und Not-Halt wertet die Sicherheitssteuerung aus;
   hier nur die Bewegung.

   Bremse lüften (nur J1/J2, Arm von Hand schieben): Antrieb in STO, Bremse über den
   Bremsausgang des Umrichters öffnen – Funktion und Freigabe bei SEW/Sicherheitskonzept klären.
   J3 nie lüften (Selbsthemmung nicht zugesichert). *)
PROGRAM PRG_Hand
VAR
    iAchse   : INT;
    xFahrt   : BOOL;
    i        : INT;
END_VAR

IF NOT GVL_IO.xBetriebsartHand OR PRG_Main.iSchritt <> 0 AND PRG_Main.iSchritt < 900 THEN
    xFahrt := FALSE;
    RETURN;
END_IF

iAchse := 0;
IF GVL_IO.xHandAchse1 THEN iAchse := 1;
ELSIF GVL_IO.xHandAchse2 THEN iAchse := 2;
ELSIF GVL_IO.xHandAchse3 THEN iAchse := 3;
END_IF

IF iAchse > 0 AND GVL_IO.xZustimmung AND GVL_IO.xSicherheitOk
   AND (GVL_IO.xHandPlus XOR GVL_IO.xHandMinus) THEN
    IF NOT xFahrt THEN
        (* Ziel = Endlage in Tipprichtung, andere Achsen bleiben stehen *)
        FOR i := 1 TO 3 DO
            GVL_Achsen.aCmdZiel[i] := GVL_Achsen.aIst[i];
            GVL_Achsen.aCmdV[i] := 0.001;
            GVL_Achsen.aCmdA[i] := 0.001;
        END_FOR
        GVL_Achsen.aCmdZiel[iAchse] := SEL(GVL_IO.xHandPlus, GVL_Param.aMin[iAchse], GVL_Param.aMax[iAchse]);
        GVL_Achsen.aCmdV[iAchse] := GVL_Param.aVmax[iAchse] * GVL_Param.FAKTOR_HAND;
        GVL_Achsen.aCmdA[iAchse] := GVL_Param.aAmax[iAchse];
        GVL_Achsen.iBesitzer := 2;
        GVL_Achsen.xCmdStop := FALSE;
        GVL_Achsen.xCmdStart := FALSE;   (* Flanke im nächsten Zyklus *)
        xFahrt := TRUE;
    ELSE
        GVL_Achsen.xCmdStart := TRUE;
    END_IF
ELSIF xFahrt THEN
    (* losgelassen: anhalten *)
    GVL_Achsen.xCmdStart := FALSE;
    GVL_Achsen.xCmdStop := TRUE;
    xFahrt := FALSE;
ELSE
    GVL_Achsen.xCmdStop := TRUE;      (* steht: Halt bleibt aktiv, Automatik nimmt ihn beim Start zurück *)
    GVL_Achsen.iBesitzer := 0;
END_IF
