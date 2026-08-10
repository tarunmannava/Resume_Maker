import { KeywordMatch } from "../lib/api";

export function KeywordTable({
  title,
  items,
  onToggle,
  selectedItems = [],
}: {
  title: string;
  items: KeywordMatch[];
  onToggle?: (term: string) => void;
  selectedItems?: string[];
}) {
  if (!items.length) {
    return (
      <section className="card small-card">
        <h3>{title}</h3>
        <p className="muted">None</p>
      </section>
    );
  }

  return (
    <section className="card small-card">
      <h3>{title}</h3>
      <div className="keyword-list">
        {items.slice(0, 20).map((item) => (
          <div
            className={`keyword ${item.risk} ${onToggle ? "interactive" : ""}`}
            key={`${item.term}-${item.status}`}
            onClick={() => onToggle?.(item.term)}
          >
            <div className="keyword-core">
              {onToggle && (
                <input
                  type="checkbox"
                  checked={selectedItems.includes(item.term)}
                  readOnly
                />
              )}
              <div>
                <strong>{item.term}</strong>
                <span>
                  {item.category} · {item.status}
                </span>
              </div>
            </div>
            <em>{item.risk}</em>
          </div>
        ))}
      </div>
    </section>
  );
}
