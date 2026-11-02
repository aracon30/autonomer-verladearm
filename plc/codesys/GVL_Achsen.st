(* Achsen J1..J3: Prozessdaten (im E/A-Abbild der drei MOVITRAC zuordnen), Fahrbefehle und
   Istwerte. Fahrbefehle schreibt immer nur ein Besitzer (Automatik oder Hand). *)
{attribute 'qualified_only'}
VAR_GLOBAL
    aPd        : ARRAY[1..3] OF ST_PdAxis;   (* E/A-Abbild MOVITRAC J1, J2, J3 *)
    (* Befehle *)
    aCmdZiel   : ARRAY[1..3] OF REAL;        (* ° *)
    aCmdV      : ARRAY[1..3] OF REAL;        (* °/s *)
    aCmdA      : ARRAY[1..3] OF REAL;        (* °/s² *)
    xCmdStart  : BOOL;                       (* Flanke = neues Ziel, halten während der Fahrt *)
    xCmdStop   : BOOL;
    xCmdReset  : BOOL;
    iBesitzer  : INT;                        (* 0 frei, 1 Automatik, 2 Hand *)
    (* Istwerte *)
    aIst       : ARRAY[1..3] OF REAL;        (* ° *)
    xAlleBereit: BOOL;
    xAlleInPos : BOOL;
    xAchsFehler: BOOL;
END_VAR
