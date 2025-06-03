// src/components/Controls.jsx
import React from "react";
import "../index.css";

export default function Controls({ onSimulate }) {
  return (
    <div className="controls">
      <button onClick={() => onSimulate("normal")}>Run Simulation</button>
      <button onClick={() => onSimulate("bruteforce")}>Brute Force Attack</button>
      <button onClick={() => onSimulate("geohop")}>Geo-Hop Attack</button>
      <button onClick={() => onSimulate("credstuff")}>Credential Stuffing</button>
    </div>
  );
}
