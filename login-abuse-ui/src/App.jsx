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
import { getStats, simulate } from "./services/api";

export default function App() {
  // We’ll store the stats JSON here
  const [stats, setStats] = useState({
    attempts: [],
    failures: [],
    suspicions: [],
    blocks: [],
    labels: [],
    recent: [],
  });

  // Poll getStats() every 1 second
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

    // Immediately fetch once…
    fetchAndSet();
    // Then poll every second
    const id = setInterval(fetchAndSet, 1000);

    return () => {
      isMounted = false;
      clearInterval(id);
    };
  }, []);

  // Handler for button clicks in Controls.jsx
  // We’ll pass this down to <Controls /> so it can call simulate(...)
  const handleSim = async (type) => {
    try {
      await simulate(type);
      // Optionally, we could immediately refresh stats here:
      // const fresh = await getStats();
      // setStats(fresh);
    } catch (err) {
      console.error("Simulation error:", err);
    }
  };

  return (
    <div>
      {/* 1) Header */}
      <div className="header">
        <h1>Login Abuse Tracker</h1>
        <SettingsDropdown />
      </div>

      {/* 2) Controls row, pass down handleSim so buttons actually call simulate() */}
      <Controls onSimulate={handleSim} />

      {/* 3) Stats cards: pass the live numbers */}
      <StatsCards stats={stats} />

      {/* 4) Main content with chart + feeds */}
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
