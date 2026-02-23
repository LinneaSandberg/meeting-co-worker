import type { TranscriptionResult } from '../types';

export function exportToMarkdown(results: TranscriptionResult): void {
  const { insights, transcript } = results;
  const date = new Date().toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });

  const lines: string[] = [];

  lines.push(`# Meeting Notes`);
  lines.push(`*Exported on ${date}*`);
  lines.push('');

  if (insights.summary) {
    lines.push('## Summary');
    lines.push(insights.summary);
    lines.push('');
  }

  if (insights.decisions && insights.decisions.length > 0) {
    lines.push('## Decisions Made');
    for (const d of insights.decisions) {
      lines.push(`- **${d.decision}**`);
      if (d.context) {
        lines.push(`  *${d.context}*`);
      }
    }
    lines.push('');
  }

  if (insights.action_items && insights.action_items.length > 0) {
    lines.push('## Action Items');
    for (const item of insights.action_items) {
      const parts = [`- [ ] ${item.task}`];
      if (item.owner) parts.push(`**${item.owner}**`);
      if (item.deadline) parts.push(`Due: ${item.deadline}`);
      lines.push(parts.join(' — '));
    }
    lines.push('');
  }

  if (insights.open_questions && insights.open_questions.length > 0) {
    lines.push('## Open Questions');
    for (const q of insights.open_questions) {
      lines.push(`- **${q.question}**`);
      if (q.context) {
        lines.push(`  *${q.context}*`);
      }
    }
    lines.push('');
  }

  lines.push('---');
  lines.push('');
  lines.push('## Full Transcript');
  lines.push('');
  lines.push(transcript);

  const content = lines.join('\n');
  const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' });
  const url = URL.createObjectURL(blob);

  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = `meeting-notes-${new Date().toISOString().slice(0, 10)}.md`;
  anchor.click();

  URL.revokeObjectURL(url);
}
