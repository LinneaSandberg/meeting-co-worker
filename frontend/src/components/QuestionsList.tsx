import type { OpenQuestion } from '../types';

interface QuestionsListProps {
  questions: OpenQuestion[];
  selectedQuestions: Map<number, { github: boolean; calendar: boolean }>;
  onSelectionChange: (index: number, type: 'github' | 'calendar', selected: boolean) => void;
}

export default function QuestionsList({ questions, selectedQuestions, onSelectionChange }: QuestionsListProps) {
  if (!questions || questions.length === 0) {
    return <p className="empty-state">No open questions were identified in this meeting.</p>;
  }

  return (
    <div>
      {questions.map((question, index) => {
        const selection = selectedQuestions.get(index) || { github: false, calendar: false };

        return (
          <div key={index} className="question-item">
            <div className="question-text">{question.question}</div>
            {question.context && (
              <div className="context-text">→ {question.context}</div>
            )}
            <div style={{ marginTop: '8px', display: 'flex', gap: '16px' }}>
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  className="integration-checkbox"
                  checked={selection.github}
                  onChange={(e) => onSelectionChange(index, 'github', e.target.checked)}
                />
                <span style={{ marginLeft: '6px' }}>Create GitHub Issue</span>
              </label>
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  className="integration-checkbox"
                  checked={selection.calendar}
                  onChange={(e) => onSelectionChange(index, 'calendar', e.target.checked)}
                />
                <span style={{ marginLeft: '6px' }}>Create Calendar Event</span>
              </label>
            </div>
          </div>
        );
      })}
    </div>
  );
}
