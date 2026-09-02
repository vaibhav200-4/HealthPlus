import React from 'react';

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

export const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content, className = '' }) => {
  if (!content) return null;

  const lines = content.split('\n');
  const blocks: React.ReactNode[] = [];
  let inTable = false;
  let tableHeaders: string[] = [];
  let tableRows: string[][] = [];

  const renderInline = (text: string): React.ReactNode => {
    // Splitting by **bold** text
    const parts = text.split(/(\*\*.*?\*\*)/g);
    return parts.map((part, idx) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={idx} className="font-extrabold text-slate-900">{part.slice(2, -2)}</strong>;
      }
      return part;
    });
  };

  const flushTable = (key: string) => {
    if (tableHeaders.length > 0 || tableRows.length > 0) {
      blocks.push(
        <div key={key} className="my-3 overflow-x-auto rounded-2xl border border-slate-200">
          <table className="min-w-full text-xs text-left text-slate-700 divide-y divide-slate-200">
            {tableHeaders.length > 0 && (
              <thead className="bg-slate-100/80 font-bold uppercase text-[10px] text-slate-600 tracking-wider">
                <tr>
                  {tableHeaders.map((th, i) => (
                    <th key={i} className="px-3.5 py-2.5 border-r last:border-r-0 border-slate-200">{th}</th>
                  ))}
                </tr>
              </thead>
            )}
            <tbody className="divide-y divide-slate-100 bg-white">
              {tableRows.map((row, rIdx) => (
                <tr key={rIdx} className="hover:bg-slate-50/60">
                  {row.map((cell, cIdx) => (
                    <td key={cIdx} className="px-3.5 py-2 border-r last:border-r-0 border-slate-200 font-medium">{renderInline(cell)}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
      tableHeaders = [];
      tableRows = [];
    }
    inTable = false;
  };

  lines.forEach((line, idx) => {
    const trimmed = line.trim();

    // Table row detection (| col | col |)
    if (trimmed.startsWith('|') && trimmed.endsWith('|')) {
      const cells = trimmed.slice(1, -1).split('|').map(c => c.trim());
      // Skip markdown divider row |---|---|
      if (cells.every(c => c.replace(/[-:\s]/g, '') === '')) {
        return;
      }
      if (!inTable) {
        inTable = true;
        tableHeaders = cells;
      } else {
        tableRows.push(cells);
      }
      return;
    } else if (inTable) {
      flushTable(`table-${idx}`);
    }

    if (!trimmed) {
      return;
    }

    // Headers
    if (trimmed.startsWith('### ')) {
      blocks.push(
        <h4 key={idx} className="text-xs font-extrabold text-tealmed-900 mt-4 mb-1.5 flex items-center gap-1.5 border-b border-tealmed-100 pb-1 uppercase tracking-wider">
          {renderInline(trimmed.slice(4))}
        </h4>
      );
    } else if (trimmed.startsWith('## ')) {
      blocks.push(
        <h3 key={idx} className="text-xs sm:text-sm font-extrabold text-slate-900 mt-4 mb-2 flex items-center gap-1.5 border-b border-slate-200 pb-1">
          {renderInline(trimmed.slice(3))}
        </h3>
      );
    } else if (trimmed.startsWith('# ')) {
      blocks.push(
        <h2 key={idx} className="text-sm sm:text-base font-extrabold text-slate-900 mt-5 mb-2">
          {renderInline(trimmed.slice(2))}
        </h2>
      );
    } else if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
      // Bullet list items
      blocks.push(
        <div key={idx} className="flex items-start gap-2 text-xs text-slate-700 my-1 font-medium pl-1">
          <span className="w-1.5 h-1.5 rounded-full bg-tealmed-500 mt-1.5 flex-shrink-0" />
          <span>{renderInline(trimmed.slice(2))}</span>
        </div>
      );
    } else if (/^\d+\.\s/.test(trimmed)) {
      // Numbered list items
      const numMatch = trimmed.match(/^(\d+)\.\s(.*)/);
      if (numMatch) {
        blocks.push(
          <div key={idx} className="flex items-start gap-2 text-xs text-slate-700 my-1 font-medium pl-1">
            <span className="font-bold text-tealmed-700 flex-shrink-0">{numMatch[1]}.</span>
            <span>{renderInline(numMatch[2])}</span>
          </div>
        );
      }
    } else {
      // Standard paragraph
      blocks.push(
        <p key={idx} className="text-xs leading-relaxed text-slate-700 my-1 font-medium">
          {renderInline(trimmed)}
        </p>
      );
    }
  });

  if (inTable) {
    flushTable('table-end');
  }

  return <div className={`space-y-1 ${className}`}>{blocks}</div>;
};
