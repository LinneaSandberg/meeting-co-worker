import { useState } from 'react';
import FileUpload from './components/FileUpload';
import ProcessingStatus from './components/ProcessingStatus';
import ResultsDisplay from './components/ResultsDisplay';
import { uploadFile, subscribeToJob } from './services/client';
import type { TranscriptionResult, ProcessingStep } from './types';
import { AppState } from './types';

function App() {
  const [state, setState] = useState<AppState>(AppState.UPLOAD);
  const [results, setResults] = useState<TranscriptionResult | null>(null);
  const [error, setError] = useState<string>('');
  const [currentStep, setCurrentStep] = useState<ProcessingStep>('uploading');

  const handleUpload = async (file: File) => {
    setState(AppState.PROCESSING);
    setCurrentStep('uploading');
    setError('');

    try {
      const { job_id } = await uploadFile(file);
      setCurrentStep('transcribing');

      subscribeToJob(job_id, {
        onStep: (step) => {
          setCurrentStep(step);
        },
        onComplete: (result) => {
          setResults(result);
          setState(AppState.RESULTS);
        },
        onError: (errorMsg) => {
          setError(errorMsg);
          setState(AppState.ERROR);
        }
      });
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    } catch (err: any) {
      console.error('Upload error:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to process file');
      setState(AppState.ERROR);
    }
  };

  const handleReset = () => {
    setState(AppState.UPLOAD);
    setResults(null);
    setError('');
    setCurrentStep('uploading');
  };

  return (
    <div className="container">
      <header>
        <h1>Meeting Copilot</h1>
        <p className="subtitle">Transcribe meetings and extract key insights automatically</p>
      </header>

      <main>
        {state === AppState.UPLOAD && <FileUpload onUpload={handleUpload} />}
        {state === AppState.PROCESSING && <ProcessingStatus step={currentStep} />}
        {state === AppState.RESULTS && results && (
          <ResultsDisplay results={results} onReset={handleReset} />
        )}
        {state === AppState.ERROR && (
          <section id="error-section">
            <div className="error-container">
              <svg className="error-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <h2>Error Processing File</h2>
              <p id="error-message">{error}</p>
              <button onClick={handleReset} className="btn-primary">Try Again</button>
            </div>
          </section>
        )}
      </main>

      <footer>
        <p>Powered by ElevenLabs Scribe v2 & Claude</p>
      </footer>
    </div>
  );
}

export default App;
