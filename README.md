# timeclock

Simple webpage for clock in/out and viewing timesheet.

- http basic auth (password in header)
- add notes to a day
- add pictures to a day


### TODO
- database behavior on server start
- photo uploads (where to put them? how to fetch them?)

### Routes
everything is served under the `/timeclock` blueprint.

- `/timeclock`
    - Show the current day's happenings

- `/timeclock/workday/<id: int>`
    - GET

- `/timeclock/workday/<id: int>/photo`
    - PUT upload a new photo
    - DELETE `?photo_id=<id>` delete the photo 

- `/timeclock/workday/<id: int>/notes`
    - POST
    - update the notes

- `/timeclock/clock_in`
    - PUT
    - `current_user`

- `/timeclock/clock_out`
    - POST
    - `current_user`

- `/timeclock/timesheet?user_id=<>`
    - GET
    - Show the current timesheet for user and links to past timesheets

- `/timeclock/timesheet/<id: int>`
    - GET
    - What links to past timesheets link to

- `/timeclock/overview`
    - GET
    - OWNER only

- `/timeclock/auth/login`
    - GET show the login page
    - POST login with creds and redirect to /timeclock

- `/timeclock/auth/logout`
    - GET logout and redirect to login page
