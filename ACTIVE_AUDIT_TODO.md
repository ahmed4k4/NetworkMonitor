# Data Contract Fix Task List

- [x] Trace full pipeline (capture -> engine -> flow -> DB -> API -> WS -> frontend)
- [x] Confirm live API shows download_today=0 / upload_today>0 (direction inversion)
- [x] Identify root cause: upstream_gateway (192.168.137.2) treated as LAN -> all traffic LOCAL
- [x] Identify SNI contract mismatch (backend sni/destination_ip/destination_port vs frontend sni_hostname/dest_ip/dest_port)
- [x] Identify precedence bug in _attribute_and_save_flow domain resolution (line 673)
- [ ] Fix direction classification: gateway-aware _is_local so monitor<->gateway = internet traffic
- [ ] Pass upstream_gateway into FlowManager and engine direction checks
- [ ] Fix domain precedence bug in engine._attribute_and_save_flow
- [ ] Fix SNI TypeScript type mismatch in dashboard/lib/types.ts
- [ ] Run python compile checks
- [ ] Run tsc --noEmit
- [ ] Run frontend build
- [ ] Verify API endpoints
- [ ] Report files changed, problems, fixes, tests, remaining issues