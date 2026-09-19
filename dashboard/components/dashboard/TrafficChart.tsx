"use client";

import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

type TrafficPoint = {
  time: string;
  download: number;
  upload: number;
};

type Props = {
  data: TrafficPoint[];
};

export default function TrafficChart({
  data,
}: Props) {
  return (
    <div className="h-[320px] w-full">

      <ResponsiveContainer
        width="100%"
        height="100%"
      >

        <AreaChart data={data}>

          <CartesianGrid strokeDasharray="3 3" />

          <XAxis dataKey="time" />

          <YAxis />

          <Tooltip />

          <Area
            type="monotone"
            dataKey="download"
            name="Download"
            fillOpacity={0.15}
            strokeWidth={2}
          />

          <Area
            type="monotone"
            dataKey="upload"
            name="Upload"
            fillOpacity={0.15}
            strokeWidth={2}
          />

        </AreaChart>

      </ResponsiveContainer>

    </div>
  );
}