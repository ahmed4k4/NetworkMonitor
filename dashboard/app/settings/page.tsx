"use client";

import { useCallback, useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { api, isAuthenticated } from "@/lib/api";
import { Settings as SettingsType } from "@/lib/types";
import { Settings as SettingsIcon, Network, Save, RefreshCw } from "lucide-react";

export default function SettingsPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("GENERAL");
  const [error, setError] = useState<string | null>(null);
  const [settings, setSettings] = useState<SettingsType>({});
  const [saving, setSaving] = useState(false);

  const loadSettingsData = useCallback(async () => {
    try {
      const settingsData = await api.getSettings();
      setSettings(settingsData || {});
    } catch (err) {
      console.error("Failed to load settings data:", err);
      setError(err instanceof Error ? err.message : "Failed to load settings data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push("/login");
      return;
    }

    const timer = setTimeout(() => {
      loadSettingsData();
    }, 0);

    return () => clearTimeout(timer);
  }, [router, loadSettingsData]);

  const handleSaveSettings = async () => {
    setSaving(true);
    setError(null);

    try {
      await api.updateSettings(settings);
    } catch (err) {
      console.error("Failed to save settings:", err);
      setError(err instanceof Error ? err.message : "Failed to save settings");
    } finally {
      setSaving(false);
    }
  };

  const handleRefresh = () => {
    setLoading(true);
    setError(null);
    loadSettingsData();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Loading settings...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-bold text-red-500">Unable to load settings</h2>
        <p className="text-muted-foreground mt-2">{error}</p>
        <Button onClick={handleRefresh} className="mt-4">
          <RefreshCw className="h-4 w-4 mr-2" />
          Try Again
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold">Settings</h1>
          <p className="text-muted-foreground">Configure system settings and preferences</p>
        </div>
        <Button onClick={handleSaveSettings} disabled={saving} size="sm">
          <Save className={`h-4 w-4 mr-2 ${saving ? "animate-spin" : ""}`} />
          {saving ? "Saving..." : "Save Settings"}
        </Button>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="GENERAL">General</TabsTrigger>
          <TabsTrigger value="NETWORK">Network</TabsTrigger>
        </TabsList>

        {/* General Settings */}
        <TabsContent value="GENERAL" className="space-y-6">
          <div className="card-default">
            <div className="p-6 border-b border-border">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <SettingsIcon className="h-5 w-5" />
                General Settings
              </h3>
              <p className="text-sm text-muted-foreground">Configure basic system settings and preferences</p>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">System Name</label>
                  <Input
                    value={String(settings.system_name || "")}
                    onChange={(e) =>
                      setSettings((prev) => ({ ...prev, system_name: e.target.value }))
                    }
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Administrator Email</label>
                  <Input
                    type="email"
                    value={String(settings.admin_email || "")}
                    onChange={(e) =>
                      setSettings((prev) => ({ ...prev, admin_email: e.target.value }))
                    }
                  />
                </div>
              </div>
            </div>
          </div>
        </TabsContent>

        {/* Network Settings */}
        <TabsContent value="NETWORK" className="space-y-6">
          <div className="card-default">
            <div className="p-6 border-b border-border">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <Network className="h-5 w-5" />
                Network Configuration
              </h3>
              <p className="text-sm text-muted-foreground">Configure DNS and network settings</p>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">DNS Server</label>
                  <Input
                    value={String(settings.dns_server || "")}
                    onChange={(e) =>
                      setSettings((prev) => ({ ...prev, dns_server: e.target.value }))
                    }
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Bandwidth Limit (Mbps)</label>
                  <Input
                    type="number"
                    value={String(settings.bandwidth_limit || "")}
                    onChange={(e) =>
                      setSettings((prev) => ({
                        ...prev,
                        bandwidth_limit: parseInt(e.target.value) || 0,
                      }))
                    }
                  />
                </div>
              </div>
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}