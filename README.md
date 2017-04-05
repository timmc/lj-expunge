# lj-expunge

This program **destroys** your LiveJournal posts. All of them.

If you want to export and save the contents of your LJ, find a
different program!

The theory is that deleting may not be enough (LJ may just set a
"deleted" flag on the post and not show it) and wiping may not be
enough (LJ may keep previous copies, but deletion might take effect
after N days.) And frankly, none of it may matter, since they could
keep all copies forever. But it's worth a try.

## Warning

This is based on https://github.com/ghewgill/ljdump so I could nab the
auth and iteration code. I *do not vouch* for this code since I have
not read the existing code in any detail, but honestly the worst this
thing could do (probably?) is to delete your entries without wiping
them first.

## Usage

The simplest way to run this is to execute the lj-expunge.py script with Python:

`python lj-expunge.py`

Depending on your OS, you may be able to double-click the lj-expunge.py script
directly, or you may need to open a Terminal/Command Prompt window to run it.
Either way, it will prompt you for your Livejournal username and password,
then **overwrite** all your journal entries.

You may optionally destroy entries from a different journal (a community)
where you are a member.

### Config file

You can also define a configuration file and pass it to lj-expunge.py
as an argument:

`python lj-expunge.py ./path/to/lj-expunge.config`

A sample configuration is provided in "lj-expunge.config.sample",
which should be copied and then edited.  The configuration settings
are:

  server - The XMLRPC server URL. This should only need to be changed
           if you are destroying a journal that is livejournal-compatible
           but is not livejournal itself.

  username - The livejournal user name.

  password - The account password. This password is never sent in the
             clear; the livejournal "challenge" password mechanism is used.

  journal - Optional: The journal to destroy entries in. If this is
            not specified, the "username" journal is destroyed.

### Restarting

The script creates file `$YOUR_LJ_NAME/.last` to record your last
position if you need to interrupt and restart the script.

If you need to restart from the beginning of the journal (e.g. if
you're hacking on the script) delete that directory or file and run
again.

### Rate-limiting

Restarting this script *from the beginning* 3 times within the same
hour may result in being blocked from editing certain entries for an
hour:

http://lj-dev.livejournal.com/757527.html?thread=8555799#t8555799

> LJ's code is under "broken client loop prevention"
> [here](http://code.sixapart.com/trac/livejournal/browser/trunk/cgi-bin/ljprotocol.pl). As
> evan said, it looks like it's preventing 3 accesses with the same
> synctime parameter within an hour from a particular user. If you
> repeatedly run your script, you'll be asking for the empty synctime
> repeatedly, because the script always starts off with that. So if
> you run the script more than 3 times in an hour, it'll stop working
> and start giving the "client is broken" error.

## TODOs

- Instead of wiping with constant string, wipe with variable length
  chunk of gibberish (maybe matched to original post length)
- After wiping, retrieve entry to confirm, then delete it
- Wipe and delete author's own comments
- Delete comments by others
- Wipe and delete userpics

## Changelog

### v1 - 2017-04-05

Replaces all journal entries and most of their metadata with "wiped".
