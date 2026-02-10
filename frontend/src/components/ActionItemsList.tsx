import type { ActionItem } from '../types';

interface ActionItemsListProps {
  actionItems: ActionItem[];
  selectedItems: Set<number>;
  onSelectionChange: (index: number, selected: boolean) => void;
}

export default function ActionItemsList({ actionItems, selectedItems, onSelectionChange }: ActionItemsListProps) {
  if (!actionItems || actionItems.length === 0) {
    return <p className="empty-state">No action items were identified in this meeting.</p>;
  }

  return (
    <div>
      {actionItems.map((item, index) => (
        <div key={index} className="action-item">
          <label className="checkbox-label">
            <input
              type="checkbox"
              className="integration-checkbox"
              checked={selectedItems.has(index)}
              onChange={(e) => onSelectionChange(index, e.target.checked)}
            />
            <div>
              <div className="action-text">
                {item.task}
                {item.owner && <span className="owner-badge">@{item.owner}</span>}
                {item.deadline && <span className="deadline-badge">Due: {item.deadline}</span>}
              </div>
            </div>
          </label>
        </div>
      ))}
    </div>
  );
}
