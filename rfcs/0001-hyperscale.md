- Feature Name: Minion cache aware localclient
- Start Date: 2018-08-20 
- RFC PR:
- Salt Issue:

# Summary
[summary]: #summary

This proposal would allow the LocalClient to perform an additional step before deciding that a minion did not return.

Prior to making an evaluation that a minion did not return, the master would issue issue a publication asking all minions
which it believes to have failed if they have run the original job and, if so, it would collect and include those returns.

# Motivation
[motivation]: #motivation

Salt has has a long-standing architectural limitation in that returns which flow from the minions to the master do
so in a many-to-one fashion, which at a certain scale, overwhealms the master and some returns are dropped. This
would allow the master to ask directly about returns which _may_ be missing and if they are found, they are included
in the CLI output whereas they were not before.

# Design
[design]: #detailed-design

A few things need to be done in order to make this happen. They are as follows:

1) The `saltutil.find_job` execution module function should be extended to include the ability to query a local minion minion cache.

The primary barrier here is that minion caches are _off by default_ in shipping versions of Salt. This means
that we'll need to document that as part of scaling up and using the CLI, it would be our best practice to enable
minion caches.

2) The LocalClient would need to be modified to search the minion cache using the flag created in `saltutil.find_job`. This should happen
in the event that a plain `find_job` either did not return or returned saying that the job is not running and prior to the LocalClient
delcaring that a minion did not respond.

## Alternatives
[alternatives]: #alternatives

We could also have minions use external caches and we could have the master query those directly.

## Unresolved questions
[unresolved]: #unresolved-questions

There is the potential for some race conditions here which need to be fully explored.

Do we need to limit the size of minion caches? Do we want to turn minion caches on by default when we roll this out?

Do we have automatic minion cache pruning? We'd need to add that as well.

# Drawbacks
[drawbacks]: #drawbacks

The potential for race conditions as mentioned above are one concern. Another might be that enabling minion
caches, which will take up space. (See question about pruning above.)

Another drawback is that doing this would add both overhead to the CLI and it might also cause the CLI
to take longer to exit.
