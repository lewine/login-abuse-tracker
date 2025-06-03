import React, { useEffect, useRef } from "react";
import Chart from "chart.js/auto";
import "chartjs-adapter-date-fns";
import "../index.css";    

export default function TrafficChart({ stats }) {
  const canvasRef = useRef(null);
  const chartRef  = useRef(null);

  useEffect(() => {
    if (!canvasRef.current) return;
    const ctx = canvasRef.current.getContext("2d");

    chartRef.current = new Chart(ctx, {
      type: "line",
      data: {
        labels: (stats.labels || []).map((ts) => new Date(ts * 1000)),
        datasets: [
          { label: "Attempts",   data: stats.attempts   || [], borderColor: "#888", fill: false },
          { label: "Failures",   data: stats.failures   || [], borderColor: "#e74c3c", fill: false },
          { label: "Suspicions", data: stats.suspicions || [], borderColor: "#f1c40f", fill: false },
          { label: "Blocks",     data: stats.blocks     || [], borderColor: "#3498db", fill: false },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false, 
        scales: {
          x: {
            type: "time",
            time: {
              unit: "second",
              tooltipFormat: "HH:mm:ss",
              displayFormats: { second: "HH:mm:ss" },
            },
            grid: { color: "#333" },
            ticks: { color: "#ccc" },
          },
          y: {
            beginAtZero: true,
            grid: { color: "#333" },
            ticks: { color: "#ccc" },
          },
        },
        plugins: { legend: { labels: { color: "#eee" } } },
      },
    });

    return () => {
      chartRef.current?.destroy();
    };
  }, []); 

  useEffect(() => {
    const chart = chartRef.current;
    if (!chart) return;

    chart.data.labels = (stats.labels || []).map((ts) => new Date(ts * 1000));
    chart.data.datasets[0].data = stats.attempts   || [];
    chart.data.datasets[1].data = stats.failures   || [];
    chart.data.datasets[2].data = stats.suspicions || [];
    chart.data.datasets[3].data = stats.blocks     || [];
    chart.update({ duration: 300 });
  }, [stats]);

  return (
    <div className="chart-container">
      <h3>Live Login Traffic</h3>
      <canvas ref={canvasRef} className="chart-canvas" />
    </div>
  );
}
