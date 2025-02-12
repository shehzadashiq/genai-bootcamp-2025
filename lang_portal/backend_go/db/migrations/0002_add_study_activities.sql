CREATE TABLE IF NOT EXISTS study_activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    thumbnail_url TEXT,
    description TEXT
);

-- Add some default study activities
INSERT INTO study_activities (name, description) VALUES 
    ('Vocabulary Quiz', 'Practice your vocabulary with flashcards'),
    ('Word Match', 'Match words with their meanings'),
    ('Sentence Builder', 'Create sentences using learned words'); 