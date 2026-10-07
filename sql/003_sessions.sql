-- Dream sessions, turns, retrieval audit, conclusions

CREATE TABLE sessions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_user_id   TEXT,
    language        TEXT NOT NULL DEFAULT 'ar',
    state           TEXT NOT NULL DEFAULT 'created'
                    CHECK (state IN (
                        'created',
                        'questionnaire_complete',
                        'dream_submitted',
                        'awaiting_followups',
                        'ready_to_conclude',
                        'retrieving',
                        'verifying',
                        'drafting',
                        'concluded',
                        'refused',
                        'expired',
                        'purged'
                    )),
    questionnaire   JSONB NOT NULL DEFAULT '{}'::jsonb,
    accumulated_facts JSONB NOT NULL DEFAULT '{}'::jsonb,
    follow_up_round INT NOT NULL DEFAULT 0,
    max_follow_up_rounds INT NOT NULL DEFAULT 3,
    retain          BOOLEAN NOT NULL DEFAULT FALSE,
    expires_at      TIMESTAMPTZ NOT NULL DEFAULT (now() + interval '24 hours'),
    guardrail_flags TEXT[] NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE session_turns (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id      UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    role            TEXT NOT NULL CHECK (role IN ('system', 'user', 'assistant')),
    turn_type       TEXT NOT NULL CHECK (turn_type IN (
                        'pre_q', 'dream', 'follow_up', 'conclusion', 'system'
                    )),
    payload         JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE retrieval_runs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id      UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    queries         JSONB NOT NULL DEFAULT '[]'::jsonb,
    curated_hits    JSONB NOT NULL DEFAULT '[]'::jsonb,
    user_hits       JSONB NOT NULL DEFAULT '[]'::jsonb,
    filters         JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE conclusions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id      UUID NOT NULL UNIQUE REFERENCES sessions(id) ON DELETE CASCADE,
    retrieval_run_id UUID REFERENCES retrieval_runs(id) ON DELETE SET NULL,
    classification  JSONB NOT NULL DEFAULT '{}'::jsonb,
    conclusion_md   TEXT NOT NULL DEFAULT '',
    claims          JSONB NOT NULL DEFAULT '[]'::jsonb,
    disagreements   JSONB NOT NULL DEFAULT '[]'::jsonb,
    adab            JSONB NOT NULL DEFAULT '{}'::jsonb,
    confidence      JSONB NOT NULL DEFAULT '{}'::jsonb,
    gaps            JSONB NOT NULL DEFAULT '[]'::jsonb,
    evidence        JSONB NOT NULL DEFAULT '[]'::jsonb,
    guardrail_flags TEXT[] NOT NULL DEFAULT '{}',
    abstained       BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX sessions_expires_idx ON sessions (expires_at)
    WHERE retain = FALSE;
CREATE INDEX sessions_owner_idx ON sessions (owner_user_id);
CREATE INDEX session_turns_session_idx ON session_turns (session_id, created_at);
CREATE INDEX retrieval_runs_session_idx ON retrieval_runs (session_id);
