CREATE TABLE IF NOT EXISTS resumes (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    text TEXT NOT NULL,
    embedding FLOAT8[] NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS jobs (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    company VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    url TEXT,
    embedding FLOAT8[] NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_resumes_created ON resumes(created_at);
CREATE INDEX IF NOT EXISTS idx_jobs_created ON jobs(created_at);
