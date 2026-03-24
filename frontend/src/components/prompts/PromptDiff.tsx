/**
 * Side-by-side diff viewer for comparing two prompt versions.
 * Uses LCS (longest common subsequence) for correct diff output.
 */

import type { PromptVersion } from '../../types';

interface PromptDiffProps {
  left: PromptVersion;
  right: PromptVersion;
  onClose: () => void;
}

interface DiffLine {
  text: string;
  type: 'same' | 'added' | 'removed' | 'empty';
}

/**
 * Compute LCS-based diff between two arrays of lines.
 * Returns paired left/right lines with type annotations.
 */
function computeDiff(a: string[], b: string[]): { left: DiffLine[]; right: DiffLine[] } {
  const m = a.length;
  const n = b.length;

  // Build LCS table
  const dp: number[][] = Array.from({ length: m + 1 }, () => Array(n + 1).fill(0));
  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      dp[i][j] = a[i - 1] === b[j - 1] ? dp[i - 1][j - 1] + 1 : Math.max(dp[i - 1][j], dp[i][j - 1]);
    }
  }

  // Backtrack to build diff
  const left: DiffLine[] = [];
  const right: DiffLine[] = [];
  let i = m;
  let j = n;

  const result: Array<{ type: 'same' | 'added' | 'removed'; lineA?: string; lineB?: string }> = [];

  while (i > 0 || j > 0) {
    if (i > 0 && j > 0 && a[i - 1] === b[j - 1]) {
      result.push({ type: 'same', lineA: a[i - 1], lineB: b[j - 1] });
      i--;
      j--;
    } else if (j > 0 && (i === 0 || dp[i][j - 1] >= dp[i - 1][j])) {
      result.push({ type: 'added', lineB: b[j - 1] });
      j--;
    } else {
      result.push({ type: 'removed', lineA: a[i - 1] });
      i--;
    }
  }

  result.reverse();

  for (const entry of result) {
    if (entry.type === 'same') {
      left.push({ text: entry.lineA!, type: 'same' });
      right.push({ text: entry.lineB!, type: 'same' });
    } else if (entry.type === 'removed') {
      left.push({ text: entry.lineA!, type: 'removed' });
      right.push({ text: '', type: 'empty' });
    } else {
      left.push({ text: '', type: 'empty' });
      right.push({ text: entry.lineB!, type: 'added' });
    }
  }

  return { left, right };
}

function DiffPanel({ title: label, lines }: { title: string; lines: DiffLine[] }) {
  return (
    <div className="diff-panel">
      <div className="diff-panel__header">{label}</div>
      <pre className="diff-panel__content">
        {lines.map((line, i) => (
          <div key={i} className={`diff-line diff-line--${line.type}`}>
            {line.text || '\u00A0'}
          </div>
        ))}
      </pre>
    </div>
  );
}

export default function PromptDiff({ left, right, onClose }: PromptDiffProps) {
  const { left: leftLines, right: rightLines } = computeDiff(
    left.content.split('\n'),
    right.content.split('\n'),
  );

  return (
    <div className="experiment-form-overlay" onClick={onClose}>
      <div className="diff-container" onClick={(e) => e.stopPropagation()}>
        <div className="diff-header">
          <h2>Compare Versions</h2>
          <button className="btn-text" onClick={onClose}>Close</button>
        </div>
        <div className="diff-panels">
          <DiffPanel title={`v${left.version}`} lines={leftLines} />
          <DiffPanel title={`v${right.version}`} lines={rightLines} />
        </div>
      </div>
    </div>
  );
}
