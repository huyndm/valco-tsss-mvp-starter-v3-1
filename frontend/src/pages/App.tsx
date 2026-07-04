import React, { useCallback, useEffect, useState } from 'react';

const API = 'http://localhost:8000/api/v1';

async function apiFetch<T>(path: string, opts: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(opts.headers ?? {}) },
    ...opts,
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`${res.status}: ${detail}`);
  }
  return res.json() as Promise<T>;
}

// ============================================================
// Interfaces
// ============================================================
interface Project {
  id: number;
  name: string;
  description: string | null;
  created_at: string;
}

interface SubjectAsset {
  id: number;
  project_id: number;
  address: string;
  market_area: string;
  land_type: string;
  planning_segment: string | null;
  size_sqm: number;
}

interface RawCandidate {
  id: number;
  project_id: number;
  source_url: string | null;
  raw_text: string | null;
  market_area: string | null;
  land_type: string | null;
  planning_segment: string | null;
  size_sqm: number | null;
  unit_price: number | null;
  asking_price: number | null;
  source_quality: string | null;
  evidence_timestamp: string | null;
  candidate_class: string;
  created_at: string | null;
  dedup_status: string | null;
  hard_filter_status: string | null;
  hard_filter_flags: string[];
  adjustment_warnings: string[];
}

interface ExtractionResultItem {
  id: number;
  raw_candidate_id: number;
  normalized_market_area: string | null;
  normalized_land_type: string | null;
  normalized_planning_segment: string | null;
  normalized_size_sqm: number | null;
  normalized_unit_price: number | null;
  extraction_status: string;
  draft_note: string | null;
}

interface ExtractionResultsResponse {
  project_id: number;
  results: ExtractionResultItem[];
}

interface Top10CandidateInfo {
  id: number;
  source_url: string | null;
  market_area: string | null;
  land_type: string | null;
  planning_segment: string | null;
  size_sqm: number | null;
  unit_price: number | null;
  asking_price: number | null;
}

interface Top10Scores {
  market_area_score: number;
  land_type_score: number;
  size_score: number;
  unit_price_score: number;
  source_link_score: number;
  adjustment_ratio_score: number;
  adjustment_ratio: number;
  total_score: number;
}

interface Top10Rec {
  rank: number;
  eligible_candidate_id: number;
  candidate: Top10CandidateInfo | null;
  scores: Top10Scores | null;
}

interface Top10Response {
  project_id: number;
  recommendations: Top10Rec[];
}

interface Final3SelectionItem {
  id: number;
  eligible_candidate_id: number;
  is_override: boolean;
  override_reason: string | null;
  selected_by: string;
  candidate: Top10CandidateInfo | null;
}

interface Final3Response {
  project_id: number;
  selections: Final3SelectionItem[];
}

interface AuditLogEntry {
  id: number;
  action: string;
  actor: string;
  details_json: string | null;
  created_at: string | null;
}

interface AuditLogResponse {
  project_id: number;
  logs: AuditLogEntry[];
}

interface ExportResponse {
  project_id: number;
  export_record_id: number;
  file_path: string | null;
  status: string;
}

// ============================================================
// Pipeline configuration
// ============================================================
interface PipelineStep {
  key: string;
  label: string;
  page: string;
}

const PIPELINE_STEPS: PipelineStep[] = [
  { key: 'project', label: 'Project', page: 'projects' },
  { key: 'subject', label: 'Subject Asset', page: 'subject' },
  { key: 'add', label: 'Add Candidate', page: 'add' },
  { key: 'pool', label: 'Candidate Pool', page: 'pool' },
  { key: 'dedup', label: 'Dedup', page: 'pool' },
  { key: 'hardfilter', label: 'Hard Filter', page: 'pool' },
  { key: 'extraction', label: 'Extraction', page: 'extraction' },
  { key: 'scoring', label: 'Scoring / Top 10', page: 'export' },
  { key: 'final3', label: 'Final 3', page: 'export' },
  { key: 'export', label: 'Export', page: 'export' },
  { key: 'audit', label: 'Audit Log', page: 'export' },
];

// ============================================================
// Utility components
// ============================================================
function useAsync<T>(fn: () => Promise<T>, deps: React.DependencyList = []) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const run = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setData(await fn());
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }, deps);

  useEffect(() => {
    void run();
  }, [run]);

  return { data, error, loading, refetch: run };
}

function Alert({ msg, type = 'danger' }: { msg: string; type?: string }) {
  return <div className={`alert alert-${type}`}>{msg}</div>;
}

function fmt(n: number | null | undefined) {
  if (n === null || n === undefined) return '-';
  return n.toLocaleString('vi-VN');
}

function fmtPct(n: number | null | undefined) {
  if (n === null || n === undefined) return '-';
  return `${(n * 100).toFixed(0)}%`;
}

function Badge({ text, variant }: { text: string; variant?: string }) {
  const cls = variant ? `badge badge-${variant}` : 'badge badge-muted';
  return <span className={cls}>{text}</span>;
}

function StatusDot({ status }: { status: string }) {
  const colorMap: Record<string, string> = {
    passed: 'dot-green',
    rejected: 'dot-red',
    pending: 'dot-yellow',
    unique: 'dot-green',
    duplicate_of_: 'dot-red',
    flagged_duplicate: 'dot-red',
  };
  let dotClass = 'dot dot-yellow';
  for (const [key, cls] of Object.entries(colorMap)) {
    if (status.startsWith(key)) {
      dotClass = `dot ${cls}`;
      break;
    }
  }
  return <span className={dotClass} style={{ marginRight: 6 }} />;
}

