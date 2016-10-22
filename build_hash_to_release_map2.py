# Copyright 2016 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import cPickle
import os
import re
import subprocess
import sys


def Git(*args):
  args = ('git',) + args
  return subprocess.check_output(args, shell=False)


def main(args):
  if len(Git('branch').splitlines()) != 1:
    print 'WARNING: should not have any local branches in this repo copy.'
    print 'WARNING: Commits will be assigned to branches, rather than tags.'
    print 'WARNING: Continuing anyway...'

  root = args[0]
  if not os.path.exists(root):
    os.makedirs(root)
  print 'loading data...'
  try:
    with open(os.path.join(root, 'cache.pickle'), 'rb') as f:
      cache = cPickle.load(f)
  except:
    cache = {}
  cache.setdefault('sha1_to_release', {})
  cache.setdefault('commit_merged_as', {})

  sha1_to_release = cache['sha1_to_release']
  print 'retrieving list of commits...'
  revs = set(Git('rev-list', '--all', '--after=\'36 months ago\'').splitlines())
  have_rev_data = set(sha1_to_release.keys())
  revs_to_get = revs - have_rev_data
  # If this crashes, `ulimit -s unlimited`.
  print 'getting revs for %d commits...' % len(revs_to_get)
  p = subprocess.Popen(['xargs', 'git', 'name-rev'], shell=False,
                       stdin=subprocess.PIPE, stdout=subprocess.PIPE)
  named_revs = p.communicate('\n'.join(revs_to_get))[0]
  print 'munging output...'
  trailing_tilde_re = re.compile(r'~.*$')
  for line in named_revs.splitlines():
    commit, _, name = line.partition(' ')
    # We want the tags, keep the ignore/foos too as we don't want them, but
    # we don't want to keep looking them up, either.
    if name.startswith('tags/'):
      sha1_to_release[commit] = trailing_tilde_re.sub('', name[5:])
    if name.startswith('remotes/origin/ignore/foo'):
      sha1_to_release[commit] = trailing_tilde_re.sub('', name)
  cache['sha1_to_release'] = sha1_to_release

  # TODO: Invalidate if tags updated.

  # Walk commit messages with the "cherry picked" annotation to try to gather
  # useful information on merges.
  print 'getting merge information...'
  current_commit = None
  commit_prefix = '!!!COMMIT!!!'
  commit_merged_as = {}
  for line in Git('log', '-F', '--all', '--no-abbrev', '--grep',
                  'cherry picked from commit',
                  '--pretty=' + commit_prefix + '%H%n%b').splitlines():
    if line.startswith(commit_prefix):
      current_commit = line[len(commit_prefix):]
      continue
    mo = re.match('\(cherry picked from commit ([0-9a-f]{40})\)', line)
    if mo:
      commit_merged_as.setdefault(mo.group(1), []).append(current_commit)
  cache['commit_merged_as'] = commit_merged_as

  print 'writing data...'
  try:
    with open(os.path.join(root, 'cache.pickle'), 'wb') as f:
      cPickle.dump(cache, f)
  except Exception as e:
    print >>sys.stderr, 'Failed to save cache', e

  return 0


if __name__ == '__main__':
  sys.exit(main(sys.argv[1:]))
