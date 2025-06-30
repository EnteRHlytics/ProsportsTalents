import { Routes, Route, Link } from 'react-router-dom';
import AthleteList from './components/AthleteList';
import AthleteProfile from './views/AthleteProfile';
import AthleteForm from './components/AthleteForm';

export default function App() {
  return (
    <div>
      <nav>
        <Link to="/">Home</Link>
      </nav>
      <Routes>
        <Route path="/" element={<AthleteList />} />
        <Route path="/athletes/new" element={<AthleteForm />} />
        <Route path="/athletes/:id/edit" element={<AthleteForm />} />
        <Route path="/athletes/:id" element={<AthleteProfile />} />
      </Routes>
    </div>
  );
}
