# timeclock

Simple timeclock webapp

### Features
- Timesheets
- Basic RBAC (owner and employee) means employee's can't sign off on their own timesheets.
- Save notes during your workday
- Upload photos taken during your workday

### TODO
- More tests
- cli for user management
- deploy script
- search notes
- more user roles
- User signup page? (And user management)

### command line tool
Right now just assume that if you have physical access to the database you're and ADMIN.

```console
# prompt for password
$ timeclock-cli adduser --email --username --role

# prompt for confirmation
$ timeclock-cli deluser {id,email,username}

```
