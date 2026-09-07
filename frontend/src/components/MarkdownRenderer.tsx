import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

export const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content, className = '' }) => {
  if (!content) return null;

  return (
    <div className={`markdown-body text-xs sm:text-sm leading-relaxed ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          strong: ({ children }) => (
            <strong className="font-bold text-slate-900">{children}</strong>
          ),
          p: ({ children }) => (
            <p className="my-1 font-medium">{children}</p>
          ),
          h1: ({ children }) => (
            <h1 className="text-base font-extrabold text-slate-900 mt-3 mb-1">{children}</h1>
          ),
          h2: ({ children }) => (
            <h2 className="text-sm font-extrabold text-slate-900 mt-3 mb-1">{children}</h2>
          ),
          h3: ({ children }) => (
            <h3 className="text-xs font-bold text-tealmed-800 mt-2 mb-1 uppercase tracking-wider">{children}</h3>
          ),
          ul: ({ children }) => (
            <ul className="my-1.5 pl-4 list-disc space-y-1 font-medium">{children}</ul>
          ),
          ol: ({ children }) => (
            <ol className="my-1.5 pl-4 list-decimal space-y-1 font-medium">{children}</ol>
          ),
          li: ({ children }) => (
            <li className="leading-snug">{children}</li>
          ),
          table: ({ children }) => (
            <div className="my-2.5 overflow-x-auto rounded-xl border border-slate-200 shadow-sm">
              <table className="min-w-full text-xs text-left text-slate-700 divide-y divide-slate-200">
                {children}
              </table>
            </div>
          ),
          thead: ({ children }) => (
            <thead className="bg-slate-100/90 font-bold text-[11px] text-slate-700 uppercase tracking-wider">
              {children}
            </thead>
          ),
          tbody: ({ children }) => (
            <tbody className="divide-y divide-slate-100 bg-white">{children}</tbody>
          ),
          tr: ({ children }) => (
            <tr className="hover:bg-slate-50/70 transition-colors">{children}</tr>
          ),
          th: ({ children }) => (
            <th className="px-3 py-2 border-r last:border-r-0 border-slate-200 font-bold">{children}</th>
          ),
          td: ({ children }) => (
            <td className="px-3 py-2 border-r last:border-r-0 border-slate-200 font-medium">{children}</td>
          ),
          code: ({ children }) => (
            <code className="bg-slate-100 text-tealmed-900 px-1.5 py-0.5 rounded text-[11px] font-mono border border-slate-200">
              {children}
            </code>
          )
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};

export default MarkdownRenderer;
