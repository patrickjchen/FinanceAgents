"use client";
import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  Sparkles,
  MessageCircle,
  FileText,
  TrendingUp,
  Landmark,
  Search,
  Bot,
  AlertTriangle,
  type LucideIcon,
} from 'lucide-react';

/** One agent's block as returned by POST /query: {response: {AgentName: {summary}}}. */
export type AgentBlocks = { [agent: string]: { summary: string } };

interface AgentMeta {
  label: string;
  icon: LucideIcon;
  /** Tailwind classes for the card accent (border + header tint). */
  accent: string;
}

const AGENT_META: Record<string, AgentMeta> = {
  FinalSummary: { label: 'Summary', icon: Sparkles, accent: 'border-blue-300 bg-blue-50' },
  RedditAgent: { label: 'Reddit sentiment', icon: MessageCircle, accent: 'border-orange-200 bg-orange-50' },
  FinanceAgent: { label: 'Internal filings', icon: FileText, accent: 'border-emerald-200 bg-emerald-50' },
  RAGAgent: { label: 'Retrieved passages', icon: Search, accent: 'border-teal-200 bg-teal-50' },
  YahooAgent: { label: 'Market data', icon: TrendingUp, accent: 'border-violet-200 bg-violet-50' },
  SecAgent: { label: 'SEC filings', icon: Landmark, accent: 'border-amber-200 bg-amber-50' },
  GeneralAgent: { label: 'Answer', icon: Bot, accent: 'border-gray-200 bg-gray-50' },
  error: { label: 'Error', icon: AlertTriangle, accent: 'border-red-300 bg-red-50' },
};

const FALLBACK_META: AgentMeta = { label: 'Agent', icon: Bot, accent: 'border-gray-200 bg-gray-50' };

function metaFor(agent: string): AgentMeta {
  return AGENT_META[agent] ?? { ...FALLBACK_META, label: agent.replace(/Agent$/, '') };
}

const Markdown: React.FC<{ text: string }> = ({ text }) => (
  <div
    className="prose prose-sm max-w-none text-gray-800
      prose-headings:font-semibold prose-headings:text-gray-900 prose-headings:mt-4 prose-headings:mb-2
      prose-h1:text-lg prose-h2:text-base prose-h3:text-sm prose-h4:text-sm prose-h4:uppercase prose-h4:tracking-wide prose-h4:text-gray-600
      prose-p:my-2 prose-p:leading-relaxed
      prose-li:my-0.5 prose-ul:my-2 prose-ol:my-2
      prose-strong:text-gray-900
      prose-hr:my-4
      prose-table:text-xs"
  >
    <ReactMarkdown remarkPlugins={[remarkGfm]}>{text}</ReactMarkdown>
  </div>
);

interface CardProps {
  agent: string;
  summary: string;
  /** Final summary renders expanded and emphasised; agent cards start collapsed. */
  primary?: boolean;
  defaultOpen?: boolean;
}

const AgentCard: React.FC<CardProps> = ({ agent, summary, primary = false, defaultOpen = false }) => {
  const { label, icon: Icon, accent } = metaFor(agent);

  if (primary) {
    return (
      <section className={`rounded-xl border ${accent} shadow-sm`}>
        <header className="flex items-center gap-2 px-4 py-2.5 border-b border-blue-200/70">
          <Icon size={16} className="text-blue-600" />
          <h2 className="text-sm font-semibold tracking-wide text-blue-900 uppercase">{label}</h2>
        </header>
        <div className="px-4 py-3 bg-white rounded-b-xl">
          <Markdown text={summary} />
        </div>
      </section>
    );
  }

  return (
    <details className={`group rounded-lg border ${accent}`} open={defaultOpen}>
      <summary className="flex items-center gap-2 px-3 py-2 cursor-pointer select-none list-none">
        <Icon size={15} className="text-gray-600 shrink-0" />
        <span className="text-sm font-medium text-gray-800">{label}</span>
        <span className="ml-auto text-xs text-gray-400 group-open:hidden">show</span>
        <span className="ml-auto text-xs text-gray-400 hidden group-open:inline">hide</span>
      </summary>
      <div className="px-3 py-2 border-t border-gray-200/70 bg-white rounded-b-lg">
        <Markdown text={summary} />
      </div>
    </details>
  );
};

/**
 * Renders a full backend reply. The final summary (when present) goes on top,
 * expanded; the per-agent sections follow as collapsible cards in the order
 * the backend returned them.
 */
const AgentResponse: React.FC<{ blocks: AgentBlocks }> = ({ blocks }) => {
  const entries = Object.entries(blocks).filter(([, v]) => v && typeof v.summary === 'string');
  const final = entries.find(([k]) => k === 'FinalSummary');
  const others = entries.filter(([k]) => k !== 'FinalSummary');
  // Without a final summary (general questions, errors) show everything expanded.
  const expandOthers = !final;

  if (entries.length === 0) {
    return <p className="text-sm text-gray-500 italic">No answer returned.</p>;
  }

  return (
    <div className="space-y-3">
      {final && <AgentCard agent={final[0]} summary={final[1].summary} primary />}
      {others.length > 0 && (
        <div className="space-y-2">
          {final && (
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide px-1">Agent details</p>
          )}
          {others.map(([agent, { summary }]) => (
            <AgentCard key={agent} agent={agent} summary={summary} defaultOpen={expandOthers} />
          ))}
        </div>
      )}
    </div>
  );
};

export default AgentResponse;
