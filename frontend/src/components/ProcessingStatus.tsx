export default function ProcessingStatus() {
  return (
    <section id="processing-section">
      <div className="processing-container">
        <div className="spinner"></div>
        <h2 id="processing-status">Processing your file...</h2>
        <p id="processing-detail">Transcribing audio and extracting insights</p>
      </div>
    </section>
  );
}
