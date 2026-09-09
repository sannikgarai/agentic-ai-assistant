
import React from "react";

function SourceCitation({
  sources = [],
}) {
  if (!sources || sources.length === 0) {
    return null;
  }

  const openSource = (source) => {
    if (source.url) {
      window.open(
        source.url,
        "_blank",
        "noopener,noreferrer"
      );
    }
  };

  return (
    <div className="source-citation">

      <div className="source-header">
        <span>📚</span>
        <strong>Sources</strong>
      </div>

      <div className="source-list">

        {sources.map((source, index) => {

          const title =
            source.title ||
            source.name ||
            `Government Document ${index + 1}`;

          return (
            <div
              key={source.id || index}
              className={`source-card ${
                source.url ? "clickable" : ""
              }`}
              onClick={() => openSource(source)}
            >

              <div className="source-number">
                {index + 1}
              </div>

              <div className="source-info">

                <strong>{title}</strong>

                {source.document && (
                  <span>
                    📄 {source.document}
                  </span>
                )}

                {source.page && (
                  <span>
                    Page {source.page}
                  </span>
                )}

                {source.category && (
                  <span>
                    Category: {source.category}
                  </span>
                )}

                {source.excerpt && (
                  <p>
                    "{source.excerpt}"
                  </p>
                )}

              </div>

              {source.url && (
                <div className="source-open">
                  ↗
                </div>
              )}

            </div>
          );
        })}

      </div>

    </div>
  );
}

export default SourceCitation;
