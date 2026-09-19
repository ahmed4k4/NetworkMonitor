# Traffic Intelligence Subsystem - Implementation Plan

## Issues Identified

### 1. Double Counting Problem
- Current: A single flow's bytes are saved to `device_app_usage`, `device_domain_usage`, `device_category_usage`, `device_protocol_usage` 
- Result: Total bytes across these tables > actual traffic
- Fix: Ensure attribution is done once per flow, then distribute bytes across dimensions without duplication

### 2. Shared CDN Attribution
- Current: Cloudflare, Akamai, Fastly, AWS, Google Cloud, Azure treated as "applications"
- Problem: Traffic to `cloudfront.net` could be Netflix, Spotify, or any service using AWS CDN
- Fix: CDN IP ranges should return category="CDN/Infrastructure" with confidence=LOW, application="Unknown (CDN)" - NOT a specific application

### 3. Confidence Level Mismatch
- Backend: Uses "HIGH", "MEDIUM", "LOW"
- Frontend types: Uses "OBSERVED", "ESTIMATED", "UNKNOWN", "HIGH", "MEDIUM", "LOW"
- Fix: Standardize on backend terminology, add mapping for UI

### 4. Missing SNI in Flow Processing
- Parser extracts SNI but Flow model doesn't store it
- Fix: Add SNI to Flow model, store during packet processing

### 5. DNS-to-Flow Correlation
- Current: Only looks up DNS by destination IP (doesn't work for CDNs)
- Fix: Correlate by (device_id + destination_ip + time window), also use SNI when DNS unavailable

### 6. Incomplete Intelligence Saving
- Domain/category/protocol saves don't include confidence or evidence
- Fix: Add confidence and evidence to all intelligence tables

### 7. Frontend Device Detail Missing Intelligence UI
- Current device page only shows basic traffic, flows, DNS
- Fix: Add intelligence tabs with confidence indicators

## Implementation Steps

### Backend Changes

1. **Fix Attribution Engine** (`attribution.py`)
   - CDN IP ranges → category="CDN/Infrastructure", application="Unknown (CDN: Cloudflare)", confidence=LOW
   - Add CDN detection logic that doesn't attribute to specific apps
   - Standardize confidence: "HIGH", "MEDIUM", "LOW" only

2. **Update Flow Model** (`models/flow.py`)
   - Add `sni` field to Flow
   - Add `domain` field to Flow (resolved from DNS/SNI)

3. **Update Packet Processing** (`engine.py`)
   - Store SNI in flow when packet has it
   - Correlate DNS queries with flows using (device_id, destination_ip, time_window)

4. **Fix Intelligence Saving** (`database/repository.py`)
   - Add confidence, evidence to `save_domain_usage`, `save_category_usage`, `save_protocol_usage`
   - Ensure single flow bytes distributed correctly (not double-counted)

5. **Fix Device Intelligence Repository** (`database/repository.py`)
   - Update queries to include confidence for all dimensions
   - Fix `get_device_intelligence_summary` to not double-count

6. **Add Shared CDN Detection** (`attribution.py`)
   - Create `is_shared_cdn_ip()` and `is_shared_cdn_domain()` helpers
   - Return special attribution for CDN traffic

### Frontend Changes

1. **Fix Types** (`lib/types.ts`)
   - Standardize `ConfidenceLevel` to match backend: "HIGH" | "MEDIUM" | "LOW"
   - Add helper for UI display (Observed/Estimated/Unknown mapping)

2. **Create Intelligence Components** (`components/dashboard/`)
   - `ApplicationBreakdown.tsx` - with confidence badges
   - `DomainBreakdown.tsx` - with category and confidence
   - `CategoryBreakdown.tsx`
   - `ProtocolBreakdown.tsx`
   - `PeaksChart.tsx`
   - `ActivityTimeline.tsx`
   - `SNIObservations.tsx`

3. **Update Device Detail Page** (`app/devices/[id]/page.tsx`)
   - Add intelligence tabs
   - Show confidence indicators
   - Display "Shared CDN" warnings where appropriate

4. **Update API Client** (`lib/api.ts`)
   - Ensure all intelligence endpoints return correct types

## Testing Strategy
- Generate real traffic to test endpoints
- Verify totals: sum(applications) == sum(categories) == sum(protocols) == total traffic
- Verify CDN traffic shows as "Unknown (CDN: Cloudflare)" with LOW confidence
- Verify DNS/SNI attribution shows HIGH confidence