# E2E Chatbot Performance Report

| Test Case | Description | Status | Latency (s) | Response Preview |
|---|---|---|---|---|
| Health Check | Verify API is up and running | ✅ 200 | 0.0013 | {"status":"ok","message":"Chatbot API running"} |
| SQL: Highest Population District | Aggregation/Sorting: Requires finding max value in districts table. | ✅ 200 | 13.6329 | {"response":"I’m unable to help with this at the moment, but I’d be happy to connect you with an admin for further assistance.","escalation_required":true,"escalation_id":"6c8e6bc9-6b14-49ec-a04d-b1f3 |
| SQL: Tourist Places in Pune | Filtering/Join: Requires filtering tourist_places by district name. | ✅ 200 | 10.9445 | {"response":"I’m unable to help with this at the moment, but I’d be happy to connect you with an admin for further assistance.","escalation_required":true,"escalation_id":"a729964f-ca81-4284-942d-5b7e |
| SQL: Total District Population | Aggregation: Summing a column across all rows. | ✅ 200 | 2.0875 | {"response":"I’m unable to help with this at the moment, but I’d be happy to connect you with an admin for further assistance.","escalation_required":true,"escalation_id":"2d9c4c56-dbe6-4acf-a575-7143 |
| SQL: Count Tourist Places | Aggregation: Counting rows in tourist_places table. | ✅ 200 | 1.9690 | {"response":"I’m unable to help with this at the moment, but I’d be happy to connect you with an admin for further assistance.","escalation_required":true,"escalation_id":"e417b86b-8563-4517-844e-e9e2 |
| SQL: Top 3 Largest Districts | Sorting/Limit: Ordering and limiting results. | ✅ 200 | 3.9708 | {"response":"I’m unable to help with this at the moment, but I’d be happy to connect you with an admin for further assistance.","escalation_required":true,"escalation_id":"9e67471d-fedd-4deb-9012-10f2 |
| SQL: Negative/Non-existent | Negative Case: Should handle missing data gracefully. | ✅ 200 | 1.8196 | {"response":"I’m unable to help with this at the moment, but I’d be happy to connect you with an admin for further assistance.","escalation_required":true,"escalation_id":"ab93f3c4-638d-453f-bfbc-0f84 |
| SQL: Complex Condition | Filtering/Sorting: Multiple conditions. | ✅ 200 | 18.3632 | {"response":"I’m unable to help with this at the moment, but I’d be happy to connect you with an admin for further assistance.","escalation_required":true,"escalation_id":"796163b8-325a-4df6-898d-b065 |
| Escalation: Crypto Price | Router Logic: Should route to escalation/general knowledge or fail safely. | ✅ 200 | 22.8215 | {"response":"I’m unable to help with this at the moment, but I’d be happy to connect you with an admin for further assistance.","escalation_required":true,"escalation_id":"bd7c1ac0-930a-493b-9c15-30de |
| Admin: List Active Escalations | Endpoint Verify: Admin route reachability. | ✅ 200 | 0.0026 | {"status":"ok","escalations":[],"count":0} |


## Summary
- **Total Tests**: 10
- **Passed**: 10
- **Failed**: 0
- **Avg Latency**: 7.5613s
- **Max Latency**: 22.8215s
