CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE projects (
  id UUID PRIMARY KEY,
  name TEXT NOT NULL,
  owner_team TEXT,
  caido_instance_id TEXT,
  status TEXT NOT NULL DEFAULT 'active',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE scope_manifests (
  id UUID PRIMARY KEY,
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  allowed_hosts JSONB NOT NULL,
  allowed_schemes JSONB NOT NULL DEFAULT '["https"]'::jsonb,
  allowed_ports JSONB NOT NULL DEFAULT '[443]'::jsonb,
  allowed_check_families JSONB NOT NULL DEFAULT '[]'::jsonb,
  blocked_check_families JSONB NOT NULL DEFAULT '[]'::jsonb,
  max_rps INTEGER NOT NULL DEFAULT 2,
  approval_rules_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE assets (
  id UUID PRIMARY KEY,
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  asset_type TEXT NOT NULL,
  value TEXT NOT NULL,
  environment TEXT,
  in_scope BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE auth_contexts (
  id UUID PRIMARY KEY,
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  label TEXT NOT NULL,
  context_hash TEXT NOT NULL,
  notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE caido_requests (
  id UUID PRIMARY KEY,
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  caido_request_id TEXT NOT NULL,
  method TEXT NOT NULL,
  url TEXT NOT NULL,
  host TEXT NOT NULL,
  path TEXT NOT NULL,
  status_code INTEGER,
  req_headers_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  resp_headers_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  req_body_hash TEXT,
  resp_body_hash TEXT,
  auth_context_id UUID REFERENCES auth_contexts(id) ON DELETE SET NULL,
  seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_caido_requests_project_host_path ON caido_requests(project_id, host, path);
CREATE INDEX idx_caido_requests_seen_at ON caido_requests(seen_at DESC);

CREATE TABLE endpoints (
  id UUID PRIMARY KEY,
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  method TEXT NOT NULL,
  route_pattern TEXT NOT NULL,
  content_type TEXT,
  auth_required BOOLEAN,
  first_seen TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  last_seen TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  source_confidence NUMERIC(5,4) NOT NULL DEFAULT 0.5000
);

CREATE UNIQUE INDEX uq_endpoints_project_method_route ON endpoints (project_id, method, route_pattern);

CREATE TABLE parameters (
  id UUID PRIMARY KEY,
  endpoint_id UUID NOT NULL REFERENCES endpoints(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  location TEXT NOT NULL,
  datatype_guess TEXT,
  example_values_json JSONB NOT NULL DEFAULT '[]'::jsonb,
  sensitivity_guess TEXT
);

CREATE TABLE evidence_bundles (
  id UUID PRIMARY KEY,
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  storage_key TEXT NOT NULL,
  summary TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE findings (
  id UUID PRIMARY KEY,
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  source TEXT NOT NULL,
  bug_class TEXT NOT NULL,
  severity TEXT,
  confidence NUMERIC(5,4),
  status TEXT NOT NULL DEFAULT 'draft',
  evidence_bundle_id UUID REFERENCES evidence_bundles(id) ON DELETE SET NULL,
  draft_report_md TEXT,
  validated_by_user_id TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_findings_project_created ON findings (project_id, created_at DESC);

CREATE TABLE hypotheses (
  id UUID PRIMARY KEY,
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  bug_class TEXT NOT NULL,
  rationale TEXT NOT NULL,
  supporting_evidence_json JSONB NOT NULL DEFAULT '[]'::jsonb,
  proposed_template_id UUID,
  priority_score NUMERIC(5,4) NOT NULL DEFAULT 0.5000,
  confidence_score NUMERIC(5,4) NOT NULL DEFAULT 0.5000,
  status TEXT NOT NULL DEFAULT 'queued',
  human_approval_required BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE research_items (
  id UUID PRIMARY KEY,
  source_name TEXT NOT NULL,
  source_url TEXT NOT NULL,
  published_at TIMESTAMPTZ,
  content_hash TEXT NOT NULL,
  summary TEXT NOT NULL,
  extracted_patterns_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  approved_for_learning BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE feedback_events (
  id UUID PRIMARY KEY,
  object_type TEXT NOT NULL,
  object_id UUID NOT NULL,
  feedback_type TEXT NOT NULL,
  user_id TEXT NOT NULL,
  notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE templates (
  id UUID PRIMARY KEY,
  bug_class TEXT NOT NULL,
  name TEXT NOT NULL,
  description TEXT NOT NULL,
  input_requirements_json JSONB NOT NULL DEFAULT '[]'::jsonb,
  workflow_ref TEXT,
  approval_level TEXT NOT NULL DEFAULT 'analyst',
  deterministic BOOLEAN NOT NULL DEFAULT TRUE,
  version TEXT NOT NULL DEFAULT '1.0.0',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE model_runs (
  id UUID PRIMARY KEY,
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  model_name TEXT NOT NULL,
  prompt_hash TEXT NOT NULL,
  input_refs_json JSONB NOT NULL DEFAULT '[]'::jsonb,
  output_ref TEXT,
  cost NUMERIC(12,6),
  latency_ms INTEGER,
  safety_flags_json JSONB NOT NULL DEFAULT '[]'::jsonb,
  approved BOOLEAN,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE retrieval_documents (
  id UUID PRIMARY KEY,
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  doc_type TEXT NOT NULL,
  source_ref TEXT,
  content TEXT NOT NULL,
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  embedding vector(1536),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_retrieval_documents_project_type ON retrieval_documents(project_id, doc_type);
