# modules/azure/event_hubs

Provisions the Event Hubs namespace, the `web-events` hub, and a dedicated consumer group used by `ingestion/streaming/` to simulate the ~1M-event synthetic web clickstream described in [ARCHITECTURE.md §4](../../../../ARCHITECTURE.md#4-layer-1--sources--ingestion) as a real streaming source rather than a batch file, demonstrating distributed/streaming ingestion alongside ADF's batch path.

Built in **Sprint 1** ([ROADMAP.md](../../../../ROADMAP.md)).