// ============================================================
// Pipeline Indicator
// ============================================================
function PipelineIndicator({ currentPage }: { currentPage: string }) {
  const currentIdx = PIPELINE_STEPS.findIndex(s => s.page === currentPage);
  return (
    <div className="pipeline">
      {PIPELINE_STEPS.map((step, idx) => {
        let cls = 'pipeline-step';
        if (idx < currentIdx) cls += ' done';
        else if (idx === currentIdx) cls += ' active';
        return (
          <span key={step.key} className={cls}>
            {step.label}
          </span>
        );
      })}
    </div>
  );
}

// ============================================================
// Pages
// ============================================================
function ProjectsPage({ onOpen }: { onOpen: (p: Project) => void }) {
  const { data, error, loading, refetch } = useAsync<Project[]>(() => apiFetch('/projects'));
  const [name, setName] = useState('');
  const [desc, setDesc] = useState('');

  async function createProject(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    await apiFetch('/projects', {
      method: 'POST',
      body: JSON.stringify({ name: name.trim(), description: desc.trim() || null }),
    });
    setName('');
    setDesc('');
    await refetch();
  }

  return (
    <div>
      <div className="page-header">
        <h1>Projects</h1>
        <p>Create and manage valuation projects.</p>
      </div>

      <section className="card" style={{ marginBottom: 20 }}>
        <h3 className="card-title">New Project</h3>
        <form onSubmit={createProject}>
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Project Name</label>
              <input className="form-input" placeholder="e.g. My Valuation" value={name} onChange={e => setName(e.target.value)} />
            </div>
            <div className="form-group">
              <label className="form-label">Description</label>
              <input className="form-input" placeholder="Optional description" value={desc} onChange={e => setDesc(e.target.value)} />
            </div>
          </div>
          <button className="btn btn-primary" type="submit">Create Project</button>
        </form>
      </section>

      <section className="card">
        <h3 className="card-title">All Projects ({data?.length ?? 0})</h3>
        {loading && <div className="loading-row"><span className="spinner" /> Loading...</div>}
        {error && <Alert msg={error} />}
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Description</th>
                <th>Created</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {(data ?? []).map(p => (
                <tr key={p.id}>
                  <td className="mono">#{p.id}</td>
                  <td>{p.name}</td>
                  <td>{p.description ?? <span className="text-muted">-</span>}</td>
                  <td className="text-sm">{p.created_at?.slice(0, 10)}</td>
                  <td><button className="btn btn-primary btn-sm" onClick={() => onOpen(p)}>Open</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

function GatewayPage() {
  const { data, error, loading, refetch } = useAsync<Record<string, unknown>>(
    () => apiFetch('/gateway/health'),
  );

  return (
    <div>
      <div className="page-header">
        <h1>Gateway Health</h1>
        <p>FreeLLMAPI runtime gateway status.</p>
      </div>
      <section className="card">
        <div className="flex justify-between items-center mb-16">
          <h3 className="card-title" style={{ margin: 0 }}>Health Check</h3>
          <button className="btn btn-ghost btn-sm" onClick={refetch}>Refresh</button>
        </div>
        {loading && <div className="loading-row"><span className="spinner" /> Checking...</div>}
        {error && <Alert msg={error} />}
        {data && <pre className="mono" style={{ background: 'var(--bg-base)', padding: 16, borderRadius: 'var(--radius-sm)', overflow: 'auto' }}>{JSON.stringify(data, null, 2)}</pre>}
      </section>
    </div>
  );
}

function SubjectPage({ project }: { project: Project }) {
  const { data, error, loading, refetch } = useAsync<SubjectAsset>(
    () => apiFetch(`/projects/${project.id}/subject-asset`),
    [project.id],
  );

  const [form, setForm] = useState({
    address: '',
    market_area: '',
    land_type: '',
    planning_segment: '',
    size_sqm: '',
  });
  const [saveMsg, setSaveMsg] = useState<string | null>(null);

  async function save(e: React.FormEvent) {
    e.preventDefault();
    setSaveMsg(null);
    await apiFetch(`/projects/${project.id}/subject-asset`, {
      method: 'POST',
      body: JSON.stringify({
        address: form.address,
        market_area: form.market_area,
        land_type: form.land_type,
        planning_segment: form.planning_segment || null,
        size_sqm: Number(form.size_sqm),
      }),
    });
    setSaveMsg('Subject asset saved successfully.');
    await refetch();
  }

  return (
    <div>
      <PipelineIndicator currentPage="subject" />
      <div className="page-header">
        <h1>Subject Asset</h1>
        <p>Project: <strong>{project.name}</strong></p>
      </div>

      {saveMsg && <Alert msg={saveMsg} type="success" />}
      {loading && <div className="loading-row"><span className="spinner" /> Loading...</div>}
      {error && !error.includes('404') && <Alert msg={error} />}

      {data && (
        <section className="card" style={{ marginBottom: 20 }}>
          <h3 className="card-title">Current Subject Asset</h3>
          <div className="card-grid card-grid-3">
            <div className="stat-card">
              <span className="stat-label">Address</span>
              <span className="stat-value" style={{ fontSize: '1.1rem' }}>{data.address}</span>
            </div>
            <div className="stat-card">
              <span className="stat-label">Market Area</span>
              <span className="stat-value" style={{ fontSize: '1.1rem' }}>{data.market_area}</span>
            </div>
            <div className="stat-card">
              <span className="stat-label">Land Type</span>
              <span className="stat-value" style={{ fontSize: '1.1rem' }}>{data.land_type}</span>
            </div>
            <div className="stat-card">
              <span className="stat-label">Planning Segment</span>
              <span className="stat-value" style={{ fontSize: '1.1rem' }}>{data.planning_segment ?? '-'}</span>
            </div>
            <div className="stat-card">
              <span className="stat-label">Size (sqm)</span>
              <span className="stat-value" style={{ fontSize: '1.1rem' }}>{fmt(data.size_sqm)}</span>
            </div>
          </div>
        </section>
      )}

      <section className="card">
        <h3 className="card-title">Create / Update Subject Asset</h3>
        <form onSubmit={save}>
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Address</label>
              <input className="form-input" placeholder="e.g. 123 Main St" value={form.address} onChange={e => setForm({ ...form, address: e.target.value })} />
            </div>
            <div className="form-group">
              <label className="form-label">Market Area</label>
              <input className="form-input" placeholder="e.g. District 2" value={form.market_area} onChange={e => setForm({ ...form, market_area: e.target.value })} />
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Land Type</label>
              <input className="form-input" placeholder="e.g. ODT, ONT, TMDV, SKC, CLN" value={form.land_type} onChange={e => setForm({ ...form, land_type: e.target.value })} />
            </div>
            <div className="form-group">
              <label className="form-label">Planning Segment</label>
              <input className="form-input" placeholder="e.g. residential" value={form.planning_segment} onChange={e => setForm({ ...form, planning_segment: e.target.value })} />
            </div>
          </div>
          <div className="form-group" style={{ maxWidth: 300 }}>
            <label className="form-label">Size (sqm)</label>
            <input className="form-input" placeholder="e.g. 100" type="number" value={form.size_sqm} onChange={e => setForm({ ...form, size_sqm: e.target.value })} />
          </div>
          <button className="btn btn-primary" type="submit">Save Subject Asset</button>
        </form>
      </section>
    </div>
  );
}

function AddCandidatePage({ project }: { project: Project }) {
  const [form, setForm] = useState({
    source_url: '',
    raw_text: '',
    market_area: '',
    land_type: '',
    size_sqm: '',
    unit_price: '',
    asking_price: '',
    source_quality: 'MEDIUM',
  });
  const [msg, setMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function add(e: React.FormEvent) {
    e.preventDefault();
    setMsg(null);
    setError(null);
    try {
      await apiFetch(`/projects/${project.id}/raw-candidates`, {
        method: 'POST',
        body: JSON.stringify({
          source_url: form.source_url || null,
          raw_text: form.raw_text || null,
          market_area: form.market_area || null,
          land_type: form.land_type || null,
          size_sqm: form.size_sqm ? Number(form.size_sqm) : null,
          unit_price: form.unit_price ? Number(form.unit_price) : null,
          asking_price: form.asking_price ? Number(form.asking_price) : null,
          source_quality: form.source_quality,
        }),
      });
      setMsg('Candidate added successfully.');
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    }
  }

  return (
    <div>
      <PipelineIndicator currentPage="add" />
      <div className="page-header">
        <h1>Add Candidate</h1>
        <p>Project: <strong>{project.name}</strong></p>
      </div>

      {msg && <Alert msg={msg} type="success" />}
      {error && <Alert msg={error} />}

      <section className="card">
        <h3 className="card-title">New Raw Candidate</h3>
        <form onSubmit={add}>
          <div className="form-group">
            <label className="form-label">Source URL</label>
            <input className="form-input" placeholder="https://example.com/listing" value={form.source_url} onChange={e => setForm({ ...form, source_url: e.target.value })} />
          </div>
          <div className="form-group">
            <label className="form-label">Raw Text</label>
            <textarea className="form-textarea" placeholder="Paste listing text here" value={form.raw_text} onChange={e => setForm({ ...form, raw_text: e.target.value })} />
          </div>
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Market Area</label>
              <input className="form-input" placeholder="e.g. District 2" value={form.market_area} onChange={e => setForm({ ...form, market_area: e.target.value })} />
            </div>
            <div className="form-group">
              <label className="form-label">Land Type</label>
              <input className="form-input" placeholder="e.g. ODT, ONT, TMDV" value={form.land_type} onChange={e => setForm({ ...form, land_type: e.target.value })} />
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Size (sqm)</label>
              <input className="form-input" placeholder="e.g. 80" type="number" value={form.size_sqm} onChange={e => setForm({ ...form, size_sqm: e.target.value })} />
            </div>
            <div className="form-group">
              <label className="form-label">Unit Price (VND)</label>
              <input className="form-input" placeholder="e.g. 40000000" type="number" value={form.unit_price} onChange={e => setForm({ ...form, unit_price: e.target.value })} />
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Asking Price (VND)</label>
              <input className="form-input" placeholder="e.g. 3500000000" type="number" value={form.asking_price} onChange={e => setForm({ ...form, asking_price: e.target.value })} />
            </div>
            <div className="form-group">
              <label className="form-label">Source Quality</label>
              <select className="form-select" value={form.source_quality} onChange={e => setForm({ ...form, source_quality: e.target.value })}>
                <option value="HIGH">HIGH</option>
                <option value="MEDIUM">MEDIUM</option>
                <option value="LOW">LOW</option>
                <option value="WEAK">WEAK</option>
              </select>
            </div>
          </div>
          <button className="btn btn-primary" type="submit">Add Candidate</button>
        </form>
      </section>
    </div>
  );
}

function PoolPage({ project }: { project: Project }) {
  const { data, error, loading, refetch } = useAsync<RawCandidate[]>(
    () => apiFetch(`/projects/${project.id}/raw-candidates`),
    [project.id],
  );
  const [actionMsg, setActionMsg] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  async function run(path: string, label: string) {
    setActionMsg(null);
    setActionError(null);
    try {
      const res = await apiFetch<Record<string, unknown>>(path, { method: 'POST' });
      setActionMsg(`${label} completed: ${JSON.stringify(res)}`);
    } catch (e) {
      setActionError(e instanceof Error ? e.message : String(e));
    }
    await refetch();
  }

  const totalCandidates = data?.length ?? 0;
  const duplicates = data?.filter(c => c.candidate_class === 'DUPLICATE').length ?? 0;
  const rejected = data?.filter(c => c.candidate_class === 'REJECT').length ?? 0;
  const passed = data?.filter(c => c.hard_filter_status === 'passed').length ?? 0;

  return (
    <div>
      <PipelineIndicator currentPage="pool" />
      <div className="page-header">
        <h1>Candidate Pool</h1>
        <p>Project: <strong>{project.name}</strong></p>
      </div>

      {actionMsg && <Alert msg={actionMsg} type="success" />}
      {actionError && <Alert msg={actionError} />}

      {/* Summary stats */}
      <div className="card-grid card-grid-auto" style={{ marginBottom: 20 }}>
        <div className="stat-card">
          <span className="stat-label">Total Candidates</span>
          <span className="stat-value">{totalCandidates}</span>
        </div>
        <div className="stat-card">
          <span className="stat-label">Duplicates</span>
          <span className="stat-value warning">{duplicates}</span>
        </div>
        <div className="stat-card">
          <span className="stat-label">Rejected</span>
          <span className="stat-value danger">{rejected}</span>
        </div>
        <div className="stat-card">
          <span className="stat-label">Passed Hard Filter</span>
          <span className="stat-value success">{passed}</span>
        </div>
      </div>

      {/* Action buttons */}
      <section className="card" style={{ marginBottom: 20 }}>
        <h3 className="card-title">Pipeline Actions</h3>
        <div className="flex gap-8">
          <button className="btn btn-primary" onClick={() => run(`/dedup/run/${project.id}`, 'Dedup')}>Run Dedup</button>
          <button className="btn btn-primary" onClick={() => run(`/hard-filter/run/${project.id}`, 'Hard Filter')}>Run Hard Filter</button>
        </div>
      </section>

      {/* Candidate table */}
      <section className="card">
        <h3 className="card-title">Candidates ({totalCandidates})</h3>
        {loading && <div className="loading-row"><span className="spinner" /> Loading...</div>}
        {error && <Alert msg={error} />}
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Market Area</th>
                <th>Land Type</th>
                <th>Size (sqm)</th>
                <th>Unit Price</th>
                <th>Class</th>
                <th>Dedup</th>
                <th>Hard Filter</th>
                <th>Rule Warnings</th>
              </tr>
            </thead>
            <tbody>
              {(data ?? []).map(c => (
                <tr key={c.id}>
                  <td className="mono">#{c.id}</td>
                  <td>{c.market_area ?? <span className="text-muted">-</span>}</td>
                  <td>{c.land_type ?? <span className="text-muted">-</span>}</td>
                  <td>{fmt(c.size_sqm)}</td>
                  <td>{fmt(c.unit_price)}</td>
                  <td>
                    <Badge text={c.candidate_class} variant={
                      c.candidate_class === 'DUPLICATE' ? 'warning' :
                      c.candidate_class === 'REJECT' ? 'danger' :
                      c.candidate_class === 'RECOMMENDED_TOP_10' ? 'accent' :
                      'muted'
                    } />
                  </td>
                  <td>
                    <span className="flex items-center gap-8">
                      <StatusDot status={c.dedup_status ?? ''} />
                      {c.dedup_status ?? <span className="text-muted">-</span>}
                    </span>
                  </td>
                  <td>
                    <span className="flex items-center gap-8">
                      <StatusDot status={c.hard_filter_status ?? ''} />
                      {c.hard_filter_status ?? <span className="text-muted">-</span>}
                    </span>
                  </td>
                  <td>
                    {c.adjustment_warnings && c.adjustment_warnings.length > 0 ? (
                      <div className="flex flex-col gap-8">
                        {c.adjustment_warnings.map((w, i) => (
                          <Badge key={i} text={w} variant="warning" />
                        ))}
                      </div>
                    ) : (
                      <span className="text-muted text-sm">none</span>
                    )}
                    {c.hard_filter_flags && c.hard_filter_flags.filter(f => !c.adjustment_warnings?.includes(f)).length > 0 && (
                      <div className="flex flex-col gap-8 mt-8" style={{ marginTop: 4 }}>
                        {c.hard_filter_flags.filter(f => !c.adjustment_warnings?.includes(f)).map((f, i) => (
                          <Badge key={i} text={f} variant="danger" />
                        ))}
                      </div>
                    )}
                  </td>
                </tr>
              ))}
              {totalCandidates === 0 && !loading && (
                <tr>
                  <td colSpan={9} className="text-center text-muted" style={{ padding: 24 }}>
                    No candidates yet. Add candidates first.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

function ExtractionPage({ project }: { project: Project }) {
  const { data, error, loading, refetch } = useAsync<ExtractionResultsResponse>(
    () => apiFetch(`/extraction/${project.id}`),
    [project.id],
  );
  const [actionMsg, setActionMsg] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  async function runExtraction() {
    setActionMsg(null);
    setActionError(null);
    try {
      const res = await apiFetch<Record<string, unknown>>(`/extraction/run/${project.id}`, { method: 'POST' });
      setActionMsg(`Extraction completed: ${JSON.stringify(res)}`);
    } catch (e) {
      setActionError(e instanceof Error ? e.message : String(e));
    }
    await refetch();
  }

  const results = data?.results ?? [];

  return (
    <div>
      <PipelineIndicator currentPage="extraction" />
      <div className="page-header">
        <h1>Extraction</h1>
        <p>Project: <strong>{project.name}</strong></p>
      </div>

      {actionMsg && <Alert msg={actionMsg} type="success" />}
      {actionError && <Alert msg={actionError} />}

      <section className="card" style={{ marginBottom: 20 }}>
        <h3 className="card-title">Run Extraction</h3>
        <p className="text-sm text-muted" style={{ marginBottom: 12 }}>
          FreeLLMAPI extracts and normalizes candidate fields from raw text.
        </p>
        <button className="btn btn-primary" onClick={runExtraction}>Run Extraction</button>
      </section>

      <section className="card">
        <h3 className="card-title">Extraction Results ({results.length})</h3>
        {loading && <div className="loading-row"><span className="spinner" /> Loading...</div>}
        {error && !error.includes('404') && <Alert msg={error} />}
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Raw Candidate</th>
                <th>Market Area</th>
                <th>Land Type</th>
                <th>Size (sqm)</th>
                <th>Unit Price</th>
                <th>Status</th>
                <th>Notes</th>
              </tr>
            </thead>
            <tbody>
              {results.map(r => (
                <tr key={r.id}>
                  <td className="mono">#{r.id}</td>
                  <td className="mono">#{r.raw_candidate_id}</td>
                  <td>{r.normalized_market_area ?? <span className="text-muted">-</span>}</td>
                  <td>{r.normalized_land_type ?? <span className="text-muted">-</span>}</td>
                  <td>{fmt(r.normalized_size_sqm)}</td>
                  <td>{fmt(r.normalized_unit_price)}</td>
                  <td>
                    <Badge text={r.extraction_status} variant={
                      r.extraction_status === 'completed' ? 'success' :
                      r.extraction_status === 'failed' ? 'danger' :
                      'muted'
                    } />
                  </td>
                  <td className="text-sm">{r.draft_note ?? <span className="text-muted">-</span>}</td>
                </tr>
              ))}
              {results.length === 0 && !loading && (
                <tr>
                  <td colSpan={8} className="text-center text-muted" style={{ padding: 24 }}>
                    No extraction results. Run extraction first.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

function ExportPage({ project }: { project: Project }) {
  const { data: top10Data, error: top10Error, loading: top10Loading, refetch: top10Refetch } = useAsync<Top10Response>(
    () => apiFetch(`/top10/${project.id}`),
    [project.id],
  );
  const { data: final3Data, refetch: final3Refetch } = useAsync<Final3Response>(
    () => apiFetch(`/projects/${project.id}/selections`),
    [project.id],
  );
  const { data: auditData, error: auditError, loading: auditLoading } = useAsync<AuditLogResponse>(
    () => apiFetch(`/audit-log/${project.id}`),
    [project.id],
  );
  const [selected, setSelected] = useState<number[]>([]);
  const [selectedBy, setSelectedBy] = useState('');
  const [msg, setMsg] = useState<string | null>(null);
  const [errMsg, setErrMsg] = useState<string | null>(null);

  const recommendations = top10Data?.recommendations ?? [];
  const selections = final3Data?.selections ?? [];
  const auditLogs = auditData?.logs ?? [];

  async function scoring() {
    setMsg(null);
    setErrMsg(null);
    try {
      const res = await apiFetch<Record<string, unknown>>(`/scoring/run/${project.id}`, { method: 'POST' });
      setMsg(`Scoring & Top 10 completed: ${JSON.stringify(res)}`);
    } catch (e) {
      setErrMsg(e instanceof Error ? e.message : String(e));
    }
    await top10Refetch();
    await final3Refetch();
  }

  async function exportWorkbook() {
    setMsg(null);
    setErrMsg(null);
    try {
      const res = await apiFetch<ExportResponse>(`/export/${project.id}`, { method: 'POST' });
      setMsg(`Export created: ID=${res.export_record_id}, status=${res.status}, path=${res.file_path ?? 'N/A'}`);
    } catch (e) {
      setErrMsg(e instanceof Error ? e.message : String(e));
    }
  }

  async function saveFinal3() {
    setMsg(null);
    setErrMsg(null);
    if (selected.length === 0) {
      setErrMsg('Please select at least one candidate.');
      return;
    }
    if (selected.length > 3) {
      setErrMsg('Cannot select more than 3 candidates.');
      return;
    }
    if (!selectedBy.trim()) {
      setErrMsg('Please enter analyst name.');
      return;
    }
    try {
      const res = await apiFetch<Record<string, unknown>>(`/projects/${project.id}/select-final3`, {
        method: 'POST',
        body: JSON.stringify({
          eligible_candidate_ids: selected,
          selected_by: selectedBy.trim(),
          override_reason: null,
        }),
      });
      setMsg(`Final 3 saved: ${JSON.stringify(res)}`);
    } catch (e) {
      setErrMsg(e instanceof Error ? e.message : String(e));
    }
    await final3Refetch();
  }

  function toggle(id: number) {
    setSelected(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);
  }

  // Pre-select the current Final 3 candidates
  useEffect(() => {
    if (selections.length > 0) {
      setSelected(selections.map(s => s.eligible_candidate_id));
    }
  }, [selections]);

  return (
    <div>
      <PipelineIndicator currentPage="export" />
      <div className="page-header">
        <h1>Export & Audit</h1>
        <p>Project: <strong>{project.name}</strong></p>
      </div>

      {msg && <Alert msg={msg} type="success" />}
      {errMsg && <Alert msg={errMsg} />}

      {/* Scoring & Top 10 */}
      <section className="card" style={{ marginBottom: 20 }}>
        <h3 className="card-title">Step 1: Scoring & Top 10</h3>
        <p className="text-sm text-muted" style={{ marginBottom: 12 }}>
          Run deterministic scoring on eligible candidates and generate Top 10 recommendations.
        </p>
        <button className="btn btn-primary" onClick={scoring}>Run Scoring & Top 10</button>

        {top10Loading && <div className="loading-row" style={{ marginTop: 16 }}><span className="spinner" /> Loading...</div>}
        {top10Error && !top10Error.includes('404') && <Alert msg={top10Error} />}

        {recommendations.length > 0 && (
          <div className="table-wrapper" style={{ marginTop: 16 }}>
            <table>
              <thead>
                <tr>
                  <th>Rank</th>
                  <th>Eligible ID</th>
                  <th>Market Area</th>
                  <th>Land Type</th>
                  <th>Size (sqm)</th>
                  <th>Unit Price</th>
                  <th>Total Score</th>
                  <th>Adj. Ratio</th>
                </tr>
              </thead>
              <tbody>
                {recommendations.map(r => (
                  <tr key={r.rank} className={r.rank <= 3 ? 'fade-in' : ''}>
                    <td><strong>#{r.rank}</strong></td>
                    <td className="mono">#{r.eligible_candidate_id}</td>
                    <td>{r.candidate?.market_area ?? '-'}</td>
                    <td>{r.candidate?.land_type ?? '-'}</td>
                    <td>{fmt(r.candidate?.size_sqm)}</td>
                    <td>{fmt(r.candidate?.unit_price)}</td>
                    <td><strong>{r.scores?.total_score?.toFixed(2) ?? '-'}</strong></td>
                    <td>{r.scores?.adjustment_ratio != null ? fmtPct(r.scores.adjustment_ratio) : '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* Final 3 Selection */}
      <section className="card" style={{ marginBottom: 20 }}>
        <h3 className="card-title">Step 2: Final 3 Selection (Analyst)</h3>
        <p className="text-sm text-muted" style={{ marginBottom: 12 }}>
          Select up to 3 candidates for the final valuation. This decision must be made by the analyst, not by LLM.
        </p>

        {selections.length > 0 && (
          <div className="alert alert-info" style={{ marginBottom: 16 }}>
            <strong>Current selections:</strong> {selections.map(s => `#${s.eligible_candidate_id}`).join(', ')} (by {selections[0]?.selected_by ?? 'unknown'})
            {selections.some(s => s.is_override) && <span> — <Badge text="OVERRIDE" variant="warning" /></span>}
          </div>
        )}

        {recommendations.length > 0 && (
          <div className="table-wrapper" style={{ marginBottom: 16 }}>
            <table>
              <thead>
                <tr>
                  <th style={{ width: 40 }}>Select</th>
                  <th>Rank</th>
                  <th>Eligible ID</th>
                  <th>Market Area</th>
                  <th>Land Type</th>
                  <th>Size (sqm)</th>
                  <th>Unit Price</th>
                  <th>Score</th>
                </tr>
              </thead>
              <tbody>
                {recommendations.map(r => (
                  <tr key={r.rank}>
                    <td style={{ textAlign: 'center' }}>
                      <input
                        type="checkbox"
                        checked={selected.includes(r.eligible_candidate_id)}
                        onChange={() => toggle(r.eligible_candidate_id)}
                        disabled={!selected.includes(r.eligible_candidate_id) && selected.length >= 3}
                      />
                    </td>
                    <td>#{r.rank}</td>
                    <td className="mono">#{r.eligible_candidate_id}</td>
                    <td>{r.candidate?.market_area ?? '-'}</td>
                    <td>{r.candidate?.land_type ?? '-'}</td>
                    <td>{fmt(r.candidate?.size_sqm)}</td>
                    <td>{fmt(r.candidate?.unit_price)}</td>
                    <td><strong>{r.scores?.total_score?.toFixed(2) ?? '-'}</strong></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <div className="flex items-center gap-8" style={{ flexWrap: 'wrap' }}>
          <input
            className="form-input"
            style={{ width: 220 }}
            placeholder="Analyst name"
            value={selectedBy}
            onChange={e => setSelectedBy(e.target.value)}
          />
          <button className="btn btn-success" onClick={saveFinal3} disabled={selected.length === 0 || !selectedBy.trim()}>
            Confirm Final {selected.length}
          </button>
          <span className="text-sm text-muted">
            {selected.length}/3 selected
          </span>
        </div>
      </section>

      {/* Export */}
      <section className="card" style={{ marginBottom: 20 }}>
        <h3 className="card-title">Step 3: Export Workbook</h3>
        <p className="text-sm text-muted" style={{ marginBottom: 12 }}>
          Generate the audit workbook with all pipeline data.
        </p>
        <button className="btn btn-primary" onClick={exportWorkbook}>Export Workbook</button>
      </section>

      {/* Audit Log */}
      <section className="card">
        <h3 className="card-title">Step 4: Audit Log</h3>
        <p className="text-sm text-muted" style={{ marginBottom: 12 }}>
          All actions recorded in the audit trail.
        </p>
        {auditLoading && <div className="loading-row"><span className="spinner" /> Loading...</div>}
        {auditError && !auditError.includes('404') && <Alert msg={auditError} />}
        {auditLogs.length > 0 ? (
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Action</th>
                  <th>Actor</th>
                  <th>Details</th>
                  <th>Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {auditLogs.map(log => (
                  <tr key={log.id}>
                    <td className="mono">#{log.id}</td>
                    <td><Badge text={log.action} variant="accent" /></td>
                    <td>{log.actor}</td>
                    <td className="text-sm mono" style={{ maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {log.details_json ?? '-'}
                    </td>
                    <td className="text-sm">{log.created_at?.slice(0, 19) ?? '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="empty-state">
            <p>No audit log entries yet.</p>
          </div>
        )}
      </section>
    </div>
  );
}

// ============================================================
// TSSS Brain Page
// ============================================================
function TsssBrainPage({ project }: { project: Project }) {
  const { data: statusData, error: statusError, loading: statusLoading } = useAsync<Record<string, unknown>>(
    () => apiFetch(`/projects/${project.id}/tsss-brain/status`),
    [project.id],
  );

  const [queriesResult, setQueriesResult] = useState<Record<string, unknown> | null>(null);
  const [queriesLoading, setQueriesLoading] = useState(false);
  const [queriesError, setQueriesError] = useState<string | null>(null);

  const [rawText, setRawText] = useState('');
  const [sourceUrl, setSourceUrl] = useState('');
  const [createRawCandidate, setCreateRawCandidate] = useState(false);
  const [extractResult, setExtractResult] = useState<Record<string, unknown> | null>(null);
  const [extractLoading, setExtractLoading] = useState(false);
  const [extractError, setExtractError] = useState<string | null>(null);

  async function suggestQueries() {
    setQueriesLoading(true);
    setQueriesError(null);
    setQueriesResult(null);
    try {
      const res = await apiFetch<Record<string, unknown>>(`/projects/${project.id}/tsss-brain/suggest-queries`, { method: 'POST' });
      setQueriesResult(res);
    } catch (e) {
      setQueriesError(e instanceof Error ? e.message : String(e));
    } finally {
      setQueriesLoading(false);
    }
  }

  async function extractCandidate() {
    if (!rawText.trim()) {
      setExtractError('raw_text is required.');
      return;
    }
    setExtractLoading(true);
    setExtractError(null);
    setExtractResult(null);
    try {
      const res = await apiFetch<Record<string, unknown>>(`/projects/${project.id}/tsss-brain/extract-candidate`, {
        method: 'POST',
        body: JSON.stringify({
          source_url: sourceUrl || null,
          raw_text: rawText,
          create_raw_candidate: createRawCandidate,
        }),
      });
      setExtractResult(res);
    } catch (e) {
      setExtractError(e instanceof Error ? e.message : String(e));
    } finally {
      setExtractLoading(false);
    }
  }

  const subjectAsset = statusData?.subject_asset_summary as Record<string, unknown> | undefined;

  return (
    <div>
      <div className="page-header">
        <h1>TSSS Brain</h1>
        <p>Project: <strong>{project.name}</strong></p>
        <p className="text-sm text-muted" style={{ marginTop: 4 }}>
          AI hỗ trợ trích xuất và gợi ý; không thay thế kiểm chứng TSSS và không tự quyết Final 3.
        </p>
      </div>

      {/* Status alert */}
      {statusLoading && <div className="loading-row"><span className="spinner" /> Loading...</div>}
      {statusError && <Alert msg={statusError} />}

      {/* Subject Asset Summary */}
      {subjectAsset && (
        <section className="card" style={{ marginBottom: 20 }}>
          <h3 className="card-title">Subject Asset Summary</h3>
          <div className="card-grid card-grid-3">
            <div className="stat-card">
              <span className="stat-label">Address</span>
              <span className="stat-value" style={{ fontSize: '1.1rem' }}>{(subjectAsset.subject_asset as Record<string, unknown>)?.address as string ?? '-'}</span>
            </div>
            <div className="stat-card">
              <span className="stat-label">Market Area</span>
              <span className="stat-value" style={{ fontSize: '1.1rem' }}>{(subjectAsset.subject_asset as Record<string, unknown>)?.market_area as string ?? '-'}</span>
            </div>
            <div className="stat-card">
              <span className="stat-label">Land Type</span>
              <span className="stat-value" style={{ fontSize: '1.1rem' }}>{(subjectAsset.subject_asset as Record<string, unknown>)?.land_type as string ?? '-'}</span>
            </div>
            <div className="stat-card">
              <span className="stat-label">Size (sqm)</span>
              <span className="stat-value" style={{ fontSize: '1.1rem' }}>{fmt((subjectAsset.subject_asset as Record<string, unknown>)?.size_sqm as number | null)}</span>
            </div>
          </div>
          {Boolean((subjectAsset as Record<string, unknown>).brief) && (
            <p className="text-sm text-muted" style={{ marginTop: 8 }}>{String((subjectAsset as Record<string, unknown>).brief)}</p>
          )}
        </section>
      )}

      {!subjectAsset && !statusLoading && (
        <div className="alert alert-warning" style={{ marginBottom: 20 }}>
          No subject asset found. Please create a subject asset first on the Subject Asset page.
        </div>
      )}

      {/* Suggest Search Queries */}
      <section className="card" style={{ marginBottom: 20 }}>
        <h3 className="card-title">Suggest Search Queries</h3>
        <p className="text-sm text-muted" style={{ marginBottom: 12 }}>
          Use OmniRoute LLM to generate search query suggestions for finding comparable properties.
        </p>
        <button className="btn btn-primary" onClick={suggestQueries} disabled={!subjectAsset || queriesLoading}>
          {queriesLoading ? <><span className="spinner" /> Generating...</> : 'Suggest Search Queries'}
        </button>
        {queriesError && <Alert msg={queriesError} />}
        {queriesResult && (
          <div className="table-wrapper" style={{ marginTop: 16 }}>
            <pre className="mono" style={{ background: 'var(--bg-base)', padding: 16, borderRadius: 'var(--radius-sm)', overflow: 'auto', fontSize: '0.82rem', maxHeight: 400 }}>
              {JSON.stringify(queriesResult, null, 2)}
            </pre>
          </div>
        )}
      </section>

      {/* Extract Candidate */}
      <section className="card" style={{ marginBottom: 20 }}>
        <h3 className="card-title">Extract Candidate from Raw Text</h3>
        <p className="text-sm text-muted" style={{ marginBottom: 12 }}>
          Paste a raw listing text below to extract candidate fields using OmniRoute LLM.
        </p>

        <div className="form-group">
          <label className="form-label">Source URL</label>
          <input
            className="form-input"
            placeholder="https://example.com/listing (optional)"
            value={sourceUrl}
            onChange={e => setSourceUrl(e.target.value)}
          />
        </div>

        <div className="form-group">
          <label className="form-label">Raw Listing Text</label>
          <textarea
            className="form-textarea"
            placeholder="Paste the listing text here..."
            value={rawText}
            onChange={e => setRawText(e.target.value)}
            rows={8}
          />
        </div>

        <div className="form-group" style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
          <input
            type="checkbox"
            id="createRawCandidate"
            checked={createRawCandidate}
            onChange={e => setCreateRawCandidate(e.target.checked)}
            style={{ width: 18, height: 18 }}
          />
          <label htmlFor="createRawCandidate" className="form-label" style={{ margin: 0 }}>
            Create Raw Candidate (adds to candidate pool, does not bypass dedup/hard-filter/scoring)
          </label>
        </div>

        <button className="btn btn-primary" onClick={extractCandidate} disabled={!subjectAsset || extractLoading || !rawText.trim()}>
          {extractLoading ? <><span className="spinner" /> Extracting...</> : 'Extract Candidate'}
        </button>
        {extractError && <Alert msg={extractError} />}
        {extractResult && (
          <div className="table-wrapper" style={{ marginTop: 16 }}>
            <pre className="mono" style={{ background: 'var(--bg-base)', padding: 16, borderRadius: 'var(--radius-sm)', overflow: 'auto', fontSize: '0.82rem', maxHeight: 400 }}>
              {JSON.stringify(extractResult, null, 2)}
            </pre>
          </div>
        )}
      </section>

      {/* AI Disclaimer */}
      <div className="alert alert-warning">
        <strong>AI hỗ trợ trích xuất và gợi ý; không thay thế kiểm chứng TSSS và không tự quyết Final 3.</strong>
        <br />
        OmniRoute là cổng LLM, không phải công cụ tìm kiếm web. Luôn kiểm chứng dữ liệu độc lập.
        Việc chọn Final 3 là quyết định của chuyên viên thẩm định, không phải AI.
      </div>
    </div>
  );
}

// ============================================================
// App Component
// ============================================================
type Page =
  | 'projects'
  | 'gateway'
  | 'subject'
  | 'add'
  | 'pool'
  | 'extraction'
  | 'export'
  | 'tsss_brain';

export function App() {
  const [page, setPage] = useState<Page>('projects');
  const [project, setProject] = useState<Project | null>(null);

  function nav(p: Page) {
    if (!project && !['projects', 'gateway'].includes(p)) {
      setPage('projects');
      return;
    }
    setPage(p);
  }

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <h2>ValCo TSSS</h2>
          <p>MVP Phase 3</p>
          <p style={{ fontSize: '0.65rem', color: 'var(--text-muted)', marginTop: 4 }}>Pipeline Dashboard</p>
        </div>

        {project && (
          <div className="nav-section" style={{ padding: '0 12px', marginBottom: 12 }}>
            <div className="nav-section-label">Project</div>
            <div className="flex items-center gap-8" style={{ padding: '4px 8px' }}>
              <span className="text-sm" style={{ fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: 140 }}>{project.name}</span>
              <button className="btn btn-ghost btn-sm" style={{ marginLeft: 'auto', padding: '2px 8px', fontSize: '0.7rem' }} onClick={() => { setProject(null); setPage('projects'); }}>Change</button>
            </div>
          </div>
        )}

        <div className="nav-section">
          <div className="nav-section-label">Management</div>
          <button className={`nav-item ${page === 'projects' ? 'active' : ''}`} onClick={() => nav('projects')}>
            <span className="icon">📋</span> Projects
          </button>
          <button className={`nav-item ${page === 'gateway' ? 'active' : ''}`} onClick={() => nav('gateway')}>
            <span className="icon">🔌</span> Gateway Health
          </button>
        </div>

        <div className="nav-section">
          <div className="nav-section-label">Pipeline</div>
          <button className={`nav-item ${page === 'subject' ? 'active' : ''}`} disabled={!project} onClick={() => nav('subject')}>
            <span className="icon">🏠</span> Subject Asset
          </button>
          <button className={`nav-item ${page === 'add' ? 'active' : ''}`} disabled={!project} onClick={() => nav('add')}>
            <span className="icon">➕</span> Add Candidate
          </button>
          <button className={`nav-item ${page === 'pool' ? 'active' : ''}`} disabled={!project} onClick={() => nav('pool')}>
            <span className="icon">📊</span> Candidate Pool
          </button>
          <button className={`nav-item ${page === 'extraction' ? 'active' : ''}`} disabled={!project} onClick={() => nav('extraction')}>
            <span className="icon">🔍</span> Extraction
          </button>
          <button className={`nav-item ${page === 'export' ? 'active' : ''}`} disabled={!project} onClick={() => nav('export')}>
            <span className="icon">📤</span> Export & Audit
          </button>
        </div>

        <div className="nav-section">
          <div className="nav-section-label">AI-Assist</div>
          <button className={`nav-item ${page === 'tsss_brain' ? 'active' : ''}`} disabled={!project} onClick={() => nav('tsss_brain')}>
            <span className="icon">🧠</span> TSSS Brain
          </button>
        </div>
      </aside>

      <main className="main-content">
        {page === 'projects' && <ProjectsPage onOpen={(p) => { setProject(p); setPage('subject'); }} />}
        {page === 'gateway' && <GatewayPage />}
        {project && page === 'subject' && <SubjectPage project={project} />}
        {project && page === 'add' && <AddCandidatePage project={project} />}
        {project && page === 'pool' && <PoolPage project={project} />}
        {project && page === 'extraction' && <ExtractionPage project={project} />}
        {project && page === 'export' && <ExportPage project={project} />}
        {project && page === 'tsss_brain' && <TsssBrainPage project={project} />}
      </main>
    </div>
  );
}
