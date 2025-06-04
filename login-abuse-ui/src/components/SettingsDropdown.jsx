// src/components/SettingsDropdown.jsx
import React, { useState, useEffect, useRef } from "react";
import "../index.css";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:5000";

export default function SettingsDropdown({ attackDefaults, setAttackDefaults }) {
  const [open, setOpen] = useState(false);

  //
  // 1) Defense thresholds local state
  //
  const [defenseLocal, setDefenseLocal] = useState({
    brute_threshold: 5,
    brute_window: 5,
    geohop_threshold: 2,
    cred_threshold: 2,
    cred_window: 20,
  });
  const [loadingDefense, setLoadingDefense] = useState(false);
  const [defenseError, setDefenseError] = useState(null);

  //
  // 2) Attack defaults local copy (from parent)
  //
  const [attackLocal, setAttackLocal] = useState({
    normal: { ...attackDefaults.normal },
    bruteforce: { ...attackDefaults.bruteforce },
    geohop: { ...attackDefaults.geohop },
    credstuff: { ...attackDefaults.credstuff },
  });
  const [attackError, setAttackError] = useState(null);

  const containerRef = useRef(null);

  // --------------------------------------------------------------------------
  // Fetch defense thresholds from backend whenever dropdown opens
  // --------------------------------------------------------------------------
  useEffect(() => {
    async function fetchDefense() {
      setLoadingDefense(true);
      setDefenseError(null);
      try {
        const res = await fetch(`${API_BASE}/defense-thresholds`);
        if (!res.ok) throw new Error(`Error ${res.status}`);
        const data = await res.json();
        setDefenseLocal({
          brute_threshold: data.brute_threshold,
          brute_window: data.brute_window,
          geohop_threshold: data.geohop_threshold,
          cred_threshold: data.cred_threshold,
          cred_window: data.cred_window,
        });
      } catch (err) {
        setDefenseError(`Could not load defense defaults: ${err.message}`);
      } finally {
        setLoadingDefense(false);
      }
    }

    if (open) {
      fetchDefense();
      // Reset attackLocal to match the current attackDefaults from parent
      setAttackLocal({
        normal: { ...attackDefaults.normal },
        bruteforce: { ...attackDefaults.bruteforce },
        geohop: { ...attackDefaults.geohop },
        credstuff: { ...attackDefaults.credstuff },
      });
    }
  }, [open, attackDefaults]);

  // --------------------------------------------------------------------------
  // Close panel when clicking outside
  // --------------------------------------------------------------------------
  useEffect(() => {
    function handleClickOutside(e) {
      if (open && containerRef.current && !containerRef.current.contains(e.target)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [open]);

  // --------------------------------------------------------------------------
  // Defense field change handler
  // --------------------------------------------------------------------------
  function onDefenseChange(e) {
    const { name, value } = e.target;
    setDefenseLocal((prev) => ({ ...prev, [name]: Number(value) }));
  }

  // --------------------------------------------------------------------------
  // Attack field change handler
  // --------------------------------------------------------------------------
  function onAttackFieldChange(type, fieldName, value) {
    setAttackLocal((prev) => ({
      ...prev,
      [type]: {
        ...prev[type],
        [fieldName]: Number(value),
      },
    }));
  }

  // --------------------------------------------------------------------------
  // Single “Save” that writes both defense AND attack defaults
  // --------------------------------------------------------------------------
  async function onSaveAll() {
    // 1) POST defenseLocal to /defense-thresholds
    setDefenseError(null);
    try {
      const res = await fetch(`${API_BASE}/defense-thresholds`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(defenseLocal),
      });
      if (!res.ok) {
        throw new Error(`Error ${res.status}`);
      }
    } catch (err) {
      setDefenseError(`Failed to save defense: ${err.message}`);
      // Even if defense fails, we still proceed to update attack defaults
    }

    // 2) Lift attackLocal up to parent
    try {
      setAttackDefaults({
        normal: { ...attackLocal.normal },
        bruteforce: { ...attackLocal.bruteforce },
        geohop: { ...attackLocal.geohop },
        credstuff: { ...attackLocal.credstuff },
      });
    } catch (err) {
      setAttackError("Failed to save attack defaults");
      console.error(err);
      return;
    }

    // If we reach here, close the dropdown
    setOpen(false);
  }

  // --------------------------------------------------------------------------
  // Utility to render one attack field (hides failure_rate for brute/geohop)
  // --------------------------------------------------------------------------
  const renderAttackField = (type, label, fieldName, min = 0, step = 1) => {
    if ((type === "bruteforce" || type === "geohop") && fieldName === "failure_rate") {
      return null;
    }
    return (
      <div className="sd-field" key={`${type}_${fieldName}`}>
        <label>
          {label}:
          <input
            type="number"
            step={step}
            name={`${type}_${fieldName}`}
            value={attackLocal[type][fieldName]}
            onChange={(e) => onAttackFieldChange(type, fieldName, e.target.value)}
            min={min}
          />
        </label>
      </div>
    );
  };

  return (
    <div className="settings-dropdown" ref={containerRef}>
      <button className="settings-button" onClick={() => setOpen((prev) => !prev)}>
        ⚙️
      </button>

      {open && (
        <div className="dropdown-panel wide">
          <h4>Settings</h4>
          <div className="columns-container">
            {/* ======== Column 1: Defense ======== */}
            <div className="column defense-col">
              <h5>Defense</h5>
              {loadingDefense ? (
                <div>Loading…</div>
              ) : (
                <>
                  <div className="sd-field">
                    <label>
                      Brute Threshold:
                      <input
                        type="number"
                        name="brute_threshold"
                        value={defenseLocal.brute_threshold}
                        onChange={onDefenseChange}
                        min={1}
                      />
                    </label>
                  </div>
                  <div className="sd-field">
                    <label>
                      Brute Window (s):
                      <input
                        type="number"
                        name="brute_window"
                        value={defenseLocal.brute_window}
                        onChange={onDefenseChange}
                        min={1}
                      />
                    </label>
                  </div>
                  <div className="sd-field">
                    <label>
                      GeoHop Threshold (s):
                      <input
                        type="number"
                        name="geohop_threshold"
                        value={defenseLocal.geohop_threshold}
                        onChange={onDefenseChange}
                        min={1}
                      />
                    </label>
                  </div>
                  <div className="sd-field">
                    <label>
                      Cred Threshold:
                      <input
                        type="number"
                        name="cred_threshold"
                        value={defenseLocal.cred_threshold}
                        onChange={onDefenseChange}
                        min={1}
                      />
                    </label>
                  </div>
                  <div className="sd-field">
                    <label>
                      Cred Window (s):
                      <input
                        type="number"
                        name="cred_window"
                        value={defenseLocal.cred_window}
                        onChange={onDefenseChange}
                        min={1}
                      />
                    </label>
                  </div>
                  {defenseError && <div className="error">{defenseError}</div>}
                </>
              )}
            </div>

            {/* ======== Column 2: Normal ======== */}
            <div className="column attack-col">
              <h5>Normal</h5>
              {renderAttackField("normal", "Delay (s)", "delay", 0, 0.1)}
              {renderAttackField("normal", "Iterations", "iterations", 1, 1)}
              {renderAttackField("normal", "Failure Rate", "failure_rate", 0, 0.01)}
              {renderAttackField("normal", "Workers", "workers", 1, 1)}
            </div>

            {/* ======== Column 3: Bruteforce ======== */}
            <div className="column attack-col">
              <h5>Bruteforce</h5>
              {renderAttackField("bruteforce", "Delay (s)", "delay", 0, 0.1)}
              {renderAttackField("bruteforce", "Iterations", "iterations", 1, 1)}
              {renderAttackField("bruteforce", "Workers", "workers", 1, 1)}
              {/* failure_rate hidden */}
            </div>

            {/* ======== Column 4: GeoHop ======== */}
            <div className="column attack-col">
              <h5>GeoHop</h5>
              {renderAttackField("geohop", "Delay (s)", "delay", 0, 0.1)}
              {renderAttackField("geohop", "Iterations", "iterations", 1, 1)}
              {renderAttackField("geohop", "Workers", "workers", 1, 1)}
              {/* failure_rate hidden */}
            </div>

            {/* ======== Column 5: CredStuff ======== */}
            <div className="column attack-col">
              <h5>CredStuff</h5>
              {renderAttackField("credstuff", "Delay (s)", "delay", 0, 0.1)}
              {renderAttackField("credstuff", "Iterations", "iterations", 1, 1)}
              {renderAttackField("credstuff", "Failure Rate", "failure_rate", 0, 0.01)}
              {renderAttackField("credstuff", "Workers", "workers", 1, 1)}
            </div>
          </div>

          {/* ======== Single Save / Cancel row ======== */}
          <div className="sd-actions">
            <button className="save-button" onClick={onSaveAll}>
              Save
            </button>
            <button className="cancel-button" onClick={() => setOpen(false)}>
              Cancel
            </button>
          </div>

          {attackError && <div className="error">{attackError}</div>}
        </div>
      )}
    </div>
  );
}
