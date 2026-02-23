import { useState, useEffect } from 'react';
import type { TranscriptionResult, IntegrationStatus, SelectedActionItem, SelectedQuestion, IntegrationResults } from '../types';
import ActionItemsList from './ActionItemsList';
import QuestionsList from './QuestionsList';
import IntegrationControls from './IntegrationControls';
import ResultsModal from './ResultsModal';
import { getIntegrationStatus, createIntegrations } from '../services/client';
import { exportToMarkdown } from '../services/exportMarkdown';

interface ResultsDisplayProps {
  results: TranscriptionResult;
  onReset: () => void;
}

export default function ResultsDisplay({ results, onReset }: ResultsDisplayProps) {
  const [integrationStatus, setIntegrationStatus] = useState<IntegrationStatus | null>(null);
  const [selectedActionItems, setSelectedActionItems] = useState<Set<number>>(new Set());
  const [selectedQuestions, setSelectedQuestions] = useState<Map<number, { github: boolean; calendar: boolean }>>(new Map());
  const [integrationLoading, setIntegrationLoading] = useState(false);
  const [integrationResults, setIntegrationResults] = useState<IntegrationResults | null>(null);
  const [showModal, setShowModal] = useState(false);

  useEffect(() => {
    getIntegrationStatus().then(setIntegrationStatus).catch(console.error);
  }, []);

  const handleActionItemSelection = (index: number, selected: boolean) => {
    setSelectedActionItems(prev => {
      const newSet = new Set(prev);
      if (selected) {
        newSet.add(index);
      } else {
        newSet.delete(index);
      }
      return newSet;
    });
  };

  const handleQuestionSelection = (index: number, type: 'github' | 'calendar', selected: boolean) => {
    setSelectedQuestions(prev => {
      const newMap = new Map(prev);
      const current = newMap.get(index) || { github: false, calendar: false };
      newMap.set(index, { ...current, [type]: selected });
      return newMap;
    });
  };

  const getSelectedCount = (): number => {
    let count = selectedActionItems.size;

    selectedQuestions.forEach(selection => {
      if (selection.github) count++;
      if (selection.calendar) count++;
    });

    return count;
  };

  const handleCreateIntegrations = async () => {
    setIntegrationLoading(true);

    try {
      const actionItems: SelectedActionItem[] = [];
      const openQuestions: SelectedQuestion[] = [];

      // Collect selected action items
      selectedActionItems.forEach(index => {
        const item = results.insights.action_items?.[index];
        if (item) {
          actionItems.push({
            ...item,
            create_github: true
          });
        }
      });

      // Collect selected questions
      selectedQuestions.forEach((selection, index) => {
        const question = results.insights.open_questions?.[index];
        if (question && (selection.github || selection.calendar)) {
          openQuestions.push({
            ...question,
            create_github: selection.github,
            create_calendar: selection.calendar
          });
        }
      });

      const intResults = await createIntegrations(actionItems, openQuestions);
      setIntegrationResults(intResults);
      setShowModal(true);

      // Reset selections after successful creation
      setSelectedActionItems(new Set());
      setSelectedQuestions(new Map());
    } catch (error) {
      console.error('Failed to create integrations:', error);
      alert('Failed to create integrations. Please check the console for details.');
    } finally {
      setIntegrationLoading(false);
    }
  };

  const { insights } = results;

  return (
    <section id="results-section">
      <div className="results-header">
        <h2>Meeting Insights</h2>
        <div className="results-header-actions">
          <button onClick={() => exportToMarkdown(results)} className="btn-export">Export as Markdown</button>
          <button onClick={onReset} className="btn-secondary">Process Another File</button>
        </div>
      </div>

      {insights.summary && (
        <div className="result-card">
          <h3>Summary</h3>
          <p>{insights.summary}</p>
        </div>
      )}

      {insights.decisions && insights.decisions.length > 0 && (
        <div className="result-card">
          <h3>Decisions Made</h3>
          {insights.decisions.map((decision, index) => (
            <div key={index} className="decision-item">
              <div className="decision-text">{decision.decision}</div>
              {decision.context && (
                <div className="context-text">→ {decision.context}</div>
              )}
            </div>
          ))}
        </div>
      )}

      {insights.action_items && insights.action_items.length > 0 && (
        <div className="result-card">
          <h3>Action Items</h3>
          <ActionItemsList
            actionItems={insights.action_items}
            selectedItems={selectedActionItems}
            onSelectionChange={handleActionItemSelection}
          />
        </div>
      )}

      {insights.open_questions && insights.open_questions.length > 0 && (
        <div className="result-card">
          <h3>Open Questions</h3>
          <QuestionsList
            questions={insights.open_questions}
            selectedQuestions={selectedQuestions}
            onSelectionChange={handleQuestionSelection}
          />
        </div>
      )}

      <IntegrationControls
        selectedCount={getSelectedCount()}
        onCreateClick={handleCreateIntegrations}
        loading={integrationLoading}
        integrationStatus={integrationStatus}
      />

      <details className="transcript-details">
        <summary>View Full Transcript</summary>
        <div className="transcript-content">{results.transcript}</div>
      </details>

      <ResultsModal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        results={integrationResults}
      />
    </section>
  );
}
