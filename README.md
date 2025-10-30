# Stream Bot (unnamed)
An event driven bot creation framework for use alongside livestreaming and content creation on Twitch, YouTube, and potentially other platforms in the future. 
Intended to be used as a backend library for a user to create any type of livestreaming adjacent tool, it can also be used as a stand alone content creation bot, and has interfaces for connecting to a wide variaty of livestreaming tools that are currently in use. 

A standard frontend UI is planned for the future.

Usage:
------ 
`python -m streambot <user>`

---

streambot/ - the source code that make the bot work including libraries for a user to build upon.

build/ - contains the current build of the bot or something.

usr/ - in here a user is expected to put a folder containing their implementations for the bot including setting and the like.
usr/secret - for all the secret keys and stuff for the bot to authorize and the like.

TODO:
- add an example user settings in `usr/example/` and include that in the project

