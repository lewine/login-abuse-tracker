// src/components/Controls.jsx
import React from "react";
import "../index.css";

export default function Controls({ onSimulate, onReset }) {
  return (
    <div className="controls">
      <button onClick={() => onSimulate("normal")}>Run Simulation</button>
      <button onClick={() => onSimulate("bruteforce")}>Brute Force Attack</button>
      <button onClick={() => onSimulate("geohop")}>Geo-Hop Attack</button>
      <button onClick={() => onSimulate("credstuff")}>Credential Stuffing</button>
      <button onClick={onReset} className="reset-button">Reset</button>
    </div>
  );
}
