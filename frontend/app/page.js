"use client";

import { useState, useEffect } from "react";
import axios from "axios";
import io from "socket.io-client";
import ReactFlow, {
  Background,
  ReactFlowProvider,
} from "reactflow";
import "reactflow/dist/style.css";

let socket;

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

  // Use environment variable or fallback
  const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

  useEffect(() => {
    socket = io(BACKEND_URL, { transports: ["websocket"] });

    socket.on("connect", () => {
      console.log("Connected to backend:", socket.id);
    });

    socket.on("node_update", (data) => {
      setNodes((prev) => {
        const newNode = {
          id: `${prev.length}`,
          type: "boxNode",
          position: {
            x: prev.length * (nodeWidth + nodeSpacing),
            y: 0,
          },
          data: { label: data.label },
        };

        const newEdge =
          prev.length > 0
            ? {
                id: `e${prev.length - 1}-${prev.length}`,
                source: `${prev.length - 1}`,
                target: `${prev.length}`,
                animated: true,
              }
            : null;

        if (newEdge) setEdges((prevEdges) => [...prevEdges, newEdge]);

        return [...prev, newNode];
      });
    });

    return () => socket.disconnect();
  }, [BACKEND_URL]);

  const handleAnalyze = async () => {
    setNodes([]);
    setEdges([]);
    try {
      await axios.post(`${BACKEND_URL}/analyze`, {
        ticker,
        start_date: startDate,
        end_date: endDate,
      });
    } catch (err) {
      console.error("Error calling backend:", err);
      alert("Error calling backend. Check console.");
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
