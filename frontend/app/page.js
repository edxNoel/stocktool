"use client";

import { useState, useEffect } from "react";
import axios from "axios";
import ReactFlow, {
  Background,
  ReactFlowProvider,
} from "reactflow";
import "reactflow/dist/style.css";

function BoxNode({ data }) {
  return (
    <div
      style={{
        width: 200,
        minHeight: 60,
        padding: "10px",
        border: "2px solid #0070f3",
        borderRadius: 8,
        background: "white",
        boxShadow: "0px 2px 5px rgba(0,0,0,0.2)",
        wordWrap: "break-word",
        whiteSpace: "pre-wrap",
      }}
    >
      {data.label}
    </div>
  );
}

export default function Home() {
  const [ticker, setTicker] = useState("AAPL");
  const [startDate, setStartDate] = useState("2025-01-01");
  const [endDate, setEndDate] = useState("2025-01-10");
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);

  const nodeWidth = 220;
  const nodeSpacing = 50;

  // Direct backend URL (no /api)
  const BACKEND_URL = "stocktool.vercel.app";

  const handleAnalyze = async () => {
    setNodes([]);
    setEdges([]);

    // Use /analyze directly on backend
    const analyzeUrl = `${BACKEND_URL.replace(/\/$/, "")}/analyze`;

    console.log("Calling backend at:", analyzeUrl);

    try {
      await axios.post(analyzeUrl, {
        ticker,
        start_date: startDate,
        end_date: endDate,
      });
      console.log("Request sent successfully");
    } catch (err) {
      console.error("Error calling backend:", err);
      alert(
        "Error calling backend. Make sure the backend is deployed and CORS allows your frontend."
      );
    }
  };

  const nodeTypes = { boxNode: BoxNode };

  return (
    <div style={{ height: "100vh", padding: "1rem" }}>
      <h1>AI Stock Analyzer</h1>

      <div style={{ marginBottom: "1rem" }}>
        <label>
          Ticker:
          <input
            value={ticker}
            onChange={(e) => setTicker(e.target.value.toUpperCase())}
          />
        </label>
        <label>
          Start Date:
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
          />
        </label>
        <label>
          End Date:
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
          />
        </label>
        <button onClick={handleAnalyze}>Analyze</button>
      </div>

      <ReactFlowProvider>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          fitView
          style={{ width: "100%", height: "70%" }}
        >
          <Background />
        </ReactFlow>
      </ReactFlowProvider>
    </div>
  );
}
