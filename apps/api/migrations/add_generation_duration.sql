-- Migration: Add generation_duration_seconds column to topics table
-- Run this SQL against your PostgreSQL database

ALTER TABLE topics
ADD COLUMN IF NOT EXISTS generation_duration_seconds FLOAT;

-- Verify the column was added
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'topics' AND column_name = 'generation_duration_seconds';
