(* Eine Achse über MOVIKIT Positioning Drive: Ziel, Geschwindigkeit, Beschleunigung vorgeben,
   Istposition und Status lesen. Positionieren, Rampen und Ruckbegrenzung macht der Umrichter.

   !!! Bitbelegung von Steuer- und Statuswort und die Anwendereinheiten vor der Inbetriebnahme
   mit dem SEW-Handbuch (Kap. 8) und MOVISUITE abgleichen – hier als Konstanten mit
   Platzhalterwerten. Anwendereinheit: 1 Inkrement = 0,001° am Gelenk (in MOVISUITE einstellen). *)
FUNCTION_BLOCK FB_PdAxis
VAR_INPUT
    xEnable  : BOOL;          (* Freigabe (STO aufgehoben, keine Störung) *)
    xStart   : BOOL;          (* steigende Flanke: neues Ziel übernehmen *)
    xStop    : BOOL;          (* Halt mit Verzögerung *)
    xReset   : BOOL;          (* Fehler quittieren *)
    rZiel    : REAL;          (* ° *)
    rV       : REAL;          (* °/s *)
    rA       : REAL;          (* °/s² (Beschleunigung = Verzögerung) *)
END_VAR
VAR_OUTPUT
    rIst     : REAL;          (* ° *)
    xBereit  : BOOL;          (* Umrichter bereit / freigegeben *)
    xInPos   : BOOL;          (* Position erreicht *)
    xFehler  : BOOL;
    wFehler  : WORD;
END_VAR
VAR_IN_OUT
    stPd     : ST_PdAxis;
END_VAR
VAR CONSTANT
    EINHEIT_POS    : REAL := 1000.0;     (* Inkremente je ° (Anwendereinheit 0,001°) *)
    EINHEIT_V      : REAL := 100.0;      (* PA2: 0,01 °/s – prüfen *)
    EINHEIT_A      : REAL := 100.0;      (* PA3/PA4: 0,01 °/s² – prüfen *)
    BETRIEBSART_ABS: WORD := 400;
    (* Steuerwort PA1 – PLATZHALTER, laut Handbuch prüfen *)
    CW_FREIGABE    : WORD := 16#0001;
    CW_START       : WORD := 16#0002;
    CW_HALT        : WORD := 16#0004;
    CW_RESET       : WORD := 16#0100;
    (* Statuswort PE1 – PLATZHALTER, laut Handbuch prüfen *)
    SW_BEREIT      : WORD := 16#0001;
    SW_INPOS       : WORD := 16#0004;
    SW_FEHLER      : WORD := 16#0020;
END_VAR
VAR
    rtStart  : R_TRIG;
    dIst     : DINT;
    dZiel    : DINT;
    wStw     : WORD;
END_VAR

rtStart(CLK := xStart);

(* Istwerte *)
dIst := INT_TO_DINT(WORD_TO_INT(stPd.aPE[7])) * 65536 + WORD_TO_DINT(stPd.aPE[8]);   (* High-Wort mit Vorzeichen *)
rIst := DINT_TO_REAL(dIst) / EINHEIT_POS;
xBereit := (stPd.aPE[1] AND SW_BEREIT) <> 0;
xFehler := (stPd.aPE[1] AND SW_FEHLER) <> 0;
wFehler := stPd.aPE[3];

(* Sollwerte: bei neuem Ziel übernehmen *)
IF rtStart.Q THEN
    dZiel := REAL_TO_DINT(rZiel * EINHEIT_POS);
    stPd.aPA[2] := DINT_TO_WORD(LIMIT(1, REAL_TO_DINT(ABS(rV) * EINHEIT_V), 32767));
    stPd.aPA[3] := DINT_TO_WORD(LIMIT(1, REAL_TO_DINT(ABS(rA) * EINHEIT_A), 32767));
    stPd.aPA[4] := stPd.aPA[3];
    stPd.aPA[7] := DWORD_TO_WORD(SHR(DINT_TO_DWORD(dZiel), 16));
    stPd.aPA[8] := DWORD_TO_WORD(DINT_TO_DWORD(dZiel));
END_IF
stPd.aPA[6] := BETRIEBSART_ABS;

wStw := 0;
IF xEnable THEN wStw := wStw OR CW_FREIGABE; END_IF
IF xEnable AND xStart AND NOT xStop THEN wStw := wStw OR CW_START; END_IF
IF xStop THEN wStw := wStw OR CW_HALT; END_IF
IF xReset THEN wStw := wStw OR CW_RESET; END_IF
stPd.aPA[1] := wStw;

xInPos := ((stPd.aPE[1] AND SW_INPOS) <> 0) AND ABS(rIst - rZiel) <= GVL_Param.TOL_POS;
