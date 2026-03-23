BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> a0faccbf343e

CREATE TABLE papers (
    id SERIAL NOT NULL, 
    external_id VARCHAR(100), 
    title VARCHAR(500) NOT NULL, 
    authors JSONB, 
    abstract_original TEXT, 
    published_date DATE, 
    pdf_url VARCHAR(500), 
    is_parsed BOOLEAN NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_papers_external_id ON papers (external_id);

CREATE TABLE users (
    id SERIAL NOT NULL, 
    username VARCHAR(50) NOT NULL, 
    email VARCHAR(100) NOT NULL, 
    hashed_password VARCHAR(255) NOT NULL, 
    is_active BOOLEAN NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    UNIQUE (email), 
    UNIQUE (username)
);

CREATE TABLE paper_summaries (
    id SERIAL NOT NULL, 
    paper_id INTEGER NOT NULL, 
    core_innovation TEXT, 
    methodology TEXT, 
    limitations TEXT, 
    relevance_score FLOAT, 
    llm_model VARCHAR(50), 
    updated_at TIMESTAMP WITH TIME ZONE, 
    PRIMARY KEY (id), 
    FOREIGN KEY(paper_id) REFERENCES papers (id) ON DELETE CASCADE, 
    UNIQUE (paper_id)
);

CREATE TABLE subscriptions (
    id SERIAL NOT NULL, 
    user_id INTEGER NOT NULL, 
    source_platform VARCHAR(50), 
    search_query VARCHAR(255), 
    cron_schedule VARCHAR(50), 
    is_active BOOLEAN NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE TABLE user_paper_interactions (
    id SERIAL NOT NULL, 
    user_id INTEGER NOT NULL, 
    paper_id INTEGER NOT NULL, 
    subscription_id INTEGER, 
    status VARCHAR(20) NOT NULL, 
    added_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(paper_id) REFERENCES papers (id) ON DELETE CASCADE, 
    FOREIGN KEY(subscription_id) REFERENCES subscriptions (id) ON DELETE SET NULL, 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
    CONSTRAINT uq_user_paper_interaction UNIQUE (user_id, paper_id)
);

INSERT INTO alembic_version (version_num) VALUES ('a0faccbf343e') RETURNING alembic_version.version_num;

COMMIT;

