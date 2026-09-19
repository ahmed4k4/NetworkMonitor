# Device Detail Page Rebuild Plan

## Goal
Rebuild ONLY `dashboard/app/devices/[id]/page.tsx` (route `/devices/{device_id}`) from real backend data contracts. No duplicate routes, no mock data.

## Data flow to trace & verify
Physical traffic → packet capture → Network Engine → PostgreSQL → FastAPI → dashboard/lib/api.ts → page

## Steps
1. Inspect frontend contracts: devices/page.tsx, lib/api.ts, lib/types.ts, hooks/useWebSocket.ts, components, design-system
2. Inspect backend routes: devices, traffic, analytics, applications, dns, flows, alerts, system/limits
3. Inspect DB schema probe for actual columns (traffic_samples, device_app_usage, etc.)
4. Build API client methods (api.ts) for each real endpoint
5. Build/verify TypeScript types from actual API responses
6. Rebuild page.tsx with sections (header, summary, live chart, history, apps, domains, categories, protocols, activity, peaks, flows, actions)
7. Apply Arabic RTL via existing design system
8. Run lint, tsc --noEmit, build
9. Verify with running API (devices list → dev_xxx detail)

## Non-negotiables
- No Math.random / hardcoded stats / fake devices
- All metrics trace to real DB rows
- Empty states instead of invented data
- useParams() for device id
- WebSocket updates scoped to current device only