/**
 * Get or create a unique session ID for this browser.
 * Stored in localStorage so it persists across page refreshes.
 */
export function getSessionId() {
  const STORAGE_KEY = 'watchparty_session_id';
  let sessionId = localStorage.getItem(STORAGE_KEY);

  if (!sessionId) {
    sessionId = crypto.randomUUID();
    localStorage.setItem(STORAGE_KEY, sessionId);
  }

  return sessionId;
}

/**
 * Get the saved username from localStorage.
 */
export function getSavedUsername() {
  return localStorage.getItem('watchparty_username') || '';
}

/**
 * Save the username to localStorage.
 */
export function saveUsername(username) {
  localStorage.setItem('watchparty_username', username);
}
