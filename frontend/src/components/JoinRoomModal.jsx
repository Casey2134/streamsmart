import { useState, useEffect } from 'react';
import { getSavedUsername, saveUsername } from '../utils/session';

/**
 * Modal that prompts users to enter their display name before joining a room.
 */
function JoinRoomModal({ onJoin, isHost = false }) {
  const [username, setUsername] = useState('');

  useEffect(() => {
    // Pre-fill with saved username if available
    const savedName = getSavedUsername();
    if (savedName) {
      setUsername(savedName);
    }
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    const trimmedName = username.trim();
    if (trimmedName) {
      saveUsername(trimmedName);
      onJoin(trimmedName);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal">
        <h2>{isHost ? 'Start Watch Party' : 'Join Watch Party'}</h2>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="username">Enter your display name:</label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Your name"
              maxLength={20}
              autoFocus
              autoComplete="off"
            />
          </div>
          <button type="submit" disabled={!username.trim()}>
            {isHost ? 'Create Room' : 'Join Room'}
          </button>
        </form>
      </div>
    </div>
  );
}

export default JoinRoomModal;
