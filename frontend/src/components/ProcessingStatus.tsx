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

        <div className="step-progress">
          {STEPS.map((s, i) => {
            const isCompleted = i < currentIndex;
            const isCurrent = i === currentIndex;
            const className = `step-item${isCompleted ? ' completed' : ''}${isCurrent ? ' active' : ''}`;

            return (
              <div key={s.key} className={className}>
                <div className="step-circle">
                  {isCompleted ? '\u2713' : i + 1}
                </div>
                <span className="step-label">{s.label}</span>
              </div>
            );
          })}
        </div>

        <p id="processing-detail" className="step-elapsed">
          Elapsed: {minutes > 0 ? `${minutes}m ` : ''}{seconds}s
        </p>
      </div>
    </section>
  );
}
