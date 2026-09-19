# COMPLETE API CONTRACT AUDIT
# ============================

# BACKEND ENDPOINTS (from FastAPI routers)
backend_endpoints = {
    # Authentication
    'POST /api/auth/login': {'file': 'auth.py', 'auth': 'public'},
    
    # Devices
    'GET /api/devices/': {'file': 'devices.py', 'auth': 'user', 'func': 'get_devices'},
    'GET /api/devices/{device_id}': {'file': 'devices.py', 'auth': 'user', 'func': 'get_device'},
    'GET /api/devices/mac/{mac_address}': {'file': 'devices.py', 'auth': 'user', 'func': 'get_device_by_mac'},
    'POST /api/devices/{device_id}/block': {'file': 'devices.py', 'auth': 'admin/operator', 'func': 'block_device'},
    'POST /api/devices/{device_id}/unblock': {'file': 'devices.py', 'auth': 'admin/operator', 'func': 'unblock_device'},
    'POST /api/devices/{device_id}/limit': {'file': 'devices.py', 'auth': 'admin/operator', 'func': 'limit_device'},
    'POST /api/devices/{device_id}/quota': {'file': 'devices.py', 'auth': 'admin/operator', 'func': 'quota_device'},
    'POST /api/devices/{device_id}/name': {'file': 'devices.py', 'auth': 'admin/operator', 'func': 'rename_device'},
    'POST /api/devices/{device_id}/pause': {'file': 'devices.py', 'auth': 'admin/operator', 'func': 'pause_device'},
    'POST /api/devices/{device_id}/resume': {'file': 'devices.py', 'auth': 'admin/operator', 'func': 'resume_device'},
    # NEW INTELLIGENCE ENDPOINTS
    'GET /api/devices/{device_id}/intelligence': {'file': 'devices.py', 'auth': 'user', 'func': 'get_device_intelligence'},
    'GET /api/devices/{device_id}/applications': {'file': 'devices.py', 'auth': 'user', 'func': 'get_device_applications'},
    'GET /api/devices/{device_id}/domains': {'file': 'devices.py', 'auth': 'user', 'func': 'get_device_domains'},
    'GET /api/devices/{device_id}/categories': {'file': 'devices.py', 'auth': 'user', 'func': 'get_device_categories'},
    'GET /api/devices/{device_id}/protocols': {'file': 'devices.py', 'auth': 'user', 'func': 'get_device_protocols'},
    'GET /api/devices/{device_id}/peaks': {'file': 'devices.py', 'auth': 'user', 'func': 'get_device_peaks'},
    'GET /api/devices/{device_id}/activity': {'file': 'devices.py', 'auth': 'user', 'func': 'get_device_activity'},
    'GET /api/devices/{device_id}/sni': {'file': 'devices.py', 'auth': 'user', 'func': 'get_device_sni'},
    
    # Traffic
    'GET /api/traffic/recent': {'file': 'traffic.py', 'auth': 'user', 'func': 'recent_traffic'},
    'GET /api/traffic/history': {'file': 'traffic.py', 'auth': 'user', 'func': 'traffic_history'},
    
    # Flows
    'GET /api/flows/active': {'file': 'flows.py', 'auth': 'none', 'func': 'active_flows'},
    
    # DNS
    'GET /api/dns/recent': {'file': 'dns.py', 'auth': 'none', 'func': 'recent_dns'},
    
    # Applications
    'GET /api/applications/': {'file': 'applications.py', 'auth': 'user', 'func': 'get_applications'},
    
    # Analytics
    'GET /api/analytics/top-devices': {'file': 'analytics.py', 'auth': 'user', 'func': 'top_devices'},
    'GET /api/analytics/hourly': {'file': 'analytics.py', 'auth': 'user', 'func': 'hourly_analytics'},
    'GET /api/analytics/daily': {'file': 'analytics.py', 'auth': 'user', 'func': 'daily_analytics'},
    'GET /api/analytics/weekly': {'file': 'analytics.py', 'auth': 'user', 'func': 'weekly_analytics'},
    'GET /api/analytics/monthly': {'file': 'analytics.py', 'auth': 'user', 'func': 'monthly_analytics'},
    'GET /api/analytics/protocols': {'file': 'analytics.py', 'auth': 'user', 'func': 'protocol_analytics'},
    'GET /api/analytics/domains': {'file': 'analytics.py', 'auth': 'user', 'func': 'domain_analytics'},
    'GET /api/analytics/applications': {'file': 'analytics.py', 'auth': 'user', 'func': 'application_analytics'},
    
    # Control
    'GET /api/control/rules': {'file': 'control.py', 'auth': 'user', 'func': 'get_rules'},
    'POST /api/control/rules': {'file': 'control.py', 'auth': 'user', 'func': 'create_rule'},
    'PUT /api/control/rules/{rule_id}': {'file': 'control.py', 'auth': 'user', 'func': 'update_rule'},
    'DELETE /api/control/rules/{rule_id}': {'file': 'control.py', 'auth': 'user', 'func': 'delete_rule'},
    'GET /api/control/limits': {'file': 'control.py', 'auth': 'user', 'func': 'get_limits'},
    'POST /api/control/limits': {'file': 'control.py', 'auth': 'user', 'func': 'create_limit'},
    'PUT /api/control/limits/{limit_id}': {'file': 'control.py', 'auth': 'user', 'func': 'update_limit'},
    'DELETE /api/control/limits/{limit_id}': {'file': 'control.py', 'auth': 'user', 'func': 'delete_limit'},
    'GET /api/control/firewall': {'file': 'control.py', 'auth': 'user', 'func': 'get_firewall'},
    'POST /api/control/firewall': {'file': 'control.py', 'auth': 'user', 'func': 'create_firewall_rule'},
    'PUT /api/control/firewall/{rule_id}': {'file': 'control.py', 'auth': 'user', 'func': 'update_firewall_rule'},
    'DELETE /api/control/firewall/{rule_id}': {'file': 'control.py', 'auth': 'user', 'func': 'delete_firewall_rule'},
    'GET /api/control/quotas': {'file': 'control.py', 'auth': 'user', 'func': 'get_quotas'},
    'POST /api/control/quotas': {'file': 'control.py', 'auth': 'user', 'func': 'create_quota'},
    'PUT /api/control/quotas/{quota_id}': {'file': 'control.py', 'auth': 'user', 'func': 'update_quota'},
    'DELETE /api/control/quotas/{quota_id}': {'file': 'control.py', 'auth': 'user', 'func': 'delete_quota'},
    
    # Alerts
    'GET /api/alerts/': {'file': 'alerts.py', 'auth': 'user', 'func': 'get_alerts'},
    
    # Reports
    'GET /api/reports/': {'file': 'reports.py', 'auth': 'user', 'func': 'get_reports'},
    'POST /api/reports/generate': {'file': 'reports.py', 'auth': 'user', 'func': 'generate_report'},
    
    # System
    'GET /api/system/status': {'file': 'system.py', 'auth': 'user', 'func': 'get_system_status'},
    'GET /api/system/interfaces': {'file': 'system.py', 'auth': 'user', 'func': 'get_interfaces'},
    'GET /api/system/settings': {'file': 'system.py', 'auth': 'user', 'func': 'get_settings'},
    'PUT /api/system/settings': {'file': 'system.py', 'auth': 'user', 'func': 'update_settings'},
    'POST /api/system/broadcast': {'file': 'system.py', 'auth': 'internal', 'func': 'broadcast'},
    
    # Health
    'GET /api/health': {'file': 'app.py', 'auth': 'public', 'func': 'health'},
}

