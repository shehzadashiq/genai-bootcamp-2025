CREATE TABLE IF NOT EXISTS words (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    urdu TEXT NOT NULL,
    urdlish TEXT NOT NULL,
    english TEXT NOT NULL,
    parts TEXT
);

CREATE TABLE IF NOT EXISTS study_activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    url TEXT,
    thumbnail_url TEXT,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    word_count INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS words_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word_id INTEGER NOT NULL,
    group_id INTEGER NOT NULL,
    FOREIGN KEY (word_id) REFERENCES words(id),
    FOREIGN KEY (group_id) REFERENCES groups(id)
);

CREATE TABLE IF NOT EXISTS study_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL,
    created_at DATETIME NOT NULL,
    study_activity_id INTEGER NOT NULL,
    FOREIGN KEY (group_id) REFERENCES groups(id),
    FOREIGN KEY (study_activity_id) REFERENCES study_activities(id)
);

CREATE TABLE IF NOT EXISTS word_review_items (
    word_id INTEGER NOT NULL,
    study_session_id INTEGER NOT NULL,
    correct BOOLEAN NOT NULL,
    created_at DATETIME NOT NULL,
    FOREIGN KEY (word_id) REFERENCES words(id),
    FOREIGN KEY (study_session_id) REFERENCES study_sessions(id),
    UNIQUE(study_session_id, word_id)
);

-- Seed data
INSERT OR REPLACE INTO groups (name) VALUES 
    ('Beginner Words'),
    ('Intermediate Words'),
    ('Advanced Words');

INSERT OR REPLACE INTO study_activities (id, name, url, thumbnail_url, description) VALUES 
    (1, 'Vocabulary Quiz', '/apps/vocabulary-quiz', '/images/thumbnails/vocabulary.svg', 'Test your vocabulary knowledge with interactive flashcards and quizzes.'),
    (2, 'Word Matching', '/apps/word-matching', '/images/thumbnails/matching.svg', 'Match Urdu words with their English translations in this fun memory game.'),
    (3, 'Sentence Builder', '/apps/sentence-builder', '/images/thumbnails/sentences.svg', 'Practice building sentences using the words you''ve learned.');
