"use client";
import React, { useState } from 'react';

interface Tab {
  label: string;
  content: React.ReactNode;
}

interface AgentResultTabsProps {
  tabs: Tab[];
}

const AgentResultTabs: React.FC<AgentResultTabsProps> = ({ tabs }) => {
  const [active, setActive] = useState(0);

  return (
    <div className="w-full max-w-2xl mx-auto my-4">
      <div className="flex border-b">
        {tabs.map((tab, idx) => (
          <button
            key={tab.label}
            className={`px-4 py-2 -mb-px border-b-2 text-sm font-medium transition-colors ${active === idx ? 'border-[var(--color-primary)] text-[var(--color-primary)]' : 'border-transparent text-gray-500 dark:text-gray-300'}`}
            onClick={() => setActive(idx)}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div className="p-4 bg-white dark:bg-[var(--color-background)] border rounded-b shadow">
        {tabs[active]?.content}
      </div>
    </div>
  );
};

export default AgentResultTabs; 