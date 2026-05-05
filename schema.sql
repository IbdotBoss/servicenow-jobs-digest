-- jobs.db schema
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    location TEXT,
    date DATE NOT NULL,
    link TEXT UNIQUE NOT NULL,
    source TEXT NOT NULL,
    sponsorship_confirmed BOOLEAN DEFAULT 0,
    security_clearance BOOLEAN DEFAULT 0,
    tags TEXT,
    salary_min INTEGER,
    salary_max INTEGER,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for faster queries
CREATE INDEX IF NOT EXISTS idx_date ON jobs(date);
CREATE INDEX IF NOT EXISTS idx_source ON jobs(source);
CREATE INDEX IF NOT EXISTS idx_location ON jobs(location);
CREATE INDEX IF NOT EXISTS idx_company ON jobs(company);

-- Insert or ignore on conflict
INSERT OR IGNORE INTO jobs (title, company, location, date, link, source, sponsorship_confirmed, security_clearance, tags, salary_min, salary_max)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);