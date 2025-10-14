    // frontend/app/socket.js
import { io } from "socket.io-client";

export const socket = io("http://localhost:8000", {
  autoConnect: false, // we'll connect manually
});
