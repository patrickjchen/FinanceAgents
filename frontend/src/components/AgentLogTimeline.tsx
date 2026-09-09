"use client";
import React from 'react';

interface LogItem {
  time: string;
  message: string;
}

interface AgentLogTimelineProps {
  logs: LogItem[];
}

const AgentLogTimeline: React.FC<AgentLogTimelineProps> = ({ logs }) => {
  return (
    <div className="w-full max-w-2xl mx-auto my-4">
      <div className="text-sm font-bold text-[var(--color-primary)] mb-2">Query Process</div>
      <ol className="relative border-l border-[var(--color-primary)]">
        {logs.map((log, idx) => (
          <li key={idx} className="mb-6 ml-4">
            <div className="absolute w-3 h-3 bg-[var(--color-primary)] rounded-full -left-1.5 border border-white dark:border-gray-900" />
            <time className="mb-1 text-xs font-normal leading-none text-gray-400">{log.time}</time>
            <div className="text-sm text-gray-700 dark:text-gray-200">{log.message}</div>
          </li>
        ))}
      </ol>
    </div>
  );
};

export default AgentLogTimeline; 