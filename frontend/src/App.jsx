import { useState } from 'react'
import './App.css'

function MyForm() {
  const [url, setUrl] = useState("");
  function handleChange(e) {
    setUrl(e.target.value);
  }
  function handleSubmit(e) {
    e.preventDefault();
    alert(url);
  }
  return (
    <form onSubmit={handleSubmit}>
      <label>Paste Your Youtube URL
        <input
          type='text'
          value={url}
          onChange={handleChange}
          />
      </label>
      <input type='submit' />
    </form>
  )
}

function App() {

  return (
    <>
      <MyForm />
    </>
  )
}

export default App
