// AgentGraph.js
"use client";
import React from "react";
import ReactFlow, { MiniMap, Controls } from "reactflow";
import "reactflow/dist/style.css";

export default function AgentGraph({ nodes, edges }) {
  return (
    <div style={{ width: "100%", height: "80vh" }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        fitView
        nodeTypes={{}}
        defaultEdgeOptions={{ animated: true }}
        nodesDraggable={true}
        nodesConnectable={false}
        snapToGrid={true}
        snapGrid={[15, 15]}
      >
        <MiniMap />
        <Controls />
      </ReactFlow>
    </div>
  );
}
