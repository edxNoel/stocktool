// app/AgentGraph.tsx
"use client";

import React, { useEffect, useState, useCallback } from "react";
import ReactFlow, {
  MiniMap,
  Controls,
  Node,
  Edge,
  addEdge,
  Connection,
  EdgeChange,
  NodeChange,
  applyNodeChanges,
  applyEdgeChanges,
} from "reactflow";
import "reactflow/dist/style.css";
import { io, Socket } from "socket.io-client";

interface NodeUpdate {
  label: string;
}

const AgentGraph: React.FC = () => {
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [socket, setSocket] = useState<Socket | null>(null);

  // Initialize Socket.IO
  useEffect(() => {
    const newSocket = io("http://localhost:8000");
    setSocket(newSocket);

    newSocket.on("connect", () => {
      console.log("Connected to Socket.IO server");
    });

    newSocket.on("node_update", (data: NodeUpdate) => {
      const newNode: Node = {
        id: (nodes.length + 1).toString(),
        position: { x: Math.random() * 600, y: Math.random() * 400 },
        data: { label: data.label },
      };
      setNodes((nds) => [...nds, newNode]);
    });

    return () => {
      newSocket.disconnect();
    };
  }, [nodes.length]);

  // Handle node & edge changes
  const onNodesChange = useCallback(
    (changes: NodeChange[]) => setNodes((nds) => applyNodeChanges(changes, nds)),
    []
  );
  const onEdgesChange = useCallback(
    (changes: EdgeChange[]) => setEdges((eds) => applyEdgeChanges(changes, eds)),
    []
  );
  const onConnect = useCallback(
    (connection: Connection) => setEdges((eds) => addEdge(connection, eds)),
    []
  );

  return (
    <div style={{ width: "100%", height: "90vh" }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        fitView
      >
        <MiniMap />
        <Controls />
      </ReactFlow>
    </div>
  );
};

export default AgentGraph;
