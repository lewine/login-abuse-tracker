import React, { useState, useEffect } from "react";
import { getBlocklist } from "../services/api";
import "../index.css";

export default function BlockedFeed() {
  const [entries, setEntries] = useState([]);

  useEffect(() => {
    let isMounted = true;

    async function fetchList() {
      try {
        const data = await getBlocklist(); 
        if (isMounted) setEntries(data);
      } catch (err) {
        console.error("Error loading blocklist:", err);
      }
    }

    fetchList();
    const intervalId = setInterval(fetchList, 1000);

    return () => {
      isMounted = false;
      clearInterval(intervalId);
    };
  }, []);

  return (
    <div className="feed-box">
      <h3>Blocklist</h3>
      {entries.length > 0 ? (
        entries.map((entry, idx) => (
          <div key={idx} className="log-entry blocked-log">
            <span className="block-type">{entry.type}:</span>
            <span className="block-val">{entry.value}</span>
          </div>
        ))
      ) : (
        <div className="placeholder">(No blocks yet)</div>
      )}
    </div>
  );
}
