"use client";

import React, { useState, useEffect } from "react";
import { DataManagementContent } from "./DataManagementContent";

export default function DataManagementPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <DataManagementContent />
    </div>
  );
}