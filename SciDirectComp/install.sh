#!/bin/bash
# install SciDirect command line utils (after untaring)

ln getSciDirect.py getSciDirect
ln JournalComp.py JournalComp
chmod a+x *.py getSciDirect JournalComp

echo JIM DO NOT FORGET to update config.cfg
