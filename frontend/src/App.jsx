import { Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import Navbar from './components/layout/Navbar';
import Dashboard from './views/Dashboard';
import AthleteList from './components/AthleteList';
import AthleteProfile from './views/AthleteProfile';
import AthleteForm from './components/AthleteForm';
import ComparePage from './views/ComparePage';

export default function App() {
  return (
    <AuthProvider>
      <div className="min-h-screen bg-surface-900 text-slate-100">
        <Navbar />
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/discover" element={<AthleteList />} />
          <Route path="/compare" element={<ComparePage />} />
          <Route path="/athletes/new" element={<AthleteForm />} />
          <Route path="/athletes/:id/edit" element={<AthleteForm />} />
          <Route path="/athletes/:id" element={<AthleteProfile />} />
        </Routes>
      </div>
    </AuthProvider>
  );
}
