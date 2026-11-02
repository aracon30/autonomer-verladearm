(* Schnittstelle Vision-PC <-> SPS, InterfaceVersion 3 (docs/schnittstelle.md).
   Gleiche Namen und Datentypen wie DB_Vision (plc/DB_Vision.db), damit der Vision-Dienst ohne
   Codeänderung verbindet. In der Symbolkonfiguration für OPC UA freigeben (Lesen/Schreiben). *)
{attribute 'qualified_only'}
VAR_GLOBAL
    (* SPS -> PC *)
    HeartbeatPLC   : INT;
    Trigger        : BOOL;
    Job            : INT;      (* 1 messen+planen, 2 nachmessen, 3 Rückfahrt, 0 nur messen *)
    ProductId      : INT;
    DomeNo         : INT;      (* 0 automatisch, n = n-ter offener Dom von vorn *)
    Reset          : BOOL;
    ActualJ1       : REAL;     (* Servo-Istwinkel [°] *)
    ActualJ2       : REAL;
    ActualJ3       : REAL;
    AxesHomed      : BOOL;
    ArmState       : INT;      (* 0 Park, 1 fährt, 2 über Dom, 3 eingetaucht, 9 Störung *)
    (* PC -> SPS *)
    HeartbeatPC    : INT;
    Ready          : BOOL;
    Busy           : BOOL;
    Done           : BOOL;
    Error          : BOOL;
    ErrorCode      : INT;
    ResultId       : DINT;
    TargetX        : REAL;     (* mm, Armbasis *)
    TargetY        : REAL;
    TargetZ        : REAL;
    NormalX        : REAL;
    NormalY        : REAL;
    NormalZ        : REAL;
    DiameterMm     : REAL;
    Confidence     : REAL;
    DomeCount      : INT;
    DomeSelected   : INT;
    WaypointCount  : INT;
    WaypointsJ1    : ARRAY[1..16] OF REAL;   (* Servo-Sollwinkel [°] *)
    WaypointsJ2    : ARRAY[1..16] OF REAL;
    WaypointsJ3    : ARRAY[1..16] OF REAL;
    ApproachIndex  : INT;      (* Stützpunkt "über dem Dom", 0 = keiner *)
    CorrectionX    : REAL;     (* mm, Job 2 *)
    CorrectionY    : REAL;
    InterfaceVersion : INT;
END_VAR
