"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  Activity, AlertTriangle, AppWindow, ArrowLeft, BarChart2, Calendar, Clock, Database, Download, Edit2, Gauge, Globe, HardDrive, Layers, LayoutGrid, Link2, Loader2, Lock, Network, RefreshCw, Server, Settings, Shield, Tag, Trash2, Unlock, Upload, Wifi, Wrench, Zap,
} from "lucide-react";
import { Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { MetricCard, StatusBadge } from "@/components/design-system";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useToast } from "@/components/ui/toast";
import { api, isAuthenticated } from "@/lib/api";
import { useWebSocket } from "@/hooks/useWebSocket";
import type { Device, DeviceActivity, DeviceApplication, DeviceCategory, DeviceDomain, DevicePeak, DeviceProtocol, Flow, TrafficHistoryEntry, TrafficSample, WebSocketMessage, ControlRule, FirewallRule, Quota } from "@/lib/types";

type ExtendedControlRule = ControlRule & { device_id?: string; target?: string };
type ExtendedQuota = Quota & { action?: string };
type ExtendedFirewallRule = FirewallRule & { device_id?: string };

function formatBytes(bytes: number | null | undefined): string { const value = Number(bytes ?? 0); if (!value || value <= 0) return "0 B"; const k = 1024; const sizes = ["B", "KB", "MB", "GB", "TB"]; const i = Math.min(Math.floor(Math.log(value) / Math.log(k)), sizes.length - 1); return `${parseFloat((value / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`; }
function formatSpeed(bps: number | null | undefined): string { const value = Number(bps ?? 0); if (!value || value <= 0) return "0 bps"; if (value >= 1_000_000_000) return `${(value / 1_000_000_000).toFixed(2)} Gbps`; if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(2)} Mbps`; if (value >= 1_000) return `${(value / 1_000).toFixed(2)} Kbps`; return `${value} bps`; }
function formatDate(dateString?: string | null): string { if (!dateString) return "Never"; try { return new Date(dateString).toLocaleString(); } catch { return dateString; } }
function formatTime(dateString?: string | null): string { if (!dateString) return "—"; try { return new Date(dateString).toLocaleTimeString(); } catch { return dateString; } }
function formatKBpsToBps(kbps: number): number { return Math.round(kbps * 1024 * 8); }

export default function DeviceDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const { addToast } = useToast();
  const deviceId = params?.id ?? "";

  const [activeTab, setActiveTab] = useState("overview");

  const [device, setDevice] = useState<Device | null>(null);
  const [deviceLoading, setDeviceLoading] = useState(true);
  const [deviceError, setDeviceError] = useState<string | null>(null);

  const [liveSamples, setLiveSamples] = useState<TrafficSample[]>([]);
  const [liveLoading, setLiveLoading] = useState(true);
  const [liveError, setLiveError] = useState<string | null>(null);

  const [history, setHistory] = useState<TrafficHistoryEntry[]>([]);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [historyDays, setHistoryDays] = useState(7);

  const [apps, setApps] = useState<DeviceApplication[]>([]);
  const [appsLoading, setAppsLoading] = useState(true);
  const [appsError, setAppsError] = useState<string | null>(null);
  const [domains, setDomains] = useState<DeviceDomain[]>([]);
  const [domainsLoading, setDomainsLoading] = useState(true);
  const [domainsError, setDomainsError] = useState<string | null>(null);
  const [categories, setCategories] = useState<DeviceCategory[]>([]);
  const [categoriesLoading, setCategoriesLoading] = useState(true);
  const [categoriesError, setCategoriesError] = useState<string | null>(null);
  const [protocols, setProtocols] = useState<DeviceProtocol[]>([]);
  const [protocolsLoading, setProtocolsLoading] = useState(true);
  const [protocolsError, setProtocolsError] = useState<string | null>(null);

  const [activity, setActivity] = useState<DeviceActivity[]>([]);
  const [activityLoading, setActivityLoading] = useState(true);
  const [activityError, setActivityError] = useState<string | null>(null);
  const [peaks, setPeaks] = useState<DevicePeak[]>([]);
  const [peaksLoading, setPeaksLoading] = useState(true);
  const [peaksError, setPeaksError] = useState<string | null>(null);

  const [flows, setFlows] = useState<Flow[]>([]);
  const [flowsLoading, setFlowsLoading] = useState(true);
  const [flowsError, setFlowsError] = useState<string | null>(null);

  const [intelRange, setIntelRange] = useState("24h");

  const [renameOpen, setRenameOpen] = useState(false);
  const [renameValue, setRenameValue] = useState("");
  const [renaming, setRenaming] = useState(false);

  const [blocking, setBlocking] = useState(false);
  const [blockOpenConfirm, setBlockOpenConfirm] = useState(false);

  const [limitOpen, setLimitOpen] = useState(false);
  const [limitLoading, setLimitLoading] = useState(false);
  const [limitDownload, setLimitDownload] = useState("");
  const [limitUpload, setLimitUpload] = useState("");
  const [limitUnit, setLimitUnit] = useState<"kbps" | "mbps">("mbps");
  const [limitEnabled, setLimitEnabled] = useState(true);

  const [quotaOpen, setQuotaOpen] = useState(false);
  const [quotaLoading, setQuotaLoading] = useState(false);
  const [quotaDaily, setQuotaDaily] = useState("");
  const [quotaWeekly, setQuotaWeekly] = useState("");
  const [quotaMonthly, setQuotaMonthly] = useState("");
  const [quotaUnit, setQuotaUnit] = useState<"mb" | "gb">("gb");
  const [quotaEnabled, setQuotaEnabled] = useState(true);
  const [quotaResetPeriod, setQuotaResetPeriod] = useState<"DAILY" | "WEEKLY" | "MONTHLY">("DAILY");
  const [quotaAction, setQuotaAction] = useState<"ALERT" | "BLOCK" | "THROTTLE">("ALERT");

  const [rulesOpen, setRulesOpen] = useState(false);
  const [rules, setRules] = useState<ExtendedControlRule[]>([]);
  const [rulesLoading, setRulesLoading] = useState(false);
  const [newRule, setNewRule] = useState({ domain: "", action: "BLOCK" as "ALLOW" | "BLOCK", enabled: true });
  const [creatingRule, setCreatingRule] = useState(false);
  const [editingRuleId, setEditingRuleId] = useState<string | null>(null);
  const [editedRule, setEditedRule] = useState({ domain: "", action: "BLOCK" as "ALLOW" | "BLOCK", enabled: true });

  const [scheduleOpen, setScheduleOpen] = useState(false);
  const [schedules, setSchedules] = useState<ExtendedControlRule[]>([]);
  const [schedulesLoading, setSchedulesLoading] = useState(false);
  const [newSchedule, setNewSchedule] = useState({
    name: "", domain: "", action: "BLOCK" as "ALLOW" | "BLOCK",
    days: [1,2,3,4,5,6,0] as number[], startTime: "22:00", endTime: "07:00", enabled: true,
  });
  const [creatingSchedule, setCreatingSchedule] = useState(false);

  const [unblocking, setUnblocking] = useState(false);

  const handleWsMessage = useCallback((message: unknown) => {
    const msg = message as WebSocketMessage;
    if (!msg?.type || !msg?.data) return;
    if (msg.type === "traffic_update") {
      const data = msg.data as { device_id: string; download_speed_bps?: number; upload_speed_bps?: number; download_today?: number; upload_today?: number; total_today?: number; download?: number; upload?: number; packets?: number; connections?: number; timestamp?: string };
      if (data.device_id !== deviceId) return;
      setDevice((prev) => prev ? { ...prev, download_speed_bps: data.download_speed_bps ?? prev.download_speed_bps, upload_speed_bps: data.upload_speed_bps ?? prev.upload_speed_bps, current_speed_bps: ((data.download_speed_bps ?? 0) + (data.upload_speed_bps ?? 0)) || prev.current_speed_bps, download_today: data.download_today ?? prev.download_today, upload_today: data.upload_today ?? prev.upload_today, total_today: data.total_today ?? prev.total_today, last_seen: data.timestamp ?? prev.last_seen } : prev);
      setLiveSamples((prev) => { const next = [...prev]; next.push({ device_id: data.device_id, ip: "", time: data.timestamp ?? new Date().toISOString(), download: data.download ?? 0, upload: data.upload ?? 0, packets: data.packets ?? 0, connections: data.connections ?? 0, download_speed_bps: data.download_speed_bps ?? 0, upload_speed_bps: data.upload_speed_bps ?? 0 }); return next.slice(-100); });
    }
    if (msg.type === "device_online" || msg.type === "device_offline") {
      const data = msg.data as { device_id: string; ip?: string };
      if (data.device_id !== deviceId) return;
      setDevice((prev) => prev ? { ...prev, state: msg.type === "device_online" ? "ONLINE" : "OFFLINE", ip: data.ip || prev.ip } : prev);
    }
  }, [deviceId]);

  const ws = useWebSocket(handleWsMessage);
  const wsStatus = ws;

  const loadDevice = useCallback(async () => { if (!deviceId) return; setDeviceLoading(true); setDeviceError(null); try { const data = await api.getDevice(deviceId); setDevice(data); } catch (err) { console.error("[DeviceDetail] Failed to load device:", err); setDeviceError(err instanceof Error ? err.message : "Failed to load device"); } finally { setDeviceLoading(false); } }, [deviceId]);
  const loadLiveTraffic = useCallback(async () => { if (!deviceId) return; setLiveLoading(true); setLiveError(null); try { const data = await api.getDeviceTraffic(deviceId); setLiveSamples(Array.isArray(data) ? data : []); } catch (err) { console.error("[DeviceDetail] Failed to load live traffic:", err); setLiveError(err instanceof Error ? err.message : "Failed to load live traffic"); } finally { setLiveLoading(false); } }, [deviceId]);
  const loadHistory = useCallback(async () => { if (!deviceId) return; setHistoryLoading(true); setHistoryError(null); try { const data = await api.getDeviceTrafficHistory(deviceId, historyDays); setHistory(Array.isArray(data) ? data : []); } catch (err) { console.error("[DeviceDetail] Failed to load history:", err); setHistoryError(err instanceof Error ? err.message : "Failed to load history"); } finally { setHistoryLoading(false); } }, [deviceId, historyDays]);
  const loadIntel = useCallback(async () => { if (!deviceId) return; setAppsLoading(true); setDomainsLoading(true); setCategoriesLoading(true); setProtocolsLoading(true); setActivityLoading(true); setPeaksLoading(true); setAppsError(null); setDomainsError(null); setCategoriesError(null); setProtocolsError(null); setActivityError(null); setPeaksError(null); const [appsRes, domainsRes, catsRes, protosRes, actRes, peaksRes] = await Promise.allSettled([ api.getDeviceApplications(deviceId, intelRange), api.getDeviceDomains(deviceId, intelRange, undefined, undefined, 50), api.getDeviceCategories(deviceId, intelRange), api.getDeviceProtocols(deviceId, intelRange), api.getDeviceActivity(deviceId, 7), api.getDevicePeaks(deviceId, 30) ]); if (appsRes.status === "fulfilled") setApps(appsRes.value); else { setApps([]); setAppsError("Unable to load application data."); } if (domainsRes.status === "fulfilled") setDomains(domainsRes.value); else { setDomains([]); setDomainsError("Unable to load domain data."); } if (catsRes.status === "fulfilled") setCategories(catsRes.value); else { setCategories([]); setCategoriesError("Unable to load category data."); } if (protosRes.status === "fulfilled") setProtocols(protosRes.value); else { setProtocols([]); setProtocolsError("Unable to load protocol data."); } if (actRes.status === "fulfilled") setActivity(actRes.value); else { setActivity([]); setActivityError("Unable to load activity data."); } if (peaksRes.status === "fulfilled") setPeaks(peaksRes.value); else { setPeaks([]); setPeaksError("Unable to load peak data."); } setAppsLoading(false); setDomainsLoading(false); setCategoriesLoading(false); setProtocolsLoading(false); setActivityLoading(false); setPeaksLoading(false); }, [deviceId, intelRange]);
  const loadFlows = useCallback(async () => { if (!deviceId) return; setFlowsLoading(true); setFlowsError(null); try { const data = await api.getDeviceFlows(deviceId); setFlows(Array.isArray(data) ? data : []); } catch (err) { console.error("[DeviceDetail] Failed to load flows:", err); setFlows([]); setFlowsError("Unable to load connection data."); } finally { setFlowsLoading(false); } }, [deviceId]);
  const loadRules = useCallback(async () => { if (!deviceId) return; setRulesLoading(true); try { const data = await api.getRules(); const deviceRules = data.filter(r => r.device_id === deviceId || r.target === deviceId); setRules(deviceRules as ExtendedControlRule[]); } catch (err) { console.error("[DeviceDetail] Failed to load rules:", err); setRules([]); } finally { setRulesLoading(false); } }, [deviceId]);
  const loadLimits = useCallback(async () => { if (!deviceId) return; try { const data = await api.getLimits(); const deviceLimits = data.filter(l => l.device_id === deviceId); if (deviceLimits.length > 0) { const lim = deviceLimits[0]; setLimitDownload(lim.download_limit?.toString() || ""); setLimitUpload(lim.upload_limit?.toString() || ""); setLimitEnabled(lim.enabled ?? true); } } catch (err) { console.error("[DeviceDetail] Failed to load limits:", err); } }, [deviceId]);
  const loadQuotas = useCallback(async () => { if (!deviceId) return; try { const data = await api.getQuotas(); const deviceQuotas = data.filter(q => q.device_id === deviceId); if (deviceQuotas.length > 0) { const q = deviceQuotas[0] as ExtendedQuota; if (q.daily_quota_mb) setQuotaDaily(q.daily_quota_mb.toString()); if (q.weekly_quota_mb) setQuotaWeekly(q.weekly_quota_mb.toString()); if (q.monthly_quota_mb) setQuotaMonthly(q.monthly_quota_mb.toString()); setQuotaEnabled(q.enabled ?? true); setQuotaResetPeriod(q.reset_period as "DAILY" | "WEEKLY" | "MONTHLY" || "DAILY"); setQuotaAction(q.action as "ALERT" | "BLOCK" | "THROTTLE" || "ALERT"); } } catch (err) { console.error("[DeviceDetail] Failed to load quotas:", err); } }, [deviceId]);
  const loadFirewallRules = useCallback(async () => { if (!deviceId) return; try { const data = await api.getFirewall(); const deviceRules = data.filter(r => (r as ExtendedFirewallRule).device_id === deviceId); setSchedules(deviceRules as ExtendedControlRule[]); } catch (err) { console.error("[DeviceDetail] Failed to load firewall rules:", err); } }, [deviceId]);

  useEffect(() => { if (!isAuthenticated()) { router.push("/login"); return; } if (!deviceId) return; const timer = setTimeout(() => { loadDevice(); loadLiveTraffic(); loadHistory(); loadIntel(); loadFlows(); loadRules(); loadLimits(); loadQuotas(); loadFirewallRules(); }, 0); return () => clearTimeout(timer); }, [deviceId, router, loadDevice, loadLiveTraffic, loadHistory, loadIntel, loadFlows, loadRules, loadLimits, loadQuotas, loadFirewallRules]);

  const liveChartData = useMemo(() => liveSamples.slice().sort((a, b) => new Date(a.time).getTime() - new Date(b.time).getTime()).map((s) => ({ time: formatTime(s.time), download: Number(s.download_speed_bps ?? 0) / 1_000_000, upload: Number(s.upload_speed_bps ?? 0) / 1_000_000 })), [liveSamples]);
  const historyChartData = useMemo(() => history.map((h) => ({ date: h.date, download: Number(h.download ?? 0) / (1024 * 1024), upload: Number(h.upload ?? 0) / (1024 * 1024), total: Number(h.total ?? 0) / (1024 * 1024) })), [history]);
  const appChartData = useMemo(() => { const max = Math.max(1, ...apps.map((a) => Number(a.total_bytes ?? 0))); return apps.map((a) => ({ name: a.name, total: Number(a.total_bytes ?? 0), pct: (Number(a.total_bytes ?? 0) / max) * 100 })); }, [apps]);
  const domainChartData = useMemo(() => { const max = Math.max(1, ...domains.map((d) => Number(d.total_bytes ?? 0))); return domains.slice(0, 10).map((d) => ({ name: d.domain, total: Number(d.total_bytes ?? 0), pct: (Number(d.total_bytes ?? 0) / max) * 100 })); }, [domains]);
  const categoryPieData = useMemo(() => categories.map((c) => ({ name: c.category, value: Number(c.total_bytes ?? 0) })), [categories]);
  const protocolChartData = useMemo(() => { const max = Math.max(1, ...protocols.map((p) => Number(p.total_bytes ?? 0))); return protocols.map((p) => ({ name: p.protocol, total: Number(p.total_bytes ?? 0), pct: (Number(p.total_bytes ?? 0) / max) * 100 })); }, [protocols]);
  const activityData = useMemo(() => activity.slice().sort((a, b) => new Date(a.hour_start).getTime() - new Date(b.hour_start).getTime()).map((a) => ({ time: formatTime(a.hour_start), bytes: Number(a.total_bytes ?? 0), active: Boolean(a.is_active) })), [activity]);
  const peakSummary = useMemo(() => { const byType: Record<string, DevicePeak[]> = {}; for (const p of peaks) { if (!byType[p.peak_type]) byType[p.peak_type] = []; byType[p.peak_type].push(p); } const pick = (type: string) => { const list = byType[type] || []; if (list.length === 0) return null; return list.reduce((a, b) => (Number(b.peak_value) > Number(a.peak_value) ? b : a)); }; return { download: pick("download_speed"), upload: pick("upload_speed"), total: pick("total_speed"), connections: pick("connections") }; }, [peaks]);
  const deviceFlows = useMemo(() => flows.filter((f) => f.device_id === deviceId), [flows, deviceId]);
  const totalDownload = Number(device?.download_today ?? device?.download ?? 0);
  const totalUpload = Number(device?.upload_today ?? device?.upload ?? 0);
  const totalTraffic = totalDownload + totalUpload;
  const currentSpeed = Number(device?.current_speed_bps ?? 0);
  const totalPackets = liveSamples.reduce((sum, s) => sum + Number(s.packets ?? 0), 0);
  const flowCount = deviceFlows.length;
  const quotaUsed = device?.quota_used_bytes ?? 0;
  const quotaTotal = device?.quota_bytes ?? 0;
  const quotaRemaining = Math.max(0, quotaTotal - quotaUsed);
  const quotaPct = quotaTotal > 0 ? Math.round((quotaUsed / quotaTotal) * 100) : 0;

  const handleRename = async () => { if (!deviceId || !renameValue.trim() || renaming) return; setRenaming(true); try { await api.renameDevice(deviceId, renameValue.trim()); setDevice((prev) => prev ? { ...prev, custom_name: renameValue.trim() } : prev); setRenameOpen(false); addToast("Device renamed successfully", { variant: "success" }); } catch (err) { console.error("[DeviceDetail] Rename failed:", err); addToast(`Failed to rename device: ${err instanceof Error ? err.message : "Unknown error"}`, { variant: "danger" }); } finally { setRenaming(false); } };
  const handleBlock = async () => { if (!deviceId || !device?.ip || blocking) return; setBlocking(true); try { await api.blockDevice(deviceId, device.ip); setBlockOpenConfirm(false); addToast("Device blocked", { variant: "success" }); loadDevice(); } catch (err) { console.error("[DeviceDetail] Block failed:", err); addToast(`Failed to block device: ${err instanceof Error ? err.message : "Unknown error"}`, { variant: "danger" }); } finally { setBlocking(false); } };
  const handleUnblock = async () => { if (!deviceId || unblocking) return; setUnblocking(true); try { await api.unblockDevice(deviceId); addToast("Device unblocked", { variant: "success" }); loadDevice(); } catch (err) { console.error("[DeviceDetail] Unblock failed:", err); addToast(`Failed to unblock device: ${err instanceof Error ? err.message : "Unknown error"}`, { variant: "danger" }); } finally { setUnblocking(false); } };
  const handleSaveLimit = async () => { if (!deviceId || limitLoading) return; setLimitLoading(true); try { const downloadBps = limitUnit === "kbps" ? formatKBpsToBps(Number(limitDownload)) : formatKBpsToBps(Number(limitDownload) * 1024); const uploadBps = limitUnit === "kbps" ? formatKBpsToBps(Number(limitUpload)) : formatKBpsToBps(Number(limitUpload) * 1024); await api.limitDevice(deviceId, downloadBps / (1024 * 8), uploadBps / (1024 * 8), limitEnabled); addToast("Speed limit saved", { variant: "success" }); setLimitOpen(false); loadDevice(); loadLimits(); } catch (err) { console.error("[DeviceDetail] Save limit failed:", err); addToast(`Failed to save speed limit: ${err instanceof Error ? err.message : "Unknown error"}`, { variant: "danger" }); } finally { setLimitLoading(false); } };
  const handleRemoveLimit = async () => { if (!deviceId || limitLoading) return; setLimitLoading(true); try { const data = await api.getLimits(); const deviceLimits = data.filter(l => l.device_id === deviceId); if (deviceLimits.length > 0) { await api.deleteLimit(deviceLimits[0].id?.toString() || ""); addToast("Speed limit removed", { variant: "success" }); loadDevice(); loadLimits(); } } catch (err) { console.error("[DeviceDetail] Remove limit failed:", err); addToast(`Failed to remove speed limit: ${err instanceof Error ? err.message : "Unknown error"}`, { variant: "danger" }); } finally { setLimitLoading(false); } };
  const handleSaveQuota = async () => { if (!deviceId || quotaLoading) return; setQuotaLoading(true); try { let dailyBytes = 0, weeklyBytes = 0, monthlyBytes = 0; const unitMultiplier = quotaUnit === "mb" ? 1024 * 1024 : 1024 * 1024 * 1024; if (quotaDaily) dailyBytes = Number(quotaDaily) * unitMultiplier; if (quotaWeekly) weeklyBytes = Number(quotaWeekly) * unitMultiplier; if (quotaMonthly) monthlyBytes = Number(quotaMonthly) * unitMultiplier; await api.setDeviceQuota(deviceId, dailyBytes || weeklyBytes || monthlyBytes, quotaDaily ? Number(quotaDaily) : undefined, quotaWeekly ? Number(quotaWeekly) : undefined, quotaMonthly ? Number(quotaMonthly) : undefined, quotaEnabled); addToast("Data quota saved", { variant: "success" }); setQuotaOpen(false); loadDevice(); loadQuotas(); } catch (err) { console.error("[DeviceDetail] Save quota failed:", err); addToast(`Failed to save data quota: ${err instanceof Error ? err.message : "Unknown error"}`, { variant: "danger" }); } finally { setQuotaLoading(false); } };
  const handleRemoveQuota = async () => { if (!deviceId || quotaLoading) return; setQuotaLoading(true); try { const data = await api.getQuotas(); const deviceQuotas = data.filter(q => q.device_id === deviceId); if (deviceQuotas.length > 0) { await api.deleteQuota(deviceQuotas[0].id?.toString() || ""); addToast("Data quota removed", { variant: "success" }); loadDevice(); loadQuotas(); } } catch (err) { console.error("[DeviceDetail] Remove quota failed:", err); addToast(`Failed to remove data quota: ${err instanceof Error ? err.message : "Unknown error"}`, { variant: "danger" }); } finally { setQuotaLoading(false); } };
  const handleCreateRule = async () => { if (!deviceId || !newRule.domain.trim() || creatingRule) return; setCreatingRule(true); try { await api.createRule({ name: newRule.domain, description: `Domain rule for ${device?.custom_name || deviceId}`, action: newRule.action, enabled: newRule.enabled, device_id: deviceId }); addToast("Domain rule created", { variant: "success" }); setNewRule({ domain: "", action: "BLOCK", enabled: true }); loadRules(); } catch (err) { console.error("[DeviceDetail] Create rule failed:", err); addToast(`Failed to create rule: ${err instanceof Error ? err.message : "Unknown error"}`, { variant: "danger" }); } finally { setCreatingRule(false); } };
  const handleUpdateRule = async (ruleId: string) => { if (!deviceId || !editedRule.domain.trim()) return; try { await api.updateRule(ruleId, { name: editedRule.domain, description: `Domain rule for ${device?.custom_name || deviceId}`, action: editedRule.action, enabled: editedRule.enabled, device_id: deviceId }); addToast("Domain rule updated", { variant: "success" }); setEditingRuleId(null); loadRules(); } catch (err) { console.error("[DeviceDetail] Update rule failed:", err); addToast(`Failed to update rule: ${err instanceof Error ? err.message : "Unknown error"}`, { variant: "danger" }); } };
  const handleDeleteRule = async (ruleId: string) => { if (!deviceId) return; try { await api.deleteRule(ruleId); addToast("Domain rule deleted", { variant: "success" }); loadRules(); loadFirewallRules(); } catch (err) { console.error("[DeviceDetail] Delete rule failed:", err); addToast(`Failed to delete rule: ${err instanceof Error ? err.message : "Unknown error"}`, { variant: "danger" }); } };
  const handleCreateSchedule = async () => { if (!deviceId || !newSchedule.name.trim() || creatingSchedule) return; setCreatingSchedule(true); try { const desc = JSON.stringify({ domain: newSchedule.domain, days: newSchedule.days, startTime: newSchedule.startTime, endTime: newSchedule.endTime, type: "schedule" }); await api.createRule({ name: newSchedule.name, description: desc, action: newSchedule.action, enabled: newSchedule.enabled, device_id: deviceId }); addToast("Schedule created", { variant: "success" }); setNewSchedule({ name: "", domain: "", action: "BLOCK", days: [1,2,3,4,5,6,0], startTime: "22:00", endTime: "07:00", enabled: true }); loadFirewallRules(); } catch (err) { console.error("[DeviceDetail] Create schedule failed:", err); addToast(`Failed to create schedule: ${err instanceof Error ? err.message : "Unknown error"}`, { variant: "danger" }); } finally { setCreatingSchedule(false); } };
  const handleRefresh = () => { loadDevice(); loadLiveTraffic(); loadHistory(); loadIntel(); loadFlows(); loadRules(); loadLimits(); loadQuotas(); loadFirewallRules(); };

  if (deviceLoading) return <div className="flex items-center justify-center h-64"><div className="text-center"><Loader2 className="h-10 w-10 animate-spin text-primary mx-auto" /><p className="mt-4 text-muted-foreground">Loading device...</p></div></div>;
  if (deviceError || !device) return <div className="text-center py-12"><AlertTriangle className="h-12 w-12 text-danger-500 mx-auto" /><h2 className="text-2xl font-bold text-danger-500 mt-4">Unable to load device</h2><p className="text-muted-foreground mt-2">{deviceError || "Device not found"}</p><Button onClick={() => router.push("/devices")} className="mt-4"><ArrowLeft className="h-4 w-4 mr-2" />Back to Devices</Button></div>;

  const displayName = device.custom_name || device.hostname || "Unnamed Device";
  const statusVariant = device.state === "ONLINE" ? "online" : device.state === "OFFLINE" ? "offline" : "unknown";
  const hasLimit = (device?.limit_id && device?.limit_enabled) || (device?.download_limit_bps || device?.upload_limit_bps);
  const hasQuota = device?.quota_enabled && device?.quota_bytes;

  // Shared tab container class for consistent card content spacing
  const contentClass = "space-y-6";

  return (
    <div className="space-y-6">
      {/* ===== Header: Status + primary actions (always visible) ===== */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div className="flex items-center gap-3 min-w-0">
          <Button variant="ghost" size="icon" onClick={() => router.push("/devices")} title="Back to devices" aria-label="Back to devices"><ArrowLeft className="h-5 w-5" /></Button>
          <div className="min-w-0">
            <div className="flex items-center gap-2 flex-wrap"><h1 className="text-2xl sm:text-3xl font-bold truncate">{displayName}</h1><StatusBadge variant={statusVariant} pulse={device.state === "ONLINE"} /></div>
            <p className="text-muted-foreground text-sm mt-1 truncate"><span className="font-mono">{device.device_id}</span>{device.vendor ? ` · ${device.vendor}` : ""}{device.interface ? ` · ${device.interface}` : ""}</p>
          </div>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <Button variant="outline" size="sm" onClick={() => { setRenameValue(device.custom_name || device.hostname || ""); setRenameOpen(true); }}><Tag className="h-4 w-4 mr-2" />Rename</Button>
          {device.state === "ONLINE"
            ? <Button variant="outline" size="sm" onClick={handleUnblock} disabled={unblocking}><Unlock className="h-4 w-4 mr-2" />{unblocking ? "Unblocking..." : "Unblock"}</Button>
            : <Button variant="destructive" size="sm" onClick={() => setBlockOpenConfirm(true)} disabled={blocking}><Lock className="h-4 w-4 mr-2" />{blocking ? "Blocking..." : "Block"}</Button>}
          <Button variant="outline" size="sm" onClick={handleRefresh}><RefreshCw className="h-4 w-4 mr-2" />Refresh</Button>
        </div>
      </div>

      {/* ===== Sticky tab navigation ===== */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <div className="sticky top-16 z-20 -mx-4 sm:-mx-6 lg:-mx-8 px-4 sm:px-6 lg:px-8 py-2 bg-background/95 backdrop-blur-sm border-b border-border">
          <TabsList className="w-full justify-start overflow-x-auto">
            <TabsTrigger value="overview"><LayoutGrid />Overview</TabsTrigger>
            <TabsTrigger value="traffic"><Activity />Traffic</TabsTrigger>
            <TabsTrigger value="applications"><AppWindow />Applications</TabsTrigger>
            <TabsTrigger value="websites"><Globe />Websites</TabsTrigger>
            <TabsTrigger value="analytics"><BarChart2 />Analytics</TabsTrigger>
            <TabsTrigger value="connections"><Link2 />Connections</TabsTrigger>
            <TabsTrigger value="controls"><Settings />Controls</TabsTrigger>
          </TabsList>
        </div>

        {/* ===== Overview ===== */}
        <TabsContent value="overview" className={contentClass}>
          <Card><CardContent className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 py-4">
            <div><p className="text-xs text-muted-foreground">IP Address</p><p className="font-mono text-sm font-medium">{device.ip || "—"}</p></div>
            <div><p className="text-xs text-muted-foreground">MAC Address</p><p className="font-mono text-sm font-medium">{device.mac || "—"}</p></div>
            <div><p className="text-xs text-muted-foreground">Hostname</p><p className="text-sm font-medium">{device.hostname || "—"}</p></div>
            <div><p className="text-xs text-muted-foreground">Vendor</p><p className="text-sm font-medium">{device.vendor || "—"}</p></div>
            <div><p className="text-xs text-muted-foreground">Interface</p><p className="text-sm font-medium">{device.interface || "—"}</p></div>
            <div><p className="text-xs text-muted-foreground">Last Seen</p><p className="text-sm font-medium">{formatDate(device.last_seen)}</p></div>
          </CardContent></Card>

          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <MetricCard label="Download Today" value={formatBytes(totalDownload)} icon={<Download className="h-6 w-6" />} variant="primary" />
            <MetricCard label="Upload Today" value={formatBytes(totalUpload)} icon={<Upload className="h-6 w-6" />} variant="success" />
            <MetricCard label="Total Traffic" value={formatBytes(totalTraffic)} icon={<Activity className="h-6 w-6" />} variant="info" />
            <MetricCard label="Current Speed" value={formatSpeed(currentSpeed)} icon={<Zap className="h-6 w-6" />} variant="warning" />
          </div>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <MetricCard label="Packets" value={totalPackets.toLocaleString()} icon={<Layers className="h-6 w-6" />} variant="neutral" />
            <MetricCard label="Active Flows" value={flowCount} icon={<Link2 className="h-6 w-6" />} variant="neutral" />
            <MetricCard label="First Seen" value={formatDate(device.first_seen)} icon={<Clock className="h-6 w-6" />} variant="neutral" />
            <MetricCard label="Live Stream" value={wsStatus === "open" ? "Connected" : wsStatus === "connecting" ? "Connecting" : "Disconnected"} icon={wsStatus === "open" ? <Wifi className="h-6 w-6" /> : <Server className="h-6 w-6" />} variant={wsStatus === "open" ? "success" : "neutral"} />
          </div>

          {hasQuota && (
            <Card><CardHeader><CardTitle className="flex items-center gap-2"><Gauge className="h-5 w-5" />Data Usage</CardTitle></CardHeader><CardContent>
              <div className="flex items-center justify-between text-sm mb-2">
                <span className="text-muted-foreground">{formatBytes(quotaUsed)} used of {formatBytes(quotaTotal)}</span>
                <span className="font-medium">{quotaPct}%</span>
              </div>
              <Progress value={quotaPct} className="h-2" />
            </CardContent></Card>
          )}
        </TabsContent>

        {/* ===== Traffic ===== */}
        <TabsContent value="traffic" className={contentClass}>
          <Card><CardHeader><CardTitle className="flex items-center gap-2"><Activity className="h-5 w-5" />Live Traffic</CardTitle><CardDescription>Real-time download/upload speed from traffic_samples (Mbps)</CardDescription></CardHeader><CardContent>{liveLoading ? <div className="flex items-center justify-center h-[280px]"><Loader2 className="h-8 w-8 animate-spin text-muted-foreground" /><span className="ml-2 text-muted-foreground">Loading live traffic...</span></div> : liveError ? <div className="text-center py-12 text-danger-500">{liveError}</div> : liveChartData.length === 0 ? <div className="text-center py-12 text-muted-foreground">No live traffic data available for this device.</div> : <div className="h-[280px] w-full"><ResponsiveContainer width="100%" height="100%"><AreaChart data={liveChartData}><defs><linearGradient id="dlGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} /><stop offset="95%" stopColor="#3b82f6" stopOpacity={0} /></linearGradient><linearGradient id="ulGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#22c55e" stopOpacity={0.3} /><stop offset="95%" stopColor="#22c55e" stopOpacity={0} /></linearGradient></defs><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="time" tick={{ fontSize: 11 }} /><YAxis tick={{ fontSize: 11 }} /><Tooltip /><Legend /><Area type="monotone" dataKey="download" name="Download" stroke="#3b82f6" fill="url(#dlGrad)" strokeWidth={2} /><Area type="monotone" dataKey="upload" name="Upload" stroke="#22c55e" fill="url(#ulGrad)" strokeWidth={2} /></AreaChart></ResponsiveContainer></div>}</CardContent></Card>

          <Card><CardHeader className="flex flex-row items-center justify-between"><div><CardTitle className="flex items-center gap-2"><Database className="h-5 w-5" />Traffic History</CardTitle><CardDescription>Daily download/upload from usage_daily (MB)</CardDescription></div><div className="flex items-center gap-1">{[7, 30].map((d) => <Button key={d} variant={historyDays === d ? "default" : "outline"} size="sm" onClick={() => { setHistoryDays(d); loadHistory(); }}>{d}D</Button>)}</div></CardHeader><CardContent>{historyLoading ? <div className="flex items-center justify-center h-[240px]"><Loader2 className="h-8 w-8 animate-spin text-muted-foreground" /><span className="ml-2 text-muted-foreground">Loading history...</span></div> : historyError ? <div className="text-center py-12 text-danger-500">{historyError}</div> : historyChartData.length === 0 ? <div className="text-center py-12 text-muted-foreground">No traffic history available for this period.</div> : <div className="h-[240px] w-full"><ResponsiveContainer width="100%" height="100%"><BarChart data={historyChartData}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="date" tick={{ fontSize: 11 }} /><YAxis tick={{ fontSize: 11 }} /><Tooltip /><Legend /><Bar dataKey="download" name="Download" fill="#3b82f6" /><Bar dataKey="upload" name="Upload" fill="#22c55e" /></BarChart></ResponsiveContainer></div>}</CardContent></Card>
        </TabsContent>

        {/* ===== Applications ===== */}
        <TabsContent value="applications" className={contentClass}>
          <div className="flex items-center justify-between"><h2 className="text-lg font-semibold">Applications</h2><div className="flex items-center gap-1">{["1h", "24h", "7d", "30d"].map((r) => <Button key={r} variant={intelRange === r ? "default" : "outline"} size="sm" onClick={() => { setIntelRange(r); loadIntel(); }}>{r.toUpperCase()}</Button>)}</div></div>
          <div className="grid gap-6 lg:grid-cols-2">
            <Card><CardHeader><CardTitle className="flex items-center gap-2"><AppWindow className="h-5 w-5" />Top Applications</CardTitle><CardDescription>Real attributed application traffic for this device</CardDescription></CardHeader><CardContent>{appsLoading ? <div className="flex items-center justify-center h-[200px]"><Loader2 className="h-8 w-8 animate-spin text-muted-foreground" /><span className="ml-2 text-muted-foreground">Loading application data...</span></div> : appsError ? <div className="text-center py-12 text-danger-500">{appsError}</div> : apps.length === 0 ? <div className="text-center py-12 text-muted-foreground">No application traffic recorded for this device.</div> : <div className="space-y-3">{apps.slice(0, 8).map((app) => <div key={app.name} className="space-y-1"><div className="flex items-center justify-between text-sm"><span className="font-medium truncate">{app.name}</span><div className="flex items-center gap-2"><Badge variant={app.confidence === "HIGH" ? "default" : app.confidence === "MEDIUM" ? "secondary" : "outline"}>{app.confidence}</Badge><span className="text-muted-foreground">{formatBytes(app.total_bytes)}</span></div></div><Progress value={appChartData.find((a) => a.name === app.name)?.pct ?? 0} className="h-2" />{app.evidence && <div className="text-xs text-muted-foreground flex items-center gap-1"><Shield className="h-3 w-3" />Evidence: {app.evidence.source} · {app.evidence.value}</div>}</div>)}</div>}</CardContent></Card>
            <Card><CardHeader><CardTitle className="flex items-center gap-2"><Layers className="h-5 w-5" />Categories</CardTitle><CardDescription>Traffic by category from backend classification</CardDescription></CardHeader><CardContent>{categoriesLoading ? <div className="flex items-center justify-center h-[200px]"><Loader2 className="h-8 w-8 animate-spin text-muted-foreground" /><span className="ml-2 text-muted-foreground">Loading category data...</span></div> : categoriesError ? <div className="text-center py-12 text-danger-500">{categoriesError}</div> : categories.length === 0 ? <div className="text-center py-12 text-muted-foreground">No category data recorded for this device.</div> : <div className="h-[220px] w-full"><ResponsiveContainer width="100%" height="100%"><PieChart><Pie data={categoryPieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label>{categoryPieData.map((entry, idx) => <Cell key={idx} fill={["#3b82f6", "#22c55e", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4", "#ec4899", "#84cc16"][idx % 8]} />)}</Pie><Tooltip formatter={(v) => formatBytes(Number(v))} /><Legend /></PieChart></ResponsiveContainer></div>}</CardContent></Card>
          </div>
        </TabsContent>

        {/* ===== Websites ===== */}
        <TabsContent value="websites" className={contentClass}>
          <div className="flex items-center justify-between"><h2 className="text-lg font-semibold">Websites / Domains</h2><div className="flex items-center gap-1">{["1h", "24h", "7d", "30d"].map((r) => <Button key={r} variant={intelRange === r ? "default" : "outline"} size="sm" onClick={() => { setIntelRange(r); loadIntel(); }}>{r.toUpperCase()}</Button>)}</div></div>
          <Card><CardHeader><CardTitle className="flex items-center gap-2"><Globe className="h-5 w-5" />Top Domains</CardTitle><CardDescription>Real DNS/domain usage for this device</CardDescription></CardHeader><CardContent>{domainsLoading ? <div className="flex items-center justify-center h-[200px]"><Loader2 className="h-8 w-8 animate-spin text-muted-foreground" /><span className="ml-2 text-muted-foreground">Loading domain data...</span></div> : domainsError ? <div className="text-center py-12 text-danger-500">{domainsError}</div> : domains.length === 0 ? <div className="text-center py-12 text-muted-foreground">No DNS/domain data captured for this device.</div> : <div className="space-y-3">{domains.slice(0, 10).map((d) => <div key={d.domain} className="space-y-1"><div className="flex items-center justify-between text-sm"><span className="font-medium truncate">{d.domain}</span><div className="flex items-center gap-2"><Badge variant={d.confidence === "HIGH" ? "default" : d.confidence === "MEDIUM" ? "secondary" : "outline"}>{d.confidence}</Badge><span className="text-muted-foreground">{formatBytes(d.total_bytes)}</span></div></div><Progress value={domainChartData.find((x) => x.name === d.domain)?.pct ?? 0} className="h-2" />{d.evidence && <div className="text-xs text-muted-foreground flex items-center gap-1"><Globe className="h-3 w-3" />Evidence: {d.evidence.source} · {d.evidence.value}</div>}</div>)}</div>}</CardContent></Card>
        </TabsContent>

        {/* ===== Analytics ===== */}
        <TabsContent value="analytics" className={contentClass}>
          <div className="grid gap-6 lg:grid-cols-2">
            <Card><CardHeader><CardTitle className="flex items-center gap-2"><Network className="h-5 w-5" />Protocols</CardTitle><CardDescription>Traffic by protocol from real flow attribution</CardDescription></CardHeader><CardContent>{protocolsLoading ? <div className="flex items-center justify-center h-[200px]"><Loader2 className="h-8 w-8 animate-spin text-muted-foreground" /><span className="ml-2 text-muted-foreground">Loading protocol data...</span></div> : protocolsError ? <div className="text-center py-12 text-danger-500">{protocolsError}</div> : protocols.length === 0 ? <div className="text-center py-12 text-muted-foreground">No protocol data recorded for this device.</div> : <div className="space-y-3">{protocols.slice(0, 8).map((p) => <div key={p.protocol} className="space-y-1"><div className="flex items-center justify-between text-sm"><span className="font-medium">{p.protocol}</span><span className="text-muted-foreground">{formatBytes(p.total_bytes)} · {p.packets?.toLocaleString() ?? 0} pkts</span></div><Progress value={protocolChartData.find((x) => x.name === p.protocol)?.pct ?? 0} className="h-2" /></div>)}</div>}</CardContent></Card>
            <Card><CardHeader><CardTitle className="flex items-center gap-2"><Clock className="h-5 w-5" />Activity Timeline</CardTitle><CardDescription>Hourly activity from device_activity_timeline</CardDescription></CardHeader><CardContent>{activityLoading ? <div className="flex items-center justify-center h-[200px]"><Loader2 className="h-8 w-8 animate-spin text-muted-foreground" /><span className="ml-2 text-muted-foreground">Loading activity...</span></div> : activityError ? <div className="text-center py-12 text-danger-500">{activityError}</div> : activityData.length === 0 ? <div className="text-center py-12 text-muted-foreground">No activity recorded for this device.</div> : <div className="h-[220px] w-full"><ResponsiveContainer width="100%" height="100%"><LineChart data={activityData}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="time" tick={{ fontSize: 10 }} /><YAxis tick={{ fontSize: 11 }} /><Tooltip formatter={(v) => formatBytes(Number(v))} /><Line type="monotone" dataKey="bytes" name="Traffic" stroke="#8b5cf6" strokeWidth={2} dot={false} /></LineChart></ResponsiveContainer></div>}</CardContent></Card>
          </div>
          <Card><CardHeader><CardTitle className="flex items-center gap-2"><Zap className="h-5 w-5" />Peak Usage</CardTitle><CardDescription>Peak speeds from device_peaks</CardDescription></CardHeader><CardContent>{peaksLoading ? <div className="flex items-center justify-center h-[200px]"><Loader2 className="h-8 w-8 animate-spin text-muted-foreground" /><span className="ml-2 text-muted-foreground">Loading peak data...</span></div> : peaksError ? <div className="text-center py-12 text-danger-500">{peaksError}</div> : peaks.length === 0 ? <div className="text-center py-12 text-muted-foreground">No peak usage recorded for this device.</div> : <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">{[{ label: "Peak Download", peak: peakSummary.download, icon: <Download className="h-4 w-4" /> },{ label: "Peak Upload", peak: peakSummary.upload, icon: <Upload className="h-4 w-4" /> },{ label: "Peak Total", peak: peakSummary.total, icon: <Activity className="h-4 w-4" /> },{ label: "Peak Connections", peak: peakSummary.connections, icon: <Link2 className="h-4 w-4" /> }].map(({ label, peak, icon }) => <div key={label} className="flex items-center justify-between p-4 border border-border rounded-lg"><div className="flex items-center gap-2 text-sm">{icon}<span className="text-muted-foreground">{label}</span></div><div className="text-right"><div className="font-medium">{peak ? peak.peak_type === "connections" ? Number(peak.peak_value).toLocaleString() : formatSpeed(Number(peak.peak_value)) : "—"}</div><div className="text-xs text-muted-foreground">{peak ? formatDate(peak.peak_at) : "No data"}</div></div></div>)}</div>}</CardContent></Card>
        </TabsContent>

        {/* ===== Connections ===== */}
        <TabsContent value="connections" className={contentClass}>
          <Card><CardHeader><CardTitle className="flex items-center gap-2"><Link2 className="h-5 w-5" />Active Connections / Flows</CardTitle><CardDescription>Real flows for this device from the flows table</CardDescription></CardHeader><CardContent>{flowsLoading ? <div className="flex items-center justify-center h-[160px]"><Loader2 className="h-8 w-8 animate-spin text-muted-foreground" /><span className="ml-2 text-muted-foreground">Loading connections...</span></div> : flowsError ? <div className="text-center py-12 text-danger-500">{flowsError}</div> : deviceFlows.length === 0 ? <div className="text-center py-12 text-muted-foreground">No active connections recorded for this device.</div> : <div className="overflow-x-auto"><table className="w-full text-sm"><thead><tr className="border-b border-border text-left text-muted-foreground"><th className="py-2 pr-4 font-medium">Destination IP</th><th className="py-2 pr-4 font-medium">Port</th><th className="py-2 pr-4 font-medium">Protocol</th><th className="py-2 pr-4 font-medium">Direction</th><th className="py-2 pr-4 font-medium text-right">Bytes</th><th className="py-2 pr-4 font-medium text-right">Packets</th><th className="py-2 pr-4 font-medium">Started</th><th className="py-2 font-medium">State</th></tr></thead><tbody>{deviceFlows.slice(0, 30).map((f) => <tr key={f.id} className="border-b border-border/50 hover:bg-muted/50"><td className="py-2 pr-4 font-mono">{f.destination_ip || "—"}</td><td className="py-2 pr-4">{f.destination_port || "—"}</td><td className="py-2 pr-4">{f.protocol || "—"}</td><td className="py-2 pr-4"><Badge variant={f.direction === "OUTBOUND" ? "default" : "secondary"}>{f.direction || "—"}</Badge></td><td className="py-2 pr-4 text-right">{formatBytes(f.bytes)}</td><td className="py-2 pr-4 text-right">{f.packets?.toLocaleString() ?? 0}</td><td className="py-2 pr-4">{formatTime(f.started_at)}</td><td className="py-2"><Badge variant={f.state === "ACTIVE" ? "default" : "secondary"}>{f.state || "—"}</Badge></td></tr>)}</tbody></table></div>}</CardContent></Card>
        </TabsContent>

        {/* ===== Controls ===== */}
        <TabsContent value="controls" className={contentClass}>
          <div>
            <h2 className="text-xl font-bold flex items-center gap-2"><Settings className="h-6 w-6" />Control Center</h2>
            <p className="text-muted-foreground mt-1">Manage speed limits, data quotas, domain rules, schedules, and firewall for this device.</p>
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <Card><CardHeader className="flex flex-row items-center justify-between"><div className="flex items-center gap-2"><Gauge className="h-5 w-5" /><CardTitle>Speed Limit</CardTitle></div><Button variant="outline" size="sm" onClick={() => { loadLimits(); setLimitOpen(true); }}><Wrench className="h-4 w-4 mr-2" />Configure</Button></CardHeader><CardContent><div className="grid gap-4 sm:grid-cols-2"><div><p className="text-xs text-muted-foreground">Current Download Limit</p><p className="font-mono text-lg font-medium">{hasLimit && device?.download_limit_bps ? formatSpeed(device.download_limit_bps) : "No limit"}</p></div><div><p className="text-xs text-muted-foreground">Current Upload Limit</p><p className="font-mono text-lg font-medium">{hasLimit && device?.upload_limit_bps ? formatSpeed(device.upload_limit_bps) : "No limit"}</p></div><div><p className="text-xs text-muted-foreground">Status</p><p className="font-medium"><Badge variant={hasLimit && device?.limit_enabled ? "default" : "secondary"}>{hasLimit && device?.limit_enabled ? "Enabled" : "Disabled"}</Badge></p></div><div><p className="text-xs text-muted-foreground">Limit ID</p><p className="font-mono text-sm">{device?.limit_id ? `#${device.limit_id}` : "—"}</p></div></div></CardContent></Card>

            <Card><CardHeader className="flex flex-row items-center justify-between"><div className="flex items-center gap-2"><HardDrive className="h-5 w-5" /><CardTitle>Data Quota</CardTitle></div><Button variant="outline" size="sm" onClick={() => { loadQuotas(); setQuotaOpen(true); }}><Wrench className="h-4 w-4 mr-2" />Configure</Button></CardHeader><CardContent><div className="grid gap-4 sm:grid-cols-2"><div><p className="text-xs text-muted-foreground">Daily Quota</p><p className="font-mono text-lg font-medium">{hasQuota && device?.quota_bytes ? formatBytes(device.quota_bytes) : "No quota"}</p></div><div><p className="text-xs text-muted-foreground">Used / Remaining</p><p className="font-mono text-lg font-medium">{formatBytes(quotaUsed)} / <span className="text-success">{formatBytes(quotaRemaining)}</span></p></div><div className="col-span-2"><p className="text-xs text-muted-foreground mb-2">Usage</p><Progress value={quotaPct} className="h-3" /><p className="text-sm text-muted-foreground mt-1">{quotaPct}% used</p></div><div><p className="text-xs text-muted-foreground">Status</p><p className="font-medium"><Badge variant={hasQuota && device?.quota_enabled ? "default" : "secondary"}>{hasQuota && device?.quota_enabled ? "Enabled" : "Disabled"}</Badge></p></div></div></CardContent></Card>
          </div>

          <Card><CardHeader className="flex flex-row items-center justify-between"><div className="flex items-center gap-2"><Globe className="h-5 w-5" /><CardTitle>Website Rules</CardTitle><CardDescription>Allow or block specific websites for this device</CardDescription></div><Button variant="outline" size="sm" onClick={() => { loadRules(); setRulesOpen(true); }}><Wrench className="h-4 w-4 mr-2" />Manage</Button></CardHeader><CardContent>{rulesLoading ? <div className="flex items-center justify-center h-[160px]"><Loader2 className="h-8 w-8 animate-spin text-muted-foreground" /><span className="ml-2 text-muted-foreground">Loading rules...</span></div> : rules.length === 0 ? <div className="text-center py-8 text-muted-foreground">No website rules configured for this device.</div> : <div className="space-y-3">{rules.map((rule) => <div key={rule.id} className="flex items-center justify-between p-3 border border-border rounded-lg"><div className="flex items-center gap-3"><Badge variant={rule.action === "BLOCK" ? "destructive" : "default"}>{rule.action}</Badge><div><p className="font-medium">{rule.name}</p><p className="text-xs text-muted-foreground">{rule.enabled ? "Enabled" : "Disabled"} · Created {formatDate(rule.created_at)}</p></div></div><div className="flex items-center gap-2"><Button variant="ghost" size="icon" onClick={() => { setEditingRuleId(rule.id?.toString() || ""); setEditedRule({ domain: rule.name, action: rule.action as "ALLOW" | "BLOCK", enabled: rule.enabled }); }} title="Edit rule"><Edit2 className="h-4 w-4" /></Button><Button variant="ghost" size="icon" onClick={() => handleDeleteRule(rule.id?.toString() || "")} title="Delete rule"><Trash2 className="h-4 w-4" /></Button></div></div>)}</div>}</CardContent></Card>

          <Card><CardHeader className="flex flex-row items-center justify-between"><div className="flex items-center gap-2"><Calendar className="h-5 w-5" /><CardTitle>Schedules</CardTitle><CardDescription>Time-based access schedules for this device</CardDescription></div><Button variant="outline" size="sm" onClick={() => { loadFirewallRules(); setScheduleOpen(true); }}><Wrench className="h-4 w-4 mr-2" />Manage</Button></CardHeader><CardContent>{schedulesLoading ? <div className="flex items-center justify-center h-[160px]"><Loader2 className="h-8 w-8 animate-spin text-muted-foreground" /><span className="ml-2 text-muted-foreground">Loading schedules...</span></div> : schedules.length === 0 ? <div className="text-center py-8 text-muted-foreground">No schedules configured for this device.</div> : <div className="grid gap-3 sm:grid-cols-2">{schedules.map((sched) => { let desc: { domain?: string; days?: number[]; startTime?: string; endTime?: string } = {}; try { desc = JSON.parse(sched.description || "{}"); } catch { /* ignore */ } return (
              <div key={sched.id} className="p-3 border border-border rounded-lg space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2"><Badge variant={sched.action === "BLOCK" ? "destructive" : "default"}>{sched.action}</Badge><p className="font-medium">{sched.name}</p></div>
                  <Button variant="ghost" size="icon" onClick={() => handleDeleteRule(sched.id?.toString() || "")} title="Delete schedule"><Trash2 className="h-4 w-4" /></Button>
                </div>
                {desc.domain && <p className="text-xs text-muted-foreground">Domain: {desc.domain}</p>}
                <p className="text-xs text-muted-foreground">{desc.days && desc.days.length ? `Days: ${desc.days.slice().sort((a, b) => a - b).join(", ")} · ${desc.startTime} – ${desc.endTime}` : "Repeating schedule"}</p>
                <p className="text-xs"><Badge variant={sched.enabled ? "default" : "secondary"}>{sched.enabled ? "Enabled" : "Disabled"}</Badge></p>
              </div>
            ); })}</div>}</CardContent></Card>
        </TabsContent>
      </Tabs>

      {/* ===== Dialogs ===== */}
      <Dialog open={renameOpen} onOpenChange={setRenameOpen}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader><DialogTitle>Rename Device</DialogTitle><DialogDescription>Set a friendly name for this device.</DialogDescription></DialogHeader>
          <div className="grid gap-4 py-4"><Input value={renameValue} onChange={(e) => setRenameValue(e.target.value)} placeholder="Enter device name" autoFocus disabled={renaming} /></div>
          <DialogFooter><Button variant="outline" onClick={() => setRenameOpen(false)} disabled={renaming}>Cancel</Button><Button onClick={handleRename} disabled={renaming || !renameValue.trim()}>{renaming ? "Saving..." : "Save"}</Button></DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={blockOpenConfirm} onOpenChange={setBlockOpenConfirm}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader><DialogTitle>Block Device?</DialogTitle><DialogDescription>This will block {displayName} ({device.ip || "no IP"}) from the network. The backend will enforce the block via {device.interface || "the monitored interface"}.</DialogDescription></DialogHeader>
          <DialogFooter><Button variant="outline" onClick={() => setBlockOpenConfirm(false)} disabled={blocking}>Cancel</Button><Button variant="destructive" onClick={handleBlock} disabled={blocking}>{blocking ? "Blocking..." : "Block Device"}</Button></DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={limitOpen} onOpenChange={setLimitOpen}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader><DialogTitle>Configure Speed Limit</DialogTitle><DialogDescription>Set download/upload speed limits for this device. Enforced by the backend.</DialogDescription></DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="flex items-center justify-between"><p className="text-sm text-muted-foreground">Enabled</p><select value={limitEnabled ? "1" : "0"} onChange={(e) => setLimitEnabled(e.target.value === "1")} className="px-2 py-1 border border-border rounded-md text-sm"><option value="1">Yes</option><option value="0">No</option></select></div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1"><label className="text-xs text-muted-foreground">Download Limit</label><Input type="number" min="0" value={limitDownload} onChange={(e) => setLimitDownload(e.target.value)} placeholder="e.g. 10" /></div>
              <div className="space-y-1"><label className="text-xs text-muted-foreground">Upload Limit</label><Input type="number" min="0" value={limitUpload} onChange={(e) => setLimitUpload(e.target.value)} placeholder="e.g. 5" /></div>
            </div>
            <div className="space-y-1"><label className="text-xs text-muted-foreground">Unit</label><select value={limitUnit} onChange={(e) => setLimitUnit(e.target.value as "kbps" | "mbps")} className="w-full px-2 py-1 border border-border rounded-md text-sm"><option value="mbps">Mbps</option><option value="kbps">Kbps</option></select></div>
          </div>
          <DialogFooter><Button variant="outline" onClick={() => setLimitOpen(false)} disabled={limitLoading}>Cancel</Button><Button variant="destructive" onClick={handleRemoveLimit} disabled={limitLoading}>Remove Limit</Button><Button onClick={handleSaveLimit} disabled={limitLoading}>{limitLoading ? "Saving..." : "Save Limit"}</Button></DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={quotaOpen} onOpenChange={setQuotaOpen}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader><DialogTitle>Configure Data Quota</DialogTitle><DialogDescription>Set daily/weekly/monthly data limits for this device. Enforced by the backend.</DialogDescription></DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="flex items-center justify-between"><p className="text-sm text-muted-foreground">Enabled</p><select value={quotaEnabled ? "1" : "0"} onChange={(e) => setQuotaEnabled(e.target.value === "1")} className="px-2 py-1 border border-border rounded-md text-sm"><option value="1">Yes</option><option value="0">No</option></select></div>
            <div className="grid grid-cols-3 gap-3">
              <div className="space-y-1"><label className="text-xs text-muted-foreground">Daily (GB)</label><Input type="number" min="0" value={quotaDaily} onChange={(e) => setQuotaDaily(e.target.value)} placeholder="e.g. 5" /></div>
              <div className="space-y-1"><label className="text-xs text-muted-foreground">Weekly</label><Input type="number" min="0" value={quotaWeekly} onChange={(e) => setQuotaWeekly(e.target.value)} placeholder="e.g. 20" /></div>
              <div className="space-y-1"><label className="text-xs text-muted-foreground">Monthly</label><Input type="number" min="0" value={quotaMonthly} onChange={(e) => setQuotaMonthly(e.target.value)} placeholder="e.g. 80" /></div>
            </div>
          </div>
          <DialogFooter><Button variant="outline" onClick={() => setQuotaOpen(false)} disabled={quotaLoading}>Cancel</Button><Button variant="destructive" onClick={handleRemoveQuota} disabled={quotaLoading}>Remove Quota</Button><Button onClick={handleSaveQuota} disabled={quotaLoading}>{quotaLoading ? "Saving..." : "Save Quota"}</Button></DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={rulesOpen} onOpenChange={setRulesOpen}>
        <DialogContent className="sm:max-w-[560px]">
          <DialogHeader><DialogTitle>Website Rules</DialogTitle><DialogDescription>Create, edit, enable, or delete domain rules for {displayName}.</DialogDescription></DialogHeader>
          <div className="grid gap-4 py-4">
            {editingRuleId ? (
              <div className="space-y-3 border border-border rounded-lg p-4">
                <p className="text-sm font-medium">Edit Rule</p>
                <Input value={editedRule.domain} onChange={(e) => setEditedRule((r) => ({ ...r, domain: e.target.value }))} placeholder="Domain" />
                <div className="flex items-center gap-2"><label className="text-sm text-muted-foreground">Action</label><select value={editedRule.action} onChange={(e) => setEditedRule((r) => ({ ...r, action: e.target.value as "ALLOW" | "BLOCK" }))} className="px-2 py-1 border border-border rounded-md text-sm"><option value="BLOCK">Block</option><option value="ALLOW">Allow</option></select><label className="text-sm text-muted-foreground ml-4">Enabled</label><select value={editedRule.enabled ? "1" : "0"} onChange={(e) => setEditedRule((r) => ({ ...r, enabled: e.target.value === "1" }))} className="px-2 py-1 border border-border rounded-md text-sm"><option value="1">Yes</option><option value="0">No</option></select></div>
                <div className="flex gap-2"><Button onClick={() => handleUpdateRule(editingRuleId)}>Save</Button><Button variant="outline" onClick={() => setEditingRuleId(null)}>Cancel</Button></div>
              </div>
            ) : (
              <div className="space-y-3 border border-border rounded-lg p-4">
                <p className="text-sm font-medium">New Rule</p>
                <Input value={newRule.domain} onChange={(e) => setNewRule((r) => ({ ...r, domain: e.target.value }))} placeholder="e.g. example.com" />
                <div className="flex items-center gap-2"><label className="text-sm text-muted-foreground">Action</label><select value={newRule.action} onChange={(e) => setNewRule((r) => ({ ...r, action: e.target.value as "ALLOW" | "BLOCK" }))} className="px-2 py-1 border border-border rounded-md text-sm"><option value="BLOCK">Block</option><option value="ALLOW">Allow</option></select><label className="text-sm text-muted-foreground ml-4">Enabled</label><select value={newRule.enabled ? "1" : "0"} onChange={(e) => setNewRule((r) => ({ ...r, enabled: e.target.value === "1" }))} className="px-2 py-1 border border-border rounded-md text-sm"><option value="1">Yes</option><option value="0">No</option></select></div>
                <Button onClick={handleCreateRule} disabled={creatingRule || !newRule.domain.trim()}>{creatingRule ? "Creating..." : "Create Rule"}</Button>
              </div>
            )}
            <div className="max-h-64 overflow-y-auto space-y-2">{rules.map((rule) => <div key={rule.id} className="flex items-center justify-between p-2 border border-border rounded-md"><div className="flex items-center gap-2"><Badge variant={rule.action === "BLOCK" ? "destructive" : "default"}>{rule.action}</Badge><span className="text-sm font-medium">{rule.name}</span><Badge variant={rule.enabled ? "default" : "secondary"}>{rule.enabled ? "On" : "Off"}</Badge></div><div className="flex items-center gap-1"><Button variant="ghost" size="icon" onClick={() => { setEditingRuleId(rule.id?.toString() || ""); setEditedRule({ domain: rule.name, action: rule.action as "ALLOW" | "BLOCK", enabled: rule.enabled }); }} title="Edit rule"><Edit2 className="h-4 w-4" /></Button><Button variant="ghost" size="icon" onClick={() => handleDeleteRule(rule.id?.toString() || "")} title="Delete rule"><Trash2 className="h-4 w-4" /></Button></div></div>)}</div>
          </div>
          <DialogFooter><Button variant="outline" onClick={() => setRulesOpen(false)}>Close</Button></DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={scheduleOpen} onOpenChange={setScheduleOpen}>
        <DialogContent className="sm:max-w-[560px]">
          <DialogHeader><DialogTitle>Schedules</DialogTitle><DialogDescription>Create time-based access schedules for {displayName}.</DialogDescription></DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="space-y-3 border border-border rounded-lg p-4">
              <p className="text-sm font-medium">New Schedule</p>
              <div className="grid grid-cols-2 gap-3"><div className="space-y-1"><label className="text-xs text-muted-foreground">Name</label><Input value={newSchedule.name} onChange={(e) => setNewSchedule((s) => ({ ...s, name: e.target.value }))} placeholder="e.g. Weekend block" /></div><div className="space-y-1"><label className="text-xs text-muted-foreground">Domain (optional)</label><Input value={newSchedule.domain} onChange={(e) => setNewSchedule((s) => ({ ...s, domain: e.target.value }))} placeholder="e.g. social.com" /></div></div>
              <div className="flex items-center gap-2"><label className="text-sm text-muted-foreground">Action</label><select value={newSchedule.action} onChange={(e) => setNewSchedule((s) => ({ ...s, action: e.target.value as "ALLOW" | "BLOCK" }))} className="px-2 py-1 border border-border rounded-md text-sm"><option value="BLOCK">Block</option><option value="ALLOW">Allow</option></select></div>
              <div className="space-y-1"><label className="text-xs text-muted-foreground">Days</label><div className="flex flex-wrap gap-1">{[0, 1, 2, 3, 4, 5, 6].map((d) => { const labels = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]; const active = newSchedule.days.includes(d); return <button key={d} type="button" onClick={() => setNewSchedule((s) => ({ ...s, days: active ? s.days.filter((x) => x !== d) : [...s.days, d] }))} className={`px-2 py-1 rounded-md text-xs font-medium ${active ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"}`}>{labels[d]}</button>; })}</div></div>
              <div className="grid grid-cols-2 gap-3"><div className="space-y-1"><label className="text-xs text-muted-foreground">Start Time</label><Input type="time" value={newSchedule.startTime} onChange={(e) => setNewSchedule((s) => ({ ...s, startTime: e.target.value }))} /></div><div className="space-y-1"><label className="text-xs text-muted-foreground">End Time</label><Input type="time" value={newSchedule.endTime} onChange={(e) => setNewSchedule((s) => ({ ...s, endTime: e.target.value }))} /></div></div>
              <Button onClick={handleCreateSchedule} disabled={creatingSchedule || !newSchedule.name.trim()}>{creatingSchedule ? "Creating..." : "Create Schedule"}</Button>
            </div>
          </div>
          <DialogFooter><Button variant="outline" onClick={() => setScheduleOpen(false)}>Close</Button></DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