# FRONTEND API CALLS (from updated api.ts)
frontend_calls = {
    'api.login(username, password)': 'POST /api/auth/login',
    'api.getHealth()': 'GET /api/health',
    'api.getSystemStatus()': 'GET /api/system/status',
    'api.getDevices()': 'GET /api/devices/',
    'api.getDevice(id)': 'GET /api/devices/{device_id}',
    'api.getDeviceByMac(mac)': 'GET /api/devices/mac/{mac_address}',
    'api.blockDevice(deviceId, ip)': 'POST /api/devices/{device_id}/block?ip=...',
    'api.unblockDevice(deviceId)': 'POST /api/devices/{device_id}/unblock',
    'api.limitDevice(deviceId, downloadLimit, uploadLimit, enabled)': 'POST /api/devices/{device_id}/limit',
    'api.setDeviceQuota(deviceId, quotaBytes, dailyQuotaMb, weeklyQuotaMb, monthlyQuotaMb, enabled)': 'POST /api/devices/{device_id}/quota',
    'api.renameDevice(deviceId, name)': 'POST /api/devices/{device_id}/name',
    'api.pauseDevice(deviceId, ip)': 'POST /api/devices/{device_id}/pause',
    'api.resumeDevice(deviceId)': 'POST /api/devices/{device_id}/resume',
    'api.getTraffic()': 'GET /api/traffic/recent',
    'api.getDeviceTraffic(deviceId)': 'GET /api/traffic/recent?device_id=...',
    'api.getFlows()': 'GET /api/flows/active',
    'api.getDNS()': 'GET /api/dns/recent',
    'api.getDomains()': 'GET /api/dns/recent',
    'api.getApplications()': 'GET /api/applications/',
    'api.getApplicationAnalytics()': 'GET /api/analytics/applications',
    'api.getTopDevices()': 'GET /api/analytics/top-devices',
    'api.getAnalytics(timeRange)': 'GET /api/analytics/{hourly|daily|weekly|monthly}',
    'api.getProtocols()': 'GET /api/analytics/protocols',
    'api.getDomainAnalytics()': 'GET /api/analytics/domains',
    'api.getRules()': 'GET /api/control/rules',
    'api.createRule(rule)': 'POST /api/control/rules',
    'api.updateRule(ruleId, rule)': 'PUT /api/control/rules/{rule_id}',
    'api.deleteRule(ruleId)': 'DELETE /api/control/rules/{rule_id}',
    'api.getLimits()': 'GET /api/control/limits',
    'api.createLimit(limit)': 'POST /api/control/limits',
    'api.updateLimit(limitId, limit)': 'PUT /api/control/limits/{limit_id}',
    'api.deleteLimit(limitId)': 'DELETE /api/control/limits/{limit_id}',
    'api.getFirewall()': 'GET /api/control/firewall',
    'api.createFirewallRule(rule)': 'POST /api/control/firewall',
    'api.updateFirewallRule(ruleId, rule)': 'PUT /api/control/firewall/{rule_id}',
    'api.deleteFirewallRule(ruleId)': 'DELETE /api/control/firewall/{rule_id}',
    'api.getQuotas()': 'GET /api/control/quotas',
    'api.createQuota(quota)': 'POST /api/control/quotas',
    'api.updateQuota(quotaId, quota)': 'PUT /api/control/quotas/{quota_id}',
    'api.deleteQuota(quotaId)': 'DELETE /api/control/quotas/{quota_id}',
    'api.getAlerts()': 'GET /api/alerts/',
    'api.getReports()': 'GET /api/reports/',
    'api.generateReport(params)': 'POST /api/reports/generate',
    'api.getInterfaces()': 'GET /api/system/interfaces',
    'api.getSettings()': 'GET /api/system/settings',
    'api.updateSettings(settings)': 'PUT /api/system/settings',
    # NEW INTELLIGENCE API CALLS
    'api.getDeviceIntelligence(deviceId, range, start, end)': 'GET /api/devices/{device_id}/intelligence',
    'api.getDeviceApplications(deviceId, range, start, end)': 'GET /api/devices/{device_id}/applications',
    'api.getDeviceDomains(deviceId, range, start, end, limit)': 'GET /api/devices/{device_id}/domains',
    'api.getDeviceCategories(deviceId, range, start, end)': 'GET /api/devices/{device_id}/categories',
    'api.getDeviceProtocols(deviceId, range, start, end)': 'GET /api/devices/{device_id}/protocols',
    'api.getDevicePeaks(deviceId, days)': 'GET /api/devices/{device_id}/peaks',
    'api.getDeviceActivity(deviceId, days)': 'GET /api/devices/{device_id}/activity',
    'api.getDeviceSNI(deviceId, range, start, end)': 'GET /api/devices/{device_id}/sni',
}

