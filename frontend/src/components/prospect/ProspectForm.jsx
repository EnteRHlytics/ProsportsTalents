import { useEffect, useState } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import { Save, ArrowLeft } from 'lucide-react';
import PageWrapper from '../layout/PageWrapper';
import ErrorBanner from '../common/ErrorBanner';
import LoadingSpinner from '../ui/LoadingSpinner';
import { listSports } from '../../utils/sportConfig';
import { apiFetch } from '../../hooks/useApi';

const SPORTS = listSports();

const inputCls = {
  width: '100%',
  padding: '9px 12px',
  background: 'var(--bg-surface-alt)',
  border: '1px solid var(--border-default)',
  borderRadius: 'var(--radius-md)',
  fontSize: 13,
  color: 'var(--fg-primary)',
  outline: 'none',
  transition: 'border-color var(--transition)',
  fontFamily: 'var(--font-body)',
};

const labelCls = {
  display: 'block',
  fontSize: 11,
  fontWeight: 600,
  letterSpacing: '0.04em',
  textTransform: 'uppercase',
  color: 'var(--fg-tertiary)',
  marginBottom: 4,
};

function Field({ label, children }) {
  return (
    <div>
      <label style={labelCls}>{label}</label>
      {children}
    </div>
  );
}

const EMPTY = {
  first_name: '',
  last_name: '',
  date_of_birth: '',
  nationality: '',
  sport: '',
  position: '',
  school: '',
  height: '',
  weight: '',
  jersey_number: '',
  draft_year: '',
  scout_grade: '',
  scout_notes: '',
  bio: '',
};

