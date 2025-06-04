// src/App.jsx

import React, { useState, useEffect } from "react";
import "./index.css";

import Controls from "./components/Controls";
import StatsCards from "./components/StatsCards";
import TrafficChart from "./components/TrafficChart";
import RecentFeed from "./components/RecentFeed";
import BlockedFeed from "./components/BlockedFeed";
import SettingsDropdown from "./components/SettingsDropdown";

// Import our API helpers
import { getStats, simulate, reset } from "./services/api";

export default function App() {
  // --------------------------------------------------------------------------
  // 0) Stats polling (unchanged)
  // --------------------------------------------------------------------------
  const [stats, setStats] = useState({
    attempts: [],
    failures: [],
    suspicions: [],
    blocks: [],
    labels: [],
    recent: [],
  });

  useEffect(() => {
    let isMounted = true;

    async function fetchAndSet() {
      try {
        const fresh = await getStats();
        if (isMounted) {
          setStats(fresh);
        }
      } catch (err) {
        console.error("Failed to fetch stats:", err);
      }
    }

    // Fetch immediately, then every second
    fetchAndSet();
    const id = setInterval(fetchAndSet, 1000);

    return () => {
      isMounted = false;
      clearInterval(id);
    };
  }, []);

  // --------------------------------------------------------------------------
  // 1) Attack defaults state:
  //    We store a "defaults" object for each of the four sim types.
  // --------------------------------------------------------------------------
  const [attackDefaults, setAttackDefaults] = useState({
    normal: {
      delay: 0.5,
      iterations: 30,
      failure_rate: 0.2,
      workers: 3,
    },
    bruteforce: {
      delay: 0.5,
      iterations: 30,
      failure_rate: 0.0, // (ignored by bruteforce internally)
      workers: 5,
    },
    geohop: {
      delay: 1.0,
      iterations: 10,
      failure_rate: 0.2, // (ignored by geohop internally)
      workers: 1,
    },
    credstuff: {
      delay: 1.0,
      iterations: 10,
      failure_rate: 0.0,
      workers: 1,
    },
  });

  // --------------------------------------------------------------------------
  // 2) Revised handleSim: when Controls calls onSimulate(type),
  //    we look up attackDefaults[type], then call simulate(...)
  // --------------------------------------------------------------------------
  const handleSim = async (type) => {
    try {
      // Pull out the correct defaults for this sim type:
      const { delay, iterations, failure_rate, workers } = attackDefaults[type];

      // Call simulate(...) with all five parameters
      await simulate(type, delay, iterations, failure_rate, workers);

      // (Optional) Immediately refresh stats if you like:
      // const fresh = await getStats();
      // setStats(fresh);
    } catch (err) {
      console.error("Simulation error:", err);
    }
  };


  // 3) NEW: handleReset
  const handleReset = async () => {
    try {
      await reset();            // call POST /reset
      const fresh = await getStats(); // reload the empty stats
      setStats(fresh);
    } catch (err) {
      console.error("Reset error:", err);
    }
  };

  // --------------------------------------------------------------------------
  // 3) JSX render
  // --------------------------------------------------------------------------
  return (
    <div className="app-container">
      {/* ------------------ Header ------------------ */}
      <header className="header">
        <h1>Login Abuse Tracker</h1>

        {/*
          Pass both attackDefaults and setAttackDefaults into SettingsDropdown
          so it can display & edit each type's { delay, iterations, failure_rate, workers }.
        */}
        <SettingsDropdown
          attackDefaults={attackDefaults}
          setAttackDefaults={setAttackDefaults}
        />
      </header>

      {/* ------------------ Controls Row ------------------ */}
      {/*
        Controls.jsx expects a prop `onSimulate(type)`
        When a button is clicked, it calls handleSim("normal"), etc.
      */}
      <Controls onSimulate={handleSim} onReset={handleReset}/>

      {/* ------------------ Stats Cards ------------------ */}
      <StatsCards stats={stats} />

      {/* ------------------ Main Content ------------------ */}
      <div className="main-content">
        <TrafficChart stats={stats} />

        <div className="feed-container">
          <RecentFeed recent={stats.recent} />
          <BlockedFeed />
        </div>
      </div>
    </div>
  );
}
