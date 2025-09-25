-- Create task results table for e2e testing
CREATE TABLE IF NOT EXISTS e2e_test_results (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    task_id VARCHAR(255) NOT NULL,
    result JSONB,
    status VARCHAR(50),
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index on task_id for faster lookups
CREATE INDEX IF NOT EXISTS idx_e2e_test_results_task_id ON e2e_test_results(task_id);

-- Create index on timestamp for time-based queries
CREATE INDEX IF NOT EXISTS idx_e2e_test_results_timestamp ON e2e_test_results(timestamp);

-- Create task status table
CREATE TABLE IF NOT EXISTS task_status (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    task_id VARCHAR(255) UNIQUE NOT NULL,
    task_type VARCHAR(100),
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    priority VARCHAR(20) DEFAULT 'normal',
    payload JSONB,
    result JSONB,
    error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    retry_count INTEGER DEFAULT 0,
    attempts INTEGER DEFAULT 0,
    worker_id VARCHAR(255),
    queue_name VARCHAR(100)
);

-- Create indices for task status
CREATE INDEX IF NOT EXISTS idx_task_status_status ON task_status(status);
CREATE INDEX IF NOT EXISTS idx_task_status_created_at ON task_status(created_at);
CREATE INDEX IF NOT EXISTS idx_task_status_priority ON task_status(priority);
CREATE INDEX IF NOT EXISTS idx_task_status_task_type ON task_status(task_type);

-- Create celery task results table
CREATE TABLE IF NOT EXISTS celery_task_results (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    task_id VARCHAR(255) UNIQUE NOT NULL,
    celery_task_id VARCHAR(255),
    task_name VARCHAR(255),
    status VARCHAR(50),
    result JSONB,
    traceback TEXT,
    date_done TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index on celery_task_id
CREATE INDEX IF NOT EXISTS idx_celery_task_results_celery_id ON celery_task_results(celery_task_id);
CREATE INDEX IF NOT EXISTS idx_celery_task_results_task_name ON celery_task_results(task_name);

-- Create audit log table for tracking all task operations
CREATE TABLE IF NOT EXISTS task_audit_log (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    task_id VARCHAR(255) NOT NULL,
    operation VARCHAR(50) NOT NULL,
    old_status VARCHAR(50),
    new_status VARCHAR(50),
    details JSONB,
    performed_by VARCHAR(255),
    performed_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index on task_id for audit trail
CREATE INDEX IF NOT EXISTS idx_task_audit_log_task_id ON task_audit_log(task_id);
CREATE INDEX IF NOT EXISTS idx_task_audit_log_performed_at ON task_audit_log(performed_at);

-- Create function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at columns
CREATE TRIGGER update_e2e_test_results_updated_at BEFORE UPDATE ON e2e_test_results
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_task_status_updated_at BEFORE UPDATE ON task_status
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_celery_task_results_updated_at BEFORE UPDATE ON celery_task_results
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create function to log task status changes
CREATE OR REPLACE FUNCTION log_task_status_change()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.status IS DISTINCT FROM NEW.status THEN
        INSERT INTO task_audit_log (task_id, operation, old_status, new_status, details)
        VALUES (NEW.task_id, 'STATUS_CHANGE', OLD.status, NEW.status,
                jsonb_build_object(
                    'old_record', to_jsonb(OLD),
                    'new_record', to_jsonb(NEW)
                ));
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for task status audit logging
CREATE TRIGGER log_task_status_changes AFTER UPDATE ON task_status
    FOR EACH ROW EXECUTE FUNCTION log_task_status_change();

-- Insert test data for validation
INSERT INTO e2e_test_results (task_id, result, status, metadata)
VALUES
    ('test-001', '{"test": true, "message": "Initial test data"}'::jsonb, 'completed', '{"source": "migration"}'::jsonb)
ON CONFLICT DO NOTHING;

-- Create view for task summary
CREATE OR REPLACE VIEW task_summary AS
SELECT
    ts.task_id,
    ts.task_type,
    ts.status,
    ts.priority,
    ts.created_at,
    ts.completed_at,
    ts.attempts,
    ctr.celery_task_id,
    ctr.task_name as celery_task_name,
    COUNT(tal.id) as audit_entries
FROM task_status ts
LEFT JOIN celery_task_results ctr ON ts.task_id = ctr.task_id
LEFT JOIN task_audit_log tal ON ts.task_id = tal.task_id
GROUP BY
    ts.task_id, ts.task_type, ts.status, ts.priority,
    ts.created_at, ts.completed_at, ts.attempts,
    ctr.celery_task_id, ctr.task_name;

-- Grant appropriate permissions (adjust based on your Supabase setup)
-- These are examples and might need to be adjusted based on your roles
GRANT ALL ON e2e_test_results TO anon;
GRANT ALL ON task_status TO anon;
GRANT ALL ON celery_task_results TO anon;
GRANT ALL ON task_audit_log TO anon;
GRANT SELECT ON task_summary TO anon;

GRANT ALL ON e2e_test_results TO authenticated;
GRANT ALL ON task_status TO authenticated;
GRANT ALL ON celery_task_results TO authenticated;
GRANT ALL ON task_audit_log TO authenticated;
GRANT SELECT ON task_summary TO authenticated;