export default function ProspectForm() {
  const navigate = useNavigate();
  const { id } = useParams();
  const isEdit = Boolean(id);

  const [form, setForm] = useState(EMPTY);
  const [loading, setLoading] = useState(isEdit);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!isEdit) return;
    let alive = true;
    setLoading(true);
    apiFetch(`/prospects/${id}`)
      .then((data) => {
        if (!alive || !data) return;
        setForm({
          first_name:    data.user?.first_name ?? data.first_name ?? '',
          last_name:     data.user?.last_name  ?? data.last_name  ?? '',
          date_of_birth: data.date_of_birth ?? '',
          nationality:   data.nationality ?? '',
          sport:         data.primary_sport?.code ?? data.sport ?? '',
          position:      data.position ?? data.primary_position?.name ?? '',
          school:        data.school ?? '',
          height:        data.height ?? '',
          weight:        data.weight ?? '',
          jersey_number: data.jersey_number ?? '',
          draft_year:    data.draft_year ?? data.draft_eligible_year ?? '',
          scout_grade:   data.scout_grade ?? '',
          scout_notes:   data.scout_notes ?? '',
          bio:           data.bio ?? '',
        });
      })
      .catch((e) => { if (alive) setError(e); })
      .finally(() => { if (alive) setLoading(false); });
    return () => { alive = false; };
  }, [id, isEdit]);

  const update = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError(null);

    const payload = {
      ...form,
      scout_grade: form.scout_grade !== '' ? Number(form.scout_grade) : undefined,
      draft_year:  form.draft_year  !== '' ? Number(form.draft_year)  : undefined,
    };

    try {
      const url    = isEdit ? `/prospects/${id}` : '/prospects';
      const method = isEdit ? 'PUT' : 'POST';
      const result = await apiFetch(url, { method, body: payload });
      const newId = result?.prospect_id || result?.id || id;
      navigate(newId ? `/prospects/${newId}` : '/prospects');
    } catch (err) {
      setError(err);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <PageWrapper><LoadingSpinner /></PageWrapper>;
  }

  return (
    <PageWrapper maxWidth={760}>
      <div style={{ marginBottom: 12 }}>
        <Link to="/prospects" style={{ color: 'var(--fg-tertiary)', fontSize: 12, display: 'inline-flex', alignItems: 'center', gap: 4 }}>
          <ArrowLeft size={12} /> All prospects
        </Link>
      </div>
      <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 32, margin: '0 0 18px', color: 'var(--fg-primary)' }}>
        {isEdit ? 'Edit Prospect' : 'New Prospect'}
      </h1>

      {error && (
        <div style={{ marginBottom: 14 }}>
          <ErrorBanner message={error.message || 'Failed to save prospect.'} />
        </div>
      )}

      <form
        onSubmit={handleSubmit}
        style={{
          background: 'var(--bg-surface)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-lg)',
          padding: 20,
          display: 'flex',
          flexDirection: 'column',
          gap: 14,
        }}
      >
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 12 }}>
          <Field label="First Name">
            <input style={inputCls} value={form.first_name} onChange={update('first_name')} required />
          </Field>
          <Field label="Last Name">
            <input style={inputCls} value={form.last_name} onChange={update('last_name')} required />
          </Field>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 12 }}>
          <Field label="Date of Birth">
            <input type="date" style={inputCls} value={form.date_of_birth} onChange={update('date_of_birth')} />
          </Field>
          <Field label="Nationality">
            <input style={inputCls} value={form.nationality} onChange={update('nationality')} placeholder="e.g. American" />
          </Field>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 12 }}>
          <Field label="Sport">
            <select style={inputCls} value={form.sport} onChange={update('sport')} required>
              <option value="">Select sport</option>
              {SPORTS.map((s) => (
                <option key={s.code} value={s.code}>{s.code} — {s.label}</option>
              ))}
            </select>
          </Field>
          <Field label="Position">
            <input style={inputCls} value={form.position} onChange={update('position')} placeholder="e.g. Point Guard" />
          </Field>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 12 }}>
          <Field label="School / College">
            <input style={inputCls} value={form.school} onChange={update('school')} placeholder="e.g. Duke" />
          </Field>
          <Field label="Draft Year">
            <input type="number" min={1990} max={2099} style={inputCls} value={form.draft_year} onChange={update('draft_year')} placeholder="e.g. 2026" />
          </Field>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 12 }}>
          <Field label="Height">
            <input style={inputCls} value={form.height} onChange={update('height')} placeholder="6'5&quot;" />
          </Field>
          <Field label="Weight">
            <input style={inputCls} value={form.weight} onChange={update('weight')} placeholder="210 lb" />
          </Field>
          <Field label="Jersey #">
            <input style={inputCls} value={form.jersey_number} onChange={update('jersey_number')} placeholder="#" />
          </Field>
          <Field label="Scout Grade (0–100)">
            <input type="number" min={0} max={100} style={inputCls} value={form.scout_grade} onChange={update('scout_grade')} />
          </Field>
        </div>

        <Field label="Scout Notes">
          <textarea
            rows={4}
            style={{ ...inputCls, resize: 'vertical' }}
            value={form.scout_notes}
            onChange={update('scout_notes')}
            placeholder="Strengths, weaknesses, comparables…"
          />
        </Field>

        <Field label="Bio">
          <textarea
            rows={3}
            style={{ ...inputCls, resize: 'vertical' }}
            value={form.bio}
            onChange={update('bio')}
            placeholder="Short biography…"
          />
        </Field>

        <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end', marginTop: 4 }}>
          <Link
            to="/prospects"
            style={{
              padding: '10px 16px',
              fontSize: 13,
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-default)',
              color: 'var(--fg-secondary)',
              textDecoration: 'none',
              display: 'inline-flex',
              alignItems: 'center',
            }}
          >
            Cancel
          </Link>
          <button
            type="submit"
            disabled={saving}
            style={{
              padding: '10px 18px',
              fontSize: 13,
              fontWeight: 600,
              borderRadius: 'var(--radius-md)',
              background: 'var(--orange-500)',
              color: '#fff',
              border: 'none',
              display: 'inline-flex',
              alignItems: 'center',
              gap: 6,
              cursor: saving ? 'wait' : 'pointer',
              opacity: saving ? 0.7 : 1,
            }}
          >
            <Save size={14} /> {saving ? 'Saving…' : (isEdit ? 'Save Changes' : 'Create Prospect')}
          </button>
        </div>
      </form>
    </PageWrapper>
  );
}
