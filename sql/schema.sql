PRAGMA foreign_keys = ON;
CREATE TABLE locations (location_id TEXT PRIMARY KEY, region TEXT NOT NULL);
CREATE TABLE expected_days (
    location_id TEXT NOT NULL REFERENCES locations(location_id),
    business_date TEXT NOT NULL,
    PRIMARY KEY(location_id, business_date)
);
CREATE TABLE daily_operations (
    location_id TEXT NOT NULL,
    business_date TEXT NOT NULL,
    orders INTEGER NOT NULL CHECK(orders >= 0),
    gross_cents INTEGER NOT NULL CHECK(gross_cents >= 0),
    refund_cents INTEGER NOT NULL CHECK(refund_cents BETWEEN 0 AND gross_cents),
    labor_minutes INTEGER NOT NULL CHECK(labor_minutes >= 0),
    completed_jobs INTEGER NOT NULL CHECK(completed_jobs BETWEEN 0 AND orders),
    on_time_jobs INTEGER NOT NULL CHECK(on_time_jobs BETWEEN 0 AND completed_jobs),
    PRIMARY KEY(location_id, business_date),
    FOREIGN KEY(location_id, business_date) REFERENCES expected_days(location_id, business_date)
);
