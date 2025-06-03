// src/components/StatsCards.jsx
import React from "react";
import "../index.css";

export default function StatsCards({ stats }) {
  // Simple helper to sum an array (or return 0 if empty)
  const sum = (arr) => (Array.isArray(arr) ? arr.reduce((a, b) => a + b, 0) : 0);

  return (
    <div className="stats-cards">
      <div className="card">
        <h3>Suspicious Events</h3>
        <p><span className="card-number">{sum(stats.suspicions)}</span></p>
      </div>
      <div className="card">
        <h3>Recent Attempts</h3>
        <p><span className="card-number">{sum(stats.attempts)}</span></p>
      </div>
      <div className="card">
        <h3>Failures</h3>
        <p><span className="card-number">{sum(stats.failures)}</span></p>
      </div>
      <div className="card">
        <h3>Blocks</h3>
        <p><span className="card-number">{sum(stats.blocks)}</span></p>
      </div>
    </div>
  );
}
