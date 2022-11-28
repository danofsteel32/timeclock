-- name: create_schema#
/* Schema for the timeclock database. */
CREATE TABLE user (
    id INTEGER PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    password_hash BLOB NOT NULL,
    role TEXT NOT NULL DEFAULT 'EMPLOYEE',
    username TEXT NOT NULL UNIQUE,
    CHECK (
        role IN (
            'ADMIN',
            'OWNER',
            'EMPLOYEE'
        )
    )
);

CREATE TABLE workday (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    clock_in TIMESTAMP NOT NULL,
    clock_out TIMESTAMP,
    notes TEXT,
    UNIQUE (user_id, clock_in),
    FOREIGN KEY (user_id) REFERENCES user(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

CREATE TABLE photo (
    id INTEGER PRIMARY KEY,
    filename TEXT NOT NULL UNIQUE
);

CREATE TABLE workday_photo (
    photo_id INTEGER,
    workday_id INTEGER,
    PRIMARY KEY (photo_id, workday_id),
    FOREIGN KEY (photo_id) REFERENCES photo(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
    FOREIGN KEY (workday_id) REFERENCES workday(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

CREATE TABLE timesheet (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    notes TEXT,
    FOREIGN KEY (user_id) REFERENCES user(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

CREATE TABLE timesheet_workday (
    timesheet_id INTEGER,
    workday_id INTEGER,
    PRIMARY KEY (timesheet_id, workday_id),
    FOREIGN KEY (timesheet_id) REFERENCES timesheet(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
    FOREIGN KEY (workday_id) REFERENCES workday(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);