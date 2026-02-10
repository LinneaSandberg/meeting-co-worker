import type { IntegrationStatus } from '../types';

interface IntegrationControlsProps {
  selectedCount: number;
  onCreateClick: () => void;
  loading: boolean;
  integrationStatus: IntegrationStatus | null;
}

export default function IntegrationControls({
  selectedCount,
  onCreateClick,
  loading,
  integrationStatus
}: IntegrationControlsProps) {
  if (!integrationStatus || (!integrationStatus.github_enabled && !integrationStatus.calendar_enabled)) {
    return (
      <div className="integration-section">
        <div className="config-notice-warning">
          <h3>Integrations Not Configured</h3>
          <p>To create GitHub issues or calendar events, please configure your integrations in the .env file.</p>
          <p>See the README for setup instructions.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="integration-section">
      <div className="integration-header">
        <h3>Create Tickets & Events</h3>
        <p className="integration-subtitle">Select items to create GitHub issues or calendar events</p>
      </div>

      {integrationStatus.github_enabled && (
        <div className="config-notice-success">
          GitHub: Connected to {integrationStatus.github_repo}
        </div>
      )}

      {integrationStatus.calendar_enabled && (
        <div className="config-notice-success">
          Google Calendar: Connected ({integrationStatus.calendar_type})
        </div>
      )}

      <div className="integration-actions">
        <button
          id="create-integrations-btn"
          className="btn-primary"
          onClick={onCreateClick}
          disabled={selectedCount === 0 || loading}
        >
          {loading ? 'Creating...' : 'Create Selected Items'}
        </button>
        <span className="selected-count">{selectedCount} items selected</span>
      </div>
    </div>
  );
}
