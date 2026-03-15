import { useState, useEffect } from 'react';
import type { ProcessingStep } from '../types';

const STEPS: { key: ProcessingStep; label: string }[] = [
  { key: 'transcribing', label: 'Transcribing Audio' },
  { key: 'extracting', label: 'Extracting Insights' },
  { key: 'complete', label: 'Done' },
];

function getStepIndex(step: ProcessingStep): number {
  if (step === 'uploading') return -1;
  return STEPS.findIndex((s) => s.key === step);
}

export default function ProcessingStatus({ step }: { step: ProcessingStep }) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const start = Date.now();
    const interval = setInterval(() => {
      setElapsed(Math.floor((Date.now() - start) / 1000));
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const currentIndex = getStepIndex(step);
  const minutes = Math.floor(elapsed / 60);
  const seconds = elapsed % 60;

  return (
    <section id="processing-section">
      <div className="processing-container">
        <div className="spinner"></div>
        <h2 id="processing-status">Processing your meeting...</h2>

        <div style={{ display: 'flex', justifyContent: 'center', gap: '2rem', margin: '1.5rem 0' }}>
          {STEPS.map((s, i) => {
            const isCompleted = i < currentIndex;
            const isCurrent = i === currentIndex;

            return (
              <div
                key={s.key}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: '0.5rem',
                  opacity: isCompleted || isCurrent ? 1 : 0.4,
                }}
              >
                <div
                  style={{
                    width: '2rem',
                    height: '2rem',
                    borderRadius: '50%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '0.875rem',
                    fontWeight: 'bold',
                    background: isCompleted
                      ? '#22c55e'
                      : isCurrent
                      ? '#3b82f6'
                      : '#374151',
                    color: '#fff',
                  }}
                >
                  {isCompleted ? '\u2713' : i + 1}
                </div>
                <span
                  style={{
                    fontSize: '0.875rem',
                    fontWeight: isCurrent ? 600 : 400,
                    color: isCurrent ? '#3b82f6' : undefined,
                  }}
                >
                  {s.label}
                </span>
              </div>
            );
          })}
        </div>

        <p id="processing-detail" style={{ color: '#9ca3af', fontSize: '0.875rem' }}>
          Elapsed: {minutes > 0 ? `${minutes}m ` : ''}{seconds}s
        </p>
      </div>
    </section>
  );
}
