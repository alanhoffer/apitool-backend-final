-- Indices de performance para dashboard, tareas, notificaciones y jobs.

CREATE INDEX IF NOT EXISTS idx_notifications_user_read_created
ON notifications ("userId", "isRead", "createdAt");

CREATE INDEX IF NOT EXISTS idx_notifications_user_type_title_read
ON notifications ("userId", type, title, "isRead");

CREATE INDEX IF NOT EXISTS idx_tasks_user_completed_due
ON tasks (user_id, completed, due_date);

CREATE INDEX IF NOT EXISTS idx_tasks_user_apiary
ON tasks (user_id, apiary_id);

CREATE INDEX IF NOT EXISTS idx_apiary_user_updated_at
ON apiary ("userId", "updatedAt");

CREATE INDEX IF NOT EXISTS idx_apiary_user_management_type
ON apiary ("userId", "managementType");

CREATE INDEX IF NOT EXISTS idx_devices_last_active_token
ON devices ("lastActive", "expoPushToken");
