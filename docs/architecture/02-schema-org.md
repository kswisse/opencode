### Component Interaction Flow

```
User Request Flow:
==================

1. Client -> API Gateway: HTTPS request + JWT
2. API Gateway -> Auth Service: Validate JWT
3. Auth Service -> API Gateway: Valid + permissions
4. API Gateway -> Target Service: Forward with context
5. Target Service -> Kafka: Emit domain event
6. Target Service -> PostgreSQL: Persist data
7. Target Service -> Redis: Cache/invalidate
8. Target Service -> API Gateway: Response
9. API Gateway -> Client: HTTPS response

Agent Execution Flow:
=====================

1. Scheduler Service -> Kafka: "agent.execute" event
2. Agent Service -> Redis: Acquire agent lock
3. Agent Service -> Memory Service: Retrieve context
4. Agent Service -> Tool Service: Execute tools
5. Agent Service -> Memory Service: Store results
6. Agent Service -> Task Service: Update progress
7. Agent Service -> Kafka: "agent.completed" event
8. Monitoring Service -> Prometheus: Record metrics
```

---

## 2. Complete Database Schema

### 2.1 Companies & Organization

```sql
-- =============================================================================
-- COMPANIES & ORGANIZATION SCHEMA
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Companies (Tenant root)
CREATE TABLE companies (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name                VARCHAR(255) NOT NULL,
    slug                VARCHAR(255) NOT NULL UNIQUE,
    legal_name          VARCHAR(500),
    tax_id              VARCHAR(100),
    billing_email       VARCHAR(255) NOT NULL,
    primary_contact_id  UUID,
    plan                VARCHAR(50) NOT NULL DEFAULT 'free' CHECK (plan IN ('free', 'starter', 'professional', 'enterprise', 'custom')),
    plan_expires_at     TIMESTAMPTZ,
    status              VARCHAR(50) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'cancelled', 'pending')),
    settings            JSONB NOT NULL DEFAULT '{}',
    metadata            JSONB NOT NULL DEFAULT '{}',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at          TIMESTAMPTZ
);

CREATE INDEX idx_companies_slug ON companies(slug);
CREATE INDEX idx_companies_status ON companies(status);
CREATE INDEX idx_companies_plan ON companies(plan);

-- Departments
CREATE TABLE departments (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id          UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    parent_id           UUID REFERENCES departments(id),
    name                VARCHAR(255) NOT NULL,
    description         TEXT,
    budget_limit        NUMERIC(15, 2),
    manager_id          UUID,
    status              VARCHAR(50) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'archived')),
    settings            JSONB NOT NULL DEFAULT '{}',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at          TIMESTAMPTZ,
    UNIQUE(company_id, name)
);

CREATE INDEX idx_departments_company ON departments(company_id);
CREATE INDEX idx_departments_parent ON departments(parent_id);

-- Teams
CREATE TABLE teams (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id          UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    department_id       UUID REFERENCES departments(id) ON DELETE SET NULL,
    name                VARCHAR(255) NOT NULL,
    description         TEXT,
    lead_id             UUID,
    max_agents          INTEGER DEFAULT 100,
    budget_limit        NUMERIC(15, 2),
    status              VARCHAR(50) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'archived')),
    settings            JSONB NOT NULL DEFAULT '{}',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at          TIMESTAMPTZ,
    UNIQUE(company_id, name)
);

CREATE INDEX idx_teams_company ON teams(company_id);
CREATE INDEX idx_teams_department ON teams(department_id);

-- Users (Platform users / Humans)
CREATE TABLE users (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email               VARCHAR(255) NOT NULL UNIQUE,
    password_hash       VARCHAR(255) NOT NULL,
    email_verified      BOOLEAN NOT NULL DEFAULT FALSE,
    mfa_enabled         BOOLEAN NOT NULL DEFAULT FALSE,
    mfa_secret          VARCHAR(255),
    first_name          VARCHAR(100),
    last_name           VARCHAR(100),
    avatar_url          TEXT,
    status              VARCHAR(50) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'pending')),
    last_login_at       TIMESTAMPTZ,
    metadata            JSONB NOT NULL DEFAULT '{}',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at          TIMESTAMPTZ
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_status ON users(status);

-- Company Memberships (User <-> Company)
CREATE TABLE company_memberships (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id          UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role                VARCHAR(50) NOT NULL DEFAULT 'member' CHECK (role IN ('owner', 'admin', 'manager', 'member', 'viewer')),
    department_id       UUID REFERENCES departments(id) ON DELETE SET NULL,
    team_id             UUID REFERENCES teams(id) ON DELETE SET NULL,
    status              VARCHAR(50) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'invited', 'suspended')),
    invited_at          TIMESTAMPTZ,
    accepted_at         TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(company_id, user_id)
);

CREATE INDEX idx_company_memberships_company ON company_memberships(company_id);
CREATE INDEX idx_company_memberships_user ON company_memberships(user_id);
CREATE INDEX idx_company_memberships_role ON company_memberships(role);
```
