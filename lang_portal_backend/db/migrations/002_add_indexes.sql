-- Add indexes for Word table
CREATE INDEX IF NOT EXISTS idx_word_urdu ON words(urdu);
CREATE INDEX IF NOT EXISTS idx_word_urdlish ON words(urdlish);
CREATE INDEX IF NOT EXISTS idx_word_english ON words(english);
CREATE INDEX IF NOT EXISTS idx_word_urdu_english ON words(urdu, english);
CREATE INDEX IF NOT EXISTS idx_word_urdlish_english ON words(urdlish, english);

-- Add indexes for Group table
CREATE UNIQUE INDEX IF NOT EXISTS idx_group_name ON groups(name);

-- Add indexes for WordGroup table
CREATE UNIQUE INDEX IF NOT EXISTS idx_wordgroup_word_group ON words_groups(word_id, group_id);

-- Add indexes for StudyActivity table
CREATE INDEX IF NOT EXISTS idx_studyactivity_created_group ON study_activities(created_at, group_id);

-- Add indexes for StudySession table
CREATE INDEX IF NOT EXISTS idx_studysession_created_group ON study_sessions(created_at, group_id);
CREATE INDEX IF NOT EXISTS idx_studysession_activity_created ON study_sessions(study_activity_id, created_at);

-- Add indexes for WordReviewItem table
CREATE INDEX IF NOT EXISTS idx_wordreview_word_correct ON word_review_items(word_id, correct);
CREATE INDEX IF NOT EXISTS idx_wordreview_session_created ON word_review_items(study_session_id, created_at); 