import { useState, useEffect, useRef } from 'react'
import './App.css'

function App() {
  const [url, setUrl] = useState("");
  const [job, setJob] = useState(null);
  const [error, setError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const pollIntervalRef = useRef(null);

  const pollJobStatus = async (jobId) => {
    try {
      const response = await fetch(`/api/v1/summarizer/jobs/${jobId}`);
      if (!response.ok) {
        throw new Error('Failed to fetch job status');
      }
      const data = await response.json();
      setJob(data);

      if (data.status === 'COMPLETED') {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
    } catch (err) {
      console.error('Error polling job status:', err);
      setError('Failed to fetch job status');
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setJob(null);
    setIsSubmitting(true);

    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
    }

    try {
      const response = await fetch('/api/v1/summarizer/summarize/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url: url }),
      });

      if (!response.ok) {
        throw new Error('Failed to create job');
      }

      const data = await response.json();
      setJob(data);

      pollIntervalRef.current = setInterval(() => {
        pollJobStatus(data.id);
      }, 2000);
    } catch (err) {
      console.error('Error submitting form:', err);
      setError('Failed to submit URL. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, []);

  const formatTimestamp = (seconds) => {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    if (hrs > 0) {
      return `${hrs}:${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
    }
    return `${mins}:${String(secs).padStart(2, '0')}`;
  };

  const getStatusMessage = (status) => {
    switch (status) {
      case 'DOWNLOADING':
        return 'Downloading video...';
      case 'TRANSCRIBING':
        return 'Transcribing audio...';
      case 'ANALYZING':
        return 'Analyzing content...';
      case 'COMPLETED':
        return 'Complete!';
      default:
        return status;
    }
  };

  return (
    <>
      <form onSubmit={handleSubmit}>
        <label>Paste Your Youtube URL
          <input
            type='text'
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            disabled={isSubmitting || (job && job.status !== 'COMPLETED')}
          />
        </label>
        <input
          type='submit'
          disabled={isSubmitting || (job && job.status !== 'COMPLETED')}
        />
      </form>

      {error && (
        <div className="error">
          {error}
        </div>
      )}

      {job && (
        <div className="job-status">
          {job.title && <h2>{job.title}</h2>}
          <p className="status">{getStatusMessage(job.status)}</p>

          {job.status === 'COMPLETED' && job.summary && (
            <div className="summary">
              <h3>Summary</h3>
              <p>{job.summary}</p>
            </div>
          )}

          {job.status === 'COMPLETED' && job.chapters && job.chapters.length > 0 && (
            <div className="chapters">
              <h3>Chapters</h3>
              <ul>
                {job.chapters.map((chapter, index) => (
                  <li key={index}>
                    <span className="timestamp">{formatTimestamp(chapter.timestamp)}</span>{' '}
                    <strong>{chapter.title}</strong>
                    {chapter.summary && <p>{chapter.summary}</p>}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {job.status === 'COMPLETED' && job.highlights && job.highlights.length > 0 && (
            <div className="highlights">
              <h3>Highlights</h3>
              <ul>
                {job.highlights.map((highlight, index) => (
                  <li key={index}>
                    <span className="timestamp">{formatTimestamp(highlight.timestamp)}</span>{' '}
                    <span>{highlight.description}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </>
  )
}

export default App
