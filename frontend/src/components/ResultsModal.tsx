import type { IntegrationResults } from '../types';

interface ResultsModalProps {
  isOpen: boolean;
  onClose: () => void;
  results: IntegrationResults | null;
}

export default function ResultsModal({ isOpen, onClose, results }: ResultsModalProps) {
  if (!isOpen || !results) return null;

  const allResults = [
    ...results.results.github_issues,
    ...results.results.calendar_events
  ];

  return (
    <div className="modal" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>Integration Results</h3>
          <button className="modal-close" onClick={onClose}>&times;</button>
        </div>
        <div className="modal-body">
          {allResults.length === 0 ? (
            <p>No items were created.</p>
          ) : (
            allResults.map((result, index) => (
              <div
                key={index}
                className={`integration-result-item ${result.error ? 'integration-result-error' : 'integration-result-success'}`}
              >
                <div style={{ fontWeight: 600, marginBottom: '4px' }}>
                  {result.type === 'action_item' ? '📌 Action Item' : '❓ Open Question'}
                </div>
                <div>{result.title}</div>

                {result.error ? (
                  <div style={{ color: '#e53e3e', marginTop: '8px' }}>
                    Error: {result.error}
                  </div>
                ) : (
                  <div style={{ marginTop: '8px' }}>
                    {result.url && (
                      <a href={result.url} target="_blank" rel="noopener noreferrer" className="result-link">
                        {result.issue_number ? `View Issue #${result.issue_number}` : 'View Calendar Event'} →
                      </a>
                    )}
                    {result.attendees && result.attendees.length > 0 && (
                      <div style={{ fontSize: '0.9rem', color: '#718096', marginTop: '4px' }}>
                        Attendees: {result.attendees.join(', ')}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
