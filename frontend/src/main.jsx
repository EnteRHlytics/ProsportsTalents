import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import './index.css';

// Set initial theme from localStorage, default to dark
const saved = (() => { try { return localStorage.getItem('pst-theme'); } catch { return null; } })();
document.documentElement.setAttribute('data-theme', saved || 'dark');

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
);
