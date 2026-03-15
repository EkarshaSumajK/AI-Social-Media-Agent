-- Add image_url column to social_posts table for AI-generated infographics
-- Migration: 002_add_social_post_image_url
-- Date: 2026-03-16

ALTER TABLE social_posts ADD COLUMN IF NOT EXISTS image_url TEXT;

COMMENT ON COLUMN social_posts.image_url IS 'URL of AI-generated infographic image for this social post';
