import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import JoinRoomModal from './JoinRoomModal';
import WatchRoom from './WatchRoom';
import { getSessionId } from '../utils/session';

/**
 * Page component that handles the watch party flow:
 * - If roomCode exists in URL, join that room
 * - Otherwise, show form to create a new room
 */
function WatchPartyPage() {
  const { roomCode } = useParams();
  const navigate = useNavigate();

  const [username, setUsername] = useState(null);
  const [sessionId] = useState(() => getSessionId());
  const [videoUrl, setVideoUrl] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState(null);
  const [roomExists, setRoomExists] = useState(null); // null = checking, true/false = result

  // Check if room exists when we have a roomCode
  useEffect(() => {
    if (roomCode) {
      fetch(`/api/v1/watchparty/rooms/${roomCode}/`)
        .then((res) => {
          if (res.ok) {
            setRoomExists(true);
          } else {
            setRoomExists(false);
            setError('Room not found. It may have been closed by the host.');
          }
        })
        .catch(() => {
          setRoomExists(false);
          setError('Failed to check room status.');
        });
    }
  }, [roomCode]);

  // Handle username submission for joining
  const handleJoin = (name) => {
    setUsername(name);
  };

  // Validate YouTube URL
  const isValidVideoUrl = (url) => {
    const patterns = [
      /^https?:\/\/(www\.)?youtube\.com\/watch\?v=[\w-]+/,
      /^https?:\/\/youtu\.be\/[\w-]+/,
      /^https?:\/\/(www\.)?youtube\.com\/embed\/[\w-]+/,
      /^https?:\/\/(www\.)?vimeo\.com\/\d+/,
    ];
    return patterns.some((pattern) => pattern.test(url));
  };

  // Handle creating a new room
  const handleCreateRoom = async (e) => {
    e.preventDefault();
    if (!videoUrl.trim()) return;

    if (!isValidVideoUrl(videoUrl)) {
      setError('Please enter a valid YouTube or Vimeo URL');
      return;
    }

    setIsCreating(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/watchparty/rooms/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          video_url: videoUrl,
          host_session_id: sessionId,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to create room');
      }

      const data = await response.json();
      // Navigate to the new room
      navigate(`/watch/${data.code}`);
    } catch (err) {
      setError('Failed to create room. Please try again.');
    } finally {
      setIsCreating(false);
    }
  };

  // Creating a new room - show video URL form first, then username modal
  if (!roomCode) {
    return (
      <div className="create-room-page">
        <h1>Create Watch Party</h1>
        <p>Paste a YouTube URL to start watching with friends.</p>

        <form onSubmit={handleCreateRoom} className="create-room-form">
          <div className="form-group">
            <label htmlFor="videoUrl">YouTube URL:</label>
            <input
              id="videoUrl"
              type="url"
              value={videoUrl}
              onChange={(e) => setVideoUrl(e.target.value)}
              placeholder="https://www.youtube.com/watch?v=..."
              disabled={isCreating}
              required
            />
          </div>
          <button type="submit" disabled={isCreating || !videoUrl.trim()}>
            {isCreating ? 'Creating...' : 'Create Room'}
          </button>
        </form>

        {error && <div className="error-message">{error}</div>}

        <p className="info-text">
          After creating a room, you&apos;ll get a shareable link to invite friends.
        </p>
      </div>
    );
  }

  // Room doesn't exist
  if (roomExists === false) {
    return (
      <div className="room-error-page">
        <h1>Room Not Found</h1>
        <p>{error}</p>
        <a href="/watch">Create a new watch party</a>
      </div>
    );
  }

  // Still checking if room exists
  if (roomExists === null) {
    return (
      <div className="loading-page">
        <p>Loading room...</p>
      </div>
    );
  }

  // Room exists but user hasn't entered username yet
  if (!username) {
    return <JoinRoomModal onJoin={handleJoin} isHost={false} />;
  }

  // Room exists and user has entered username - show the watch room
  return (
    <WatchRoom roomCode={roomCode} sessionId={sessionId} username={username} />
  );
}

export default WatchPartyPage;