print('=' * 100)
print('API CONTRACT AUDIT REPORT')
print('=' * 100)

# Check each frontend call against backend
print()
print('1. FRONTEND -> BACKEND MAPPING VERIFICATION')
print('-' * 100)

all_ok = True
for fe_call, be_endpoint in frontend_calls.items():
    # Normalize endpoint for comparison (replace {id} with {device_id} etc)
    normalized = be_endpoint.replace('{id}', '{device_id}').replace('{mac}', '{mac_address}')
    # Handle query param variants
    base_endpoint = normalized.split('?')[0]
    
    # Check if the base endpoint exists in backend
    found = False
    for backend_ep in backend_endpoints:
        if base_endpoint == backend_ep.split('?')[0]:
            found = True
            info = backend_endpoints[backend_ep]
            print('  OK {:<60} -> {} [{}]'.format(fe_call, backend_ep, info['auth']))
            break
    
    if not found:
        print('  MISSING: {:<60} -> {} (NOT FOUND IN BACKEND)'.format(fe_call, be_endpoint))
        all_ok = False

# Check for backend endpoints not used by frontend
print()
print('2. BACKEND ENDPOINTS NOT USED BY FRONTEND')
print('-' * 100)
used_endpoints = set()
for be_endpoint in frontend_calls.values():
    base = be_endpoint.split('?')[0].replace('{id}', '{device_id}').replace('{mac}', '{mac_address}')
    used_endpoints.add(base)

for be_endpoint in backend_endpoints:
    base = be_endpoint.split('?')[0]
    if base not in used_endpoints:
        info = backend_endpoints[be_endpoint]
        print('  UNUSED: {} [{}] in {}'.format(be_endpoint, info['auth'], info['file']))

# Check intelligence endpoints specifically
print()
print('3. NEW INTELLIGENCE ENDPOINTS - FRONTEND INTEGRATION CHECK')
print('-' * 100)
intel_endpoints = [
    'GET /api/devices/{device_id}/intelligence',
    'GET /api/devices/{device_id}/applications',
    'GET /api/devices/{device_id}/domains',
    'GET /api/devices/{device_id}/categories',
    'GET /api/devices/{device_id}/protocols',
    'GET /api/devices/{device_id}/peaks',
    'GET /api/devices/{device_id}/activity',
    'GET /api/devices/{device_id}/sni',
]
for ep in intel_endpoints:
    if ep in used_endpoints:
        print('  USED: {}'.format(ep))
    else:
        print('  NOT INTEGRATED: {}'.format(ep))

print()
print('=' * 100)
print('AUDIT COMPLETE')
print('=' * 100)