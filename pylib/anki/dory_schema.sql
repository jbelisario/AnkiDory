-- Schema for Dory's hint system

-- Table to store card hints
CREATE TABLE IF NOT EXISTS dory_hints (
    id INTEGER PRIMARY KEY,
    cid INTEGER NOT NULL,  -- card id
    hint TEXT NOT NULL,    -- the hint content
    created INTEGER NOT NULL,  -- timestamp when hint was generated
    FOREIGN KEY(cid) REFERENCES cards(id)
);

-- Table to track hint usage statistics
CREATE TABLE IF NOT EXISTS dory_hint_stats (
    id INTEGER PRIMARY KEY,
    cid INTEGER NOT NULL,  -- card id
    hints_used INTEGER NOT NULL DEFAULT 0,  -- total number of hints used
    last_hint_date INTEGER,  -- timestamp of last hint request
    FOREIGN KEY(cid) REFERENCES cards(id)
);
