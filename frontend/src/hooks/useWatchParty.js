import { useEffect, useRef, useState, useCallback } from 'react';

/**
 * Custom hook for managing WebSocket connection to a watch party room.
 *
 * @param {string} roomCode - The room code to connect to
 * @param {string} sessionId - The user's session ID
 * @param {string} username - The user's display name
 * @returns {object} - Connection state and methods
 */
export function useWatchParty(roomCode, sessionId, username) {
  const ws = useRef(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isHost, setIsHost] = useState(false);
  const [videoUrl, setVideoUrl] = useState('');
  const [chatMessages, setChatMessages] = useState([]);
  const [syncState, setSyncState] = useState({ currentTime: 0, isPlaying: false });
  const [error, setError] = useState(null);
  const [roomClosed, setRoomClosed] = useState(false);

  // Latency measurement with averaging
  const latencyRef = useRef(0);
  const latencySamplesRef = useRef([]);
  const pingTimestampRef = useRef(null);

  useEffect(() => {
    if (!roomCode || !sessionId || !username) return;

    // Determine WebSocket URL based on environment
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/ws/watch/${roomCode}/`;

    ws.current = new WebSocket(wsUrl);

    ws.current.onopen = () => {
      setIsConnected(true);
      setError(null);

      // Send join message with session_id and username
      ws.current.send(
        JSON.stringify({
          type: 'join',
          session_id: sessionId,
          username: username,
        })
      );

      // Start measuring latency - rapid initial pings, then slow down
      measureLatency();
      // Quick initial pings to calibrate
      setTimeout(measureLatency, 500);
      setTimeout(measureLatency, 1000);
      setTimeout(measureLatency, 2000);
    };

    const measureLatency = () => {
      if (ws.current?.readyState === WebSocket.OPEN) {
        pingTimestampRef.current = performance.now();
        ws.current.send(JSON.stringify({ type: 'ping' }));
      }
    };

    // Periodically measure latency (every 2 seconds for accuracy)
    const latencyInterval = setInterval(measureLatency, 2000);

    ws.current.onclose = (event) => {
      setIsConnected(false);
      if (!event.wasClean && !roomClosed) {
        setError('Connection lost. Please refresh the page.');
      }
    };

    ws.current.onerror = () => {
      setError('Failed to connect to watch party.');
    };

    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('WebSocket message received:', data);

      switch (data.type) {
        case 'pong':
          // Calculate round-trip time and use rolling average
          if (pingTimestampRef.current) {
            const rtt = performance.now() - pingTimestampRef.current;
            const oneWayMs = rtt / 2;

            // Keep last 5 samples for averaging
            latencySamplesRef.current.push(oneWayMs);
            if (latencySamplesRef.current.length > 5) {
              latencySamplesRef.current.shift();
            }

            // Calculate average latency
            const avgLatency = latencySamplesRef.current.reduce((a, b) => a + b, 0) / latencySamplesRef.current.length;
            latencyRef.current = avgLatency / 1000; // Convert to seconds

            console.log(`Latency: ${Math.round(avgLatency)}ms (avg of ${latencySamplesRef.current.length} samples)`);
          }
          break;

        case 'role':
          console.log('Setting role - isHost:', data.is_host, 'videoUrl:', data.video_url);
          setIsHost(data.is_host);
          setVideoUrl(data.video_url);
          break;

        case 'sync':
          // Compensate for network latency - add latency to catch up to where host actually is
          const compensatedTime = data.current_time + latencyRef.current;
          setSyncState({
            currentTime: compensatedTime,
            isPlaying: data.is_playing,
          });
          break;

        case 'chat':
          setChatMessages((prev) => [
            ...prev,
            {
              username: data.username,
              message: data.message,
              timestamp: new Date(),
            },
          ]);
          break;

        case 'user_joined':
          setChatMessages((prev) => [
            ...prev,
            {
              type: 'system',
              message: `${data.username} joined the party`,
              timestamp: new Date(),
            },
          ]);
          break;

        case 'user_left':
          setChatMessages((prev) => [
            ...prev,
            {
              type: 'system',
              message: `${data.username} left the party`,
              timestamp: new Date(),
            },
          ]);
          break;

        case 'room_closed':
          setRoomClosed(true);
          setError(data.message);
          break;

        case 'error':
          console.warn('Server error:', data.message);
          break;

        default:
          console.log('Unknown message type:', data.type);
      }
    };

    return () => {
      clearInterval(latencyInterval);
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [roomCode, sessionId, username, roomClosed]);

  /**
   * Send playback sync update (host only).
   */
  const sendSync = useCallback((currentTime, isPlaying) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(
        JSON.stringify({
          type: 'sync',
          current_time: currentTime,
          is_playing: isPlaying,
        })
      );
    }
  }, []);

  /**
   * Send a chat message.
   */
  const sendChat = useCallback((message) => {
    if (ws.current?.readyState === WebSocket.OPEN && message.trim()) {
      ws.current.send(
        JSON.stringify({
          type: 'chat',
          message: message.trim(),
        })
      );
    }
  }, []);

  return {
    isConnected,
    isHost,
    videoUrl,
    syncState,
    chatMessages,
    error,
    roomClosed,
    sendSync,
    sendChat,
  };
}
