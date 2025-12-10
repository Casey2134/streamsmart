import { useRef, useEffect, useState, useCallback } from 'react';
import { useWatchParty } from '../hooks/useWatchParty';
import ChatBox from './ChatBox';

/**
 * Extract YouTube video ID from various URL formats.
 */
function getYouTubeId(url) {
  if (!url) return null;
  const match = url.match(
    /(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&?/]+)/
  );
  return match ? match[1] : null;
}

/**
 * Main watch party room component with synchronized video playback and chat.
 */
function WatchRoom({ roomCode, sessionId, username }) {
  const playerRef = useRef(null);
  const containerRef = useRef(null);
  const [playerReady, setPlayerReady] = useState(false);
  const isLocalActionRef = useRef(false);

  const {
    isConnected,
    isHost,
    videoUrl,
    syncState,
    chatMessages,
    error,
    roomClosed,
    sendSync,
    sendChat,
  } = useWatchParty(roomCode, sessionId, username);

  const videoId = getYouTubeId(videoUrl);

  // Load YouTube IFrame API
  useEffect(() => {
    if (window.YT) return;

    const tag = document.createElement('script');
    tag.src = 'https://www.youtube.com/iframe_api';
    const firstScript = document.getElementsByTagName('script')[0];
    firstScript.parentNode.insertBefore(tag, firstScript);
  }, []);

  // Initialize YouTube player when API is ready and we have a video ID
  useEffect(() => {
    if (!videoId || !containerRef.current) return;

    const initPlayer = () => {
      if (playerRef.current) {
        playerRef.current.destroy();
      }

      playerRef.current = new window.YT.Player(containerRef.current, {
        videoId,
        playerVars: {
          autoplay: 0,
          controls: isHost ? 1 : 0,
          disablekb: isHost ? 0 : 1,
          modestbranding: 1,
          rel: 0,
        },
        events: {
          onReady: () => {
            console.log('YouTube player ready');
            setPlayerReady(true);
          },
          onStateChange: (event) => {
            if (!isHost || isLocalActionRef.current) return;

            const currentTime = playerRef.current.getCurrentTime();

            if (event.data === window.YT.PlayerState.PLAYING) {
              sendSync(currentTime, true);
            } else if (event.data === window.YT.PlayerState.PAUSED) {
              sendSync(currentTime, false);
            }
          },
        },
      });
    };

    if (window.YT && window.YT.Player) {
      initPlayer();
    } else {
      window.onYouTubeIframeAPIReady = initPlayer;
    }

    return () => {
      if (playerRef.current) {
        playerRef.current.destroy();
        playerRef.current = null;
      }
    };
  }, [videoId, isHost, sendSync]);

  // Initial sync when player becomes ready (viewers only)
  const initialSyncDone = useRef(false);
  useEffect(() => {
    if (isHost || !playerReady || !playerRef.current || initialSyncDone.current) return;

    // Small delay to ensure YouTube player is fully initialized
    const timer = setTimeout(() => {
      const player = playerRef.current;
      if (!player) return;

      try {
        initialSyncDone.current = true;
        isLocalActionRef.current = true;

        // Seek to current position
        if (syncState.currentTime > 0) {
          player.seekTo(syncState.currentTime, true);
        }

        // Play if host is playing
        if (syncState.isPlaying) {
          player.playVideo();
        }

        setTimeout(() => {
          isLocalActionRef.current = false;
        }, 500);
      } catch (e) {
        console.error('Initial sync error:', e);
      }
    }, 500);

    return () => clearTimeout(timer);
  }, [isHost, playerReady, syncState.currentTime, syncState.isPlaying]);

  // Ongoing sync for viewers (after initial sync)
  useEffect(() => {
    if (isHost || !playerReady || !playerRef.current || !initialSyncDone.current) return;

    const player = playerRef.current;

    try {
      const currentTime = player.getCurrentTime() || 0;
      const diff = syncState.currentTime - currentTime;
      const absDiff = Math.abs(diff);

      // Hard seek if difference > 0.5 seconds
      if (absDiff > 0.5) {
        isLocalActionRef.current = true;
        player.seekTo(syncState.currentTime, true);
        player.setPlaybackRate(1.0);
        setTimeout(() => {
          isLocalActionRef.current = false;
        }, 300);
      }
      // Aggressive correction: adjust playback rate for drift (0.15-0.5 second)
      else if (absDiff > 0.1 && syncState.isPlaying) {
        // More aggressive rate adjustment based on drift amount
        const intensity = Math.min(absDiff * 0.2, 0.1); // Max 10% speed change
        const rate = diff > 0 ? 1 + intensity : 1 - intensity;
        player.setPlaybackRate(rate);
      }
      // Reset to normal speed when tightly synced
      else if (absDiff <= 0.1) {
        player.setPlaybackRate(1.0);
      }

      // Play/pause
      const playerState = player.getPlayerState();
      const isPlaying = playerState === window.YT.PlayerState.PLAYING;

      if (syncState.isPlaying && !isPlaying) {
        isLocalActionRef.current = true;
        player.playVideo();
        setTimeout(() => {
          isLocalActionRef.current = false;
        }, 300);
      } else if (!syncState.isPlaying && isPlaying) {
        isLocalActionRef.current = true;
        player.pauseVideo();
        player.setPlaybackRate(1.0);
        setTimeout(() => {
          isLocalActionRef.current = false;
        }, 300);
      }
    } catch (e) {
      console.error('Sync error:', e);
    }
  }, [isHost, syncState.currentTime, syncState.isPlaying, playerReady]);

  // High-frequency sync from host (every 500ms for tight sync)
  useEffect(() => {
    if (!isHost || !playerReady || !syncState.isPlaying) return;

    const interval = setInterval(() => {
      if (playerRef.current) {
        try {
          const currentTime = playerRef.current.getCurrentTime() || 0;
          sendSync(currentTime, true);
        } catch (e) {
          console.error('Periodic sync error:', e);
        }
      }
    }, 500);

    return () => clearInterval(interval);
  }, [isHost, playerReady, syncState.isPlaying, sendSync]);

  const handleCopyLink = useCallback(() => {
    navigator.clipboard.writeText(window.location.href);
    alert('Link copied to clipboard!');
  }, []);

  if (roomClosed) {
    return (
      <div className="watch-room-error">
        <h2>Watch Party Ended</h2>
        <p>{error}</p>
        <a href="/">Return Home</a>
      </div>
    );
  }

  if (error && !isConnected) {
    return (
      <div className="watch-room-error">
        <h2>Connection Error</h2>
        <p>{error}</p>
        <button onClick={() => window.location.reload()}>Retry</button>
      </div>
    );
  }

  return (
    <div className="watch-room">
      <div className="watch-room-header">
        <h2>Watch Party: {roomCode}</h2>
        <div className="watch-room-controls">
          <span
            className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}
          >
            {isConnected ? 'Connected' : 'Connecting...'}
          </span>
          <button onClick={handleCopyLink} className="share-btn">
            Copy Invite Link
          </button>
        </div>
      </div>

      {!isHost && (
        <div className="viewer-notice">
          You are viewing. Only the host can control playback.
        </div>
      )}

      <div className="watch-room-content">
        <div className="video-container">
          <div className="video-wrapper">
            {videoId ? (
              <>
                <div ref={containerRef} id="youtube-player" />
                {!isHost && <div className="video-overlay" />}
              </>
            ) : (
              <div className="video-loading">
                {videoUrl ? 'Invalid video URL' : 'Loading video...'}
              </div>
            )}
          </div>
        </div>

        <div className="chat-container">
          <ChatBox messages={chatMessages} onSendMessage={sendChat} />
        </div>
      </div>
    </div>
  );
}

export default WatchRoom;
