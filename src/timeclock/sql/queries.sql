-- name: insert_photo$
/* Add a new photo and return the new photo id.

Args:
    filename (str): The filename of the new photo.

Returns:
    int: The newly created photo's id.
*/
INSERT INTO photo (filename) VALUES (:filename) RETURNING id;

-- name: delete_photo!
/* Delete the photo with the given photo id.

Args:
    photo_id (int): The primary key id of the photo.

Returns:
    None
*/
DELETE FROM photo WHERE id = :photo_id;

-- name: get_workday_photos
/* Get all photos for the given workday id.

Args:
    workday_id (int): The primary key id of the workday.

Returns:
    Iterable of (photo.id, photo.filename) tuples.
*/
SELECT p.id, p.filename
  FROM photo p
  JOIN workday_photo wp
    ON p.id = wp.photo_id
WHERE wp.workday_id = :workday_id;

-- name: insert_workday_photo!
/* Add a new row to the workday_photo table.

Args:
    photo_id (int): The primary key id of the photo.
    workday_id (int): The primary key id of the workday.

Returns:
    None
*/
INSERT INTO workday_photo (photo_id, workday_id)
VALUES (:photo_id, :workday_id);

-- name: get_user_current_workday^
/* Get the latest workday for the given user id.

Args:
    user_id (int): The primary key id of the user.

Returns:
    Tuple[int, pendulum.DateTime, pendulum.DateTime, str]: (id, clock_in, clock_out, notes)
*/
SELECT id, clock_in, clock_out, notes
  FROM workday
 WHERE user_id = :user_id
 ORDER BY clock_in DESC LIMIT 1;

-- name: get_workday^
/* Get the workday with the given workday id.

Args:
    workday_id (int): The primary key id of the workday.

Returns:
    Tuple[pendulum.DateTime, pendulum.DateTime, str]
*/
SELECT clock_in, clock_out, notes FROM workday WHERE id = :workday_id

-- name: get_workday_user_id$
/* Get the user_id associated with the given workday id.

Args:
    workday_id (int): The primary key id of the workday.

Returns:
    int
*/
SELECT user_id FROM workday WHERE id = :workday_id;

-- name: get_workday_archived$
/* Get whether the workday id has been written to the timesheet_workday table.

Args:
    workday_id (int)

Returns:
    bool
*/
SELECT EXISTS (SELECT 1 FROM timesheet_workday WHERE workday_id = :workday_id);

-- name: update_workday!
/* Update the workday row for the given workday id.

Args:
    workday_id (int): The primary key id of the workday.
    clock_in (pendulum.DateTime): Clock in timestamp.
    clock_out (pendulum.DateTime): Clock out timestamp.
    notes (str): Any notes.

Returns:
    None
*/
UPDATE workday SET
    clock_in = :clock_in,
    clock_out = :clock_out,
    notes = :notes
WHERE id = :workday_id;
