# Architecture

```text
Enterprise Producers
        |
        v
Event Backbone (Kafka adapter optional in v1)
        |
        v
Derived State / DBSS
        |
        v
+---------------------------+
| STREAM-SURE Engine        |
| P_T temporal              |
| P_C contract              |
| P_L lineage               |
| P_F freshness/completeness|
| P_U uncertainty           |
| P_I invariant             |
| P_D decision policy       |
+-------------+-------------+
              |
              v
   SSAC: CERTIFIED / PROVISIONAL /
         WAIT / CORRECT / REJECT
              |
              v
 SQLite evidence + consumers + repair lineage
```

The core engine is provider-neutral. External stream runtimes map their runtime evidence into `DecisionBearingState` and `Evidence`.
