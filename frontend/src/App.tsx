/**
 * Main App component with routing
 */

import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import Chat from './components/Chat';
import Analytics from './components/analytics/Analytics';
import Experiments from './components/experiments/Experiments';
import Prompts from './components/prompts/Prompts';
import Settings from './components/settings/Settings';
import './App.css';

export default function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <nav className="app-nav">
          <NavLink to="/" end className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            Chat
          </NavLink>
          <NavLink to="/analytics" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            Analytics
          </NavLink>
          <NavLink to="/experiments" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            Experiments
          </NavLink>
          <NavLink to="/prompts" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            Prompts
          </NavLink>
          <NavLink to="/settings" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            Settings
          </NavLink>
        </nav>
        <div className="app-content">
          <Routes>
            <Route path="/" element={<Chat />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/experiments" element={<Experiments />} />
            <Route path="/prompts" element={<Prompts />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  );
}
