import React from "react";
import "../index.css";

export default function RecentFeed({ recent }) {
  return (
    <div className="feed-box">
      <h3>Recent Login Attempts</h3>

      {recent && recent.length > 0 ? (
        recent.slice(0, 20).map((rec, idx) => {
          const classes = ["log-entry"];
          if (rec.is_blocked) {
            classes.push("blocked");
          } else if (rec.is_suspicious) {
            classes.push("suspicious-log");
          }

          return (
            <div key={idx} className={classes.join(" ")}>
              {/* <span className="timestamp">
                [{new Date(rec.timestamp * 1000).toLocaleTimeString()}]
              </span>{" "} */}
              <span className="ip">{rec.ip}</span>
              <span className="geo">{rec.geo}</span>
              <span className="user">user:{rec.user}</span>
              <span className="type">{rec.sim_type.toUpperCase()}</span>{" "}
              <span
                className={rec.result === "SUCCESS" ? "res-success" : "res-failure"}
              >
                — {rec.result}
              </span>
            </div>
          );
        })
      ) : (
        <div className="placeholder">(No events yet)</div>
      )}
    </div>
  );
}
