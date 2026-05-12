-- Migration: add data column to notifications table
-- Adds a JSON field to store navigation context (apiaryId, hiveId, taskId)
-- that allows the mobile app to navigate to the related resource when
-- the user taps a notification.

ALTER TABLE notifications ADD COLUMN data JSONB;
