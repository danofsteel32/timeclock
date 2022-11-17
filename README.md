# timeclock

Simple webpage for clock in/out and viewing timesheet.

- http basic auth (password in header)
- add notes to a day
- add pictures to a day

### TODO
- database behavior on server start
- create app config object
- get DB FILE from config instead of env?

### Routes
everything is served under the `/timeclock` blueprint.

- `/timeclock` 
    - GET
    - Show either clock in or out button
    - Show current weeks hours
- `/timeclock/clock_in`
    - PUT
- `/timeclock/clock_out`
    - PUT
- `/timeclock/timesheet`
    - GET
- `/timeclock/auth/login`
    - GET, POST
- `/timeclock/auth/logout`
    - POST
