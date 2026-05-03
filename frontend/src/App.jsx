import { Routes, Route } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { AuthProvider } from './context/AuthContext';
import Navbar from './components/layout/Navbar';
import Footer from './components/layout/Footer';
import Dashboard from './views/Dashboard';
import AthleteList from './components/AthleteList';
import AthleteProfile from './views/AthleteProfile';
import AthleteForm from './components/AthleteForm';
import ComparePage from './views/ComparePage';
import ProspectList from './views/ProspectList';
import ProspectProfile from './views/ProspectProfile';
import ProspectForm from './components/prospect/ProspectForm';
import Discover from './views/Discover';
import Rankings from './views/Rankings';
import RankingsCustomize from './views/RankingsCustomize';
import Login from './views/Login';
import AuthCallback from './views/AuthCallback';
import AdminActivity from './views/AdminActivity';

export default function App() {
  const [theme, setTheme] = useState(() => {
    try { return localStorage.getItem('pst-theme') || 'dark'; } catch { return 'dark'; }
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    try { localStorage.setItem('pst-theme', theme); } catch {}
  }, [theme]);

  function toggleTheme() {
    setTheme(t => t === 'dark' ? 'light' : 'dark');
  }

  return (
    <AuthProvider>
      <div className="flex flex-col min-h-screen bg-surface-900 text-slate-100" style={{ transition: 'background-color 350ms ease, color 350ms ease' }}>
        <Navbar theme={theme} toggleTheme={toggleTheme} />
        <div className="flex-1">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/discover" element={<Discover />} />
            <Route path="/discover/legacy" element={<AthleteList />} />
            <Route path="/athletes" element={<AthleteList />} />
            <Route path="/compare" element={<ComparePage />} />
            <Route path="/rankings" element={<Rankings />} />
            <Route path="/rankings/customize" element={<RankingsCustomize />} />
            <Route path="/athletes/new" element={<AthleteForm />} />
            <Route path="/athletes/:id/edit" element={<AthleteForm />} />
            <Route path="/athletes/:id" element={<AthleteProfile />} />
            <Route path="/prospects" element={<ProspectList />} />
            <Route path="/prospects/new" element={<ProspectForm />} />
            <Route path="/prospects/:id" element={<ProspectProfile />} />
            <Route path="/login" element={<Login />} />
            <Route path="/auth/callback" element={<AuthCallback />} />
            <Route path="/admin/activity" element={<AdminActivity />} />
          </Routes>
        </div>
        <Footer />
      </div>
    </AuthProvider>
  );
}
