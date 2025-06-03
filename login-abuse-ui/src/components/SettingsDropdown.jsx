// src/components/SettingsDropdown.jsx
import React, { useState, useEffect } from "react";
import "../index.css";
import { getThresholds, setThresholds } from "../services/api";

export default function SettingsDropdown() {
  const [open, setOpen] = useState(false);
  const [thresholds, setThresholdsState] = useState({
    bruteforce_limit: 5,
    geohop_interval: 60,
    credstuff_limit: 10,
  });

  // Fetch current thresholds once on mount
  useEffect(() => {
    async function fetchThresh() {
      try {
        const data = await getThresholds();
        setThresholdsState(data);
      } catch (err) {
        console.error("Error loading thresholds:", err);
      }
    }
    fetchThresh();
  }, []);

  const handleSave = async (e) => {
    e.preventDefault();
    try {
      await setThresholds(thresholds);
      setOpen(false);
    } catch (err) {
      console.error("Error saving thresholds:", err);
    }
  };

  return (
    <div style={{ position: "relative" }}>
      <span className="settings-cog" onClick={() => setOpen((o) => !o)}>
        ⚙️
      </span>
      {open && (
        <form
          onSubmit={handleSave}
          style={{
            position: "absolute",
            top: "36px",
            right: 0,
            background: "#222",
            padding: "12px",
            borderRadius: "6px",
            zIndex: 10,
            width: "200px",
          }}
        >
          <label style={{ display: "block", marginBottom: "8px" }}>
            Brute-Force Limit:
            <input
              type="number"
              value={thresholds.bruteforce_limit}
              onChange={(e) =>
                setThresholdsState({ ...thresholds, bruteforce_limit: +e.target.value })
              }
              style={{ marginTop: "4px", width: "100%" }}
            />
          </label>
          <label style={{ display: "block", marginBottom: "8px" }}>
            Geo-Hop Interval:
            <input
              type="number"
              value={thresholds.geohop_interval}
              onChange={(e) =>
                setThresholdsState({ ...thresholds, geohop_interval: +e.target.value })
              }
              style={{ marginTop: "4px", width: "100%" }}
            />
          </label>
          <label style={{ display: "block", marginBottom: "12px" }}>
            Cred-Stuff Limit:
            <input
              type="number"
              value={thresholds.credstuff_limit}
              onChange={(e) =>
                setThresholdsState({ ...thresholds, credstuff_limit: +e.target.value })
              }
              style={{ marginTop: "4px", width: "100%" }}
            />
          </label>
          <button
            type="submit"
            style={{
              background: "#3498db",
              color: "#fff",
              border: "none",
              padding: "8px",
              borderRadius: "4px",
              width: "100%",
              cursor: "pointer",
            }}
          >
            Save
          </button>
        </form>
      )}
    </div>
  );
}
