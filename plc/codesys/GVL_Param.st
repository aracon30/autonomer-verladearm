(* Parameter Prototyp HETA. Werte aus vision/config/anlagen/heta_prototyp.yaml (drives, arm.joints)
   und docs/fuellstand_ueberfuellsicherung.md. Bei der Inbetriebnahme prüfen. *)
{attribute 'qualified_only'}
VAR_GLOBAL CONSTANT
    INTERFACE_VERSION : INT := 3;
    MAX_WP            : INT := 16;
    TIMEOUT_JOB       : TIME := T#5S;       (* Done muss innerhalb 5 s kommen *)
    TIMEOUT_HEARTBEAT : TIME := T#1S;
    TIMEOUT_MOVE_ADD  : TIME := T#10S;      (* Reserve zur berechneten Fahrzeit *)
    BERUHIGEN         : TIME := T#3S;       (* Auslass pendelt frei aus (J4) *)
    ABTROPFEN         : TIME := T#60S;      (* BASF: 1 min reicht oft nicht – mit Abtropfsicherung *)
    FAKTOR_LANGSAM    : REAL := 0.3;        (* Eintauchen, Herausfahren, Nachziehen *)
    FAKTOR_HAND       : REAL := 0.2;        (* Tippen *)
    TOL_POS           : REAL := 0.2;        (* ° Position erreicht *)
    TOL_PARK          : REAL := 0.5;        (* ° in Parkstellung *)
    MAX_KORREKTUR     : REAL := 50.0;       (* mm Job 2, darüber Abbruch *)
    ANFAHRHOEHE       : REAL := 0.3;        (* m über Domrand (arm.approach_height) *)
    NACHZIEH_SCHRITT  : REAL := 0.02;       (* m je Nachziehen, bis B wieder trocken *)
END_VAR
VAR_GLOBAL
    (* je Achse J1..J3: Höchstgeschwindigkeit [°/s], Beschleunigung [°/s²], Grenzen und Park [°] *)
    aVmax   : ARRAY[1..3] OF REAL := [6.0, 6.0, 5.93];
    aAmax   : ARRAY[1..3] OF REAL := [1.5, 3.0, 3.95];   (* = vmax / Rampe 4 / 2 / 1,5 s *)
    rRuckzeit : REAL := 0.3;                             (* s, auf allen Achsen gleich *)
    aMin    : ARRAY[1..3] OF REAL := [-120.0, -140.0, -45.0];
    aMax    : ARRAY[1..3] OF REAL := [120.0, 140.0, 45.0];
    aPark   : ARRAY[1..3] OF REAL := [70.0, -135.0, 10.0]; (* heta_prototyp.yaml, bei IBN anpassen *)
    (* Eintauchtiefe je Produkt [m unter Domrand], Index = ProductId 0..9 *)
    aEintauchtiefe : ARRAY[0..9] OF REAL := [0.4, 1.1, 0.75, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4];
    rMaxHoeheUnterRand : REAL := 0.28;   (* m: Füllende Ebene 2, knapp unter der Überfüllsicherung (ca. 0,2 m) *)
END_VAR
