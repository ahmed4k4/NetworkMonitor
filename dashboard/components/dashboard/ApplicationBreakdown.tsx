"use client";

import { DeviceApplication } from "@/lib/types";
import { getConfidenceDisplay, isSharedCDN, getSharedCDNWarning, formatEvidence } from "@/lib/confidence";
import { Badge } from "@/components/ui/badge";
import { AlertCircle, Info, ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";
import { formatBytes } from "@/lib/utils";

interface ApplicationBreakdownProps {
  applications: DeviceApplication[];
  totalBytes: number;
}

export default function ApplicationBreakdown({ applications, totalBytes }: ApplicationBreakdownProps) {
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [hovered, setHovered] = useState<string | null>(null);

  const toggleExpand = (name: string) => {
    setExpanded(prev => {
      const next = new Set(prev);
      if (next.has(name)) next.delete(name);
      else next.add(name);
      return next;
    });
  };

  const isExpanded = (name: string) => expanded.has(name);

  if (!applications.length) {
    return (
      <div className="text-center py-8">
        <p className="text-muted-foreground">No application data available</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {applications.map((app) => {
        const percentage = totalBytes > 0 ? ((app.total_bytes / totalBytes) * 100).toFixed(1) : "0";
        const confDisplay = getConfidenceDisplay(app.confidence);
        const isCDN = isSharedCDN(app.name, app.category);
        
        return (
          <div key={app.name} className="border rounded-lg overflow-hidden">
            <div className="p-4 bg-gray-50 border-b">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3 flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium truncate">{app.name}</span>
                    {isCDN && (
                      <span
                        className="inline-flex items-center justify-center w-5 h-5 text-orange-500 rounded-full hover:bg-orange-100 cursor-help transition-colors"
                        onMouseEnter={() => setHovered(app.name)}
                        onMouseLeave={() => setHovered(null)}
                        title={getSharedCDNWarning(app.name)}
                      >
                        <AlertCircle className="h-4 w-4" />
                      </span>
                    )}
                  </div>
                  <Badge variant="outline" className="text-xs">{app.category}</Badge>
                  <Badge 
                    variant="outline" 
                    className={`${confDisplay.bgColor} ${confDisplay.color} text-xs`}
                  >
                    {confDisplay.icon} {confDisplay.label}
                  </Badge>
                </div>
                <div className="flex items-center gap-3 text-right">
                  <div className="text-sm">
                    <div className="font-mono font-medium">{formatBytes(app.total_bytes)}</div>
                    <div className="text-muted-foreground">{percentage}% of total</div>
                  </div>
                  <button
                    onClick={() => toggleExpand(app.name)}
                    className="p-1 hover:bg-gray-200 rounded transition-colors"
                    aria-label={isExpanded(app.name) ? "Collapse" : "Expand"}
                  >
                    {isExpanded(app.name) ? (
                      <ChevronUp className="h-4 w-4" />
                    ) : (
                      <ChevronDown className="h-4 w-4" />
                    )}
                  </button>
                </div>
              </div>
              
              <div className="mt-3 h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-500 transition-all duration-300"
                  style={{ width: `${Math.min(100, parseFloat(percentage))}%` }}
                ></div>
              </div>
            </div>

            {isExpanded(app.name) && (
              <div className="p-4 space-y-3 bg-white border-t">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <div className="text-muted-foreground">Download</div>
                    <div className="font-mono font-medium">{formatBytes(app.download_bytes)}</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">Upload</div>
                    <div className="font-mono font-medium">{formatBytes(app.upload_bytes)}</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">Connections</div>
                    <div className="font-mono font-medium">{app.connections}</div>
                  </div>
                </div>

                {formatEvidence(app.evidence) && (
                  <div className="pt-3 border-t">
                    <div className="flex items-center gap-2 text-sm font-medium mb-2">
                      <Info className="h-4 w-4 text-blue-500" />
                      Evidence
                    </div>
                    <ul className="space-y-1 text-xs font-mono">
                      <li className="text-muted-foreground">{formatEvidence(app.evidence)}</li>
                    </ul>
                  </div>
                )}
              </div>
            )}

            {/* Tooltip for CDN warning */}
            {hovered === app.name && isCDN && (
              <div className="fixed z-50 px-3 py-2 bg-orange-900 text-white text-sm rounded shadow-lg pointer-events-none"
                style={{ 
                  top: '50%', 
                  left: '50%',
                  transform: 'translate(-50%, -120%)'
                }}
              >
                {getSharedCDNWarning(app.name)}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
