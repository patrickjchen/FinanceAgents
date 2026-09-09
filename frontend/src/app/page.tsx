"use client";
import React, { useState } from "react";
import dynamic from "next/dynamic";

// 动态导入组件，禁用SSR以避免hydration错误
const Sidebar = dynamic(() => import("../components/Sidebar"), { ssr: false });
const Dashboard = dynamic(() => import("../components/Dashboard"), { ssr: false });
const Analysis = dynamic(() => import("../components/Analysis"), { ssr: false });
const Settings = dynamic(() => import("../components/Settings"), { ssr: false });

export default function Home() {
  const [activeTab, setActiveTab] = useState("dashboard");

  const renderContent = () => {
    switch (activeTab) {
      case "dashboard":
        return <Dashboard />;
      case "analysis":
        return <Analysis />;
      case "settings":
        return <Settings />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <div className="flex min-h-screen bg-gray-100">
      <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />
      <div className="flex-1 ml-20">
        {renderContent()}
      </div>
    </div>
  );
}
