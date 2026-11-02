(* Heartbeat SPS -> PC alle 100 ms, Überwachung des PC-Heartbeats (Ausfall > 1 s). *)
PROGRAM PRG_Heartbeat
VAR
    tonTakt   : TON;
    tonPc     : TON;
    iLetzter  : INT;
END_VAR
VAR_OUTPUT
    xPcOk     : BOOL;     (* PC-Heartbeat läuft *)
END_VAR

tonTakt(IN := NOT tonTakt.Q, PT := T#100MS);
IF tonTakt.Q THEN
    IF GVL_Vision.HeartbeatPLC >= 32766 THEN
        GVL_Vision.HeartbeatPLC := 0;
    ELSE
        GVL_Vision.HeartbeatPLC := GVL_Vision.HeartbeatPLC + 1;
    END_IF
END_IF

tonPc(IN := GVL_Vision.HeartbeatPC = iLetzter, PT := GVL_Param.TIMEOUT_HEARTBEAT);
iLetzter := GVL_Vision.HeartbeatPC;
xPcOk := NOT tonPc.Q;
