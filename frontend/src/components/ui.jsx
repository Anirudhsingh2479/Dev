import React from "react";

export function Panel({ title, icon, children }) {
  return (
    <article className="panel">
      <h2>{icon}{title}</h2>
      {children}
    </article>
  );
}

export function Metric({ label, value }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
