### 2.2 Agents & Capabilities

```sql
-- =============================================================================
-- AGENTS & CAPABILITIES SCHEMA
-- =============================================================================

-- Agent Templates (Reusable agent blueprints)
CREATE TABLE agent_templates (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id          UUID REFERENCES companies(id) ON DELETE SET NULL,
    name                VARCHAR(255) NOT NULL,
    slug                VARCHAR(255) NOT NULL UNIQUE,
    description         TEXT,
    category            VARCHAR(100) NOT NULL,
    icon_url            TEXT,
    model_provider      VARCHAR(100) NOT NULL,
    model_name          VARCHAR(255) NOT NULL,
    system_prompt       TEXT NOT NULL,
    config_schema       JSONB NOT NULL DEFAULT '{}',
    default_config      JSONB NOT NULL DEFAULT '{}',
    required_tools      TEXT[] DEFAULT '{}',
    optional_tools      TEXT[] DEFAULT '{}',
    estimated_cost_per_task NUMERIC(10, 6),
    is_public           BOOLEAN NOT NULL DEFAULT FALSE,
    version             VARCHAR(50) NOT NULL DEFAULT '1.0.0',
    downloads           INTEGER DEFAULT 0,
    rating              NUMERIC(3, 2) DEFAULT 0.00,
    rating_count        INTEGER DEFAULT 0,
    status              VARCHAR(50) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'deprecated', 'draft', 'review')),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at          TIMESTAMPTZ
);

CREATE INDEX idx_agent_templates_company ON agent_templates(company_id);
CREATE INDEX idx_agent_templates_category ON agent_templates(category);
CREATE INDEX idx_agent_templates_public ON agent_templates(is_public);

-- Template Reviews
CREATE TABLE template_reviews (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    template_id         UUID NOT NULL REFERENCES agent_templates(id) ON DELETE CASCADE,
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    rating              INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    title               VARCHAR(255),
    content             TEXT,
    helpful_count       INTEGER DEFAULT 0,
    status              VARCHAR(50) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'flagged', 'removed')),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(template_id, user_id)
);

CREATE INDEX idx_template_reviews_template ON template_reviews(template_id);

-- Template Installs
CREATE TABLE template_installs (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    template_id         UUID NOT NULL REFERENCES agent_templates(id) ON DELETE CASCADE,
    company_id          UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    custom_config       JSONB NOT NULL DEFAULT '{}',
    version_installed   VARCHAR(50) NOT NULL,
    installed_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(template_id, company_id)
);

-- Agents
CREATE TABLE agents (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id          UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    team_id             UUID REFERENCES teams(id) ON DELETE SET NULL,
    template_id         UUID REFERENCES agent_templates(id) ON DELETE SET NULL,
    name                VARCHAR(255) NOT NULL,
    description         TEXT,
    avatar_url          TEXT,
    agent_type          VARCHAR(100) NOT NULL DEFAULT 'general' CHECK (agent_type IN ('general', 'specialist', 'orchestrator', 'monitor', 'custom')),
    model_provider      VARCHAR(100) NOT NULL,
    model_name          VARCHAR(255) NOT NULL,
    system_prompt       TEXT NOT NULL,
    config              JSONB NOT NULL DEFAULT '{}',
    capabilities        TEXT[] DEFAULT '{}',
    status              VARCHAR(50) NOT NULL DEFAULT 'idle' CHECK (status IN ('idle', 'running', 'paused', 'error', 'terminated', 'maintenance')),
    health_status       VARCHAR(50) NOT NULL DEFAULT 'healthy' CHECK (health_status IN ('healthy', 'degraded', 'unhealthy', 'unknown')),
    last_active_at      TIMESTAMPTZ,
    last_error          TEXT,
    total_tasks_completed INTEGER DEFAULT 0,
    total_tasks_failed  INTEGER DEFAULT 0,
    avg_completion_time_ms INTEGER,
    cost_per_hour       NUMERIC(10, 6),
    total_cost          NUMERIC(15, 6) DEFAULT 0.00,
    max_concurrent_tasks INTEGER DEFAULT 1,
    current_task_count  INTEGER DEFAULT 0,
    priority            INTEGER DEFAULT 5 CHECK (priority BETWEEN 1 AND 10),
    tags                TEXT[] DEFAULT '{}',
    metadata            JSONB NOT NULL DEFAULT '{}',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    terminated_at       TIMESTAMPTZ,
    deleted_at          TIMESTAMPTZ
);

CREATE INDEX idx_agents_company ON agents(company_id);
CREATE INDEX idx_agents_team ON agents(team_id);
CREATE INDEX idx_agents_status ON agents(status);
CREATE INDEX idx_agents_type ON agents(agent_type);
CREATE INDEX idx_agents_health ON agents(health_status);
CREATE INDEX idx_agents_tags ON agents USING GIN(tags);

-- Agent Capabilities (Extended capability definitions)
CREATE TABLE agent_capabilities (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id            UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    capability_name     VARCHAR(255) NOT NULL,
    capability_type     VARCHAR(100) NOT NULL CHECK (capability_type IN ('skill', 'tool_access', 'knowledge', 'integration', 'custom')),
    description         TEXT,
    proficiency_level   INTEGER DEFAULT 5 CHECK (proficiency_level BETWEEN 1 AND 10),
    config              JSONB NOT NULL DEFAULT '{}',
    is_enabled          BOOLEAN NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(agent_id, capability_name)
);

CREATE INDEX idx_agent_capabilities_agent ON agent_capabilities(agent_id);

-- Agent Sessions (Execution sessions)
CREATE TABLE agent_sessions (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id            UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    company_id          UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    session_type        VARCHAR(100) NOT NULL DEFAULT 'task' CHECK (session_type IN ('task', 'conversation', 'maintenance', 'training')),
    status              VARCHAR(50) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'completed', 'failed', 'timeout', 'cancelled')),
    started_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at            TIMESTAMPTZ,
    duration_ms         INTEGER,
    tokens_input        INTEGER DEFAULT 0,
    tokens_output       INTEGER DEFAULT 0,
    tokens_total        INTEGER DEFAULT 0,
    cost                NUMERIC(10, 6) DEFAULT 0.00,
    model_used          VARCHAR(255),
    tools_used          TEXT[] DEFAULT '{}',
    error_message       TEXT,
    metadata            JSONB NOT NULL DEFAULT '{}',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_agent_sessions_agent ON agent_sessions(agent_id);
CREATE INDEX idx_agent_sessions_company ON agent_sessions(company_id);
CREATE INDEX idx_agent_sessions_status ON agent_sessions(status);
CREATE INDEX idx_agent_sessions_started ON agent_sessions(started_at DESC);
```
