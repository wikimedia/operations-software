Clinic Duty software
====

A collection of software to be used while on [SRE clinic duty](https://wikitech.wikimedia.org/wiki/SRE/Clinic_Duty).

## ops-maint-gcal

Add links to Google Calendar for [`ops-maintenance` Google Group](https://groups.google.com/u/0/a/wikimedia.org/g/ops-maintenance).

Script usage is as follows:

* Open https://groups.google.com/u/0/a/wikimedia.org/g/ops-maintenance/
* Copy/paste the code in the js console:

  Linux: `cat ops-maint-gcal.js | xclip`

  macOS: `cat ops-maint-gcal.js | pbcopy`

* Navigate to a thread with the maintenance announcement you are
  interested in
* Call `addLinks()`, either from the console or via a bookmarklet such
  as `javascript:addLinks()`
* If the maintenance can be parsed a Google Calendar link will be
  appended next to the message's sender

Code will remain loaded until the current tab is refreshed. Use the navigation
buttons within Google Groups to avoid having to load the code again.

## Contributing

To run the unit test, run the following in an isolated environment
of your choosing where you'd be comfortable running
`curl unknown.com | bash`, because that's what using npm is.

```
npm install && npm test
```

To run other scripts in package.json, use `npm run <script>`.
