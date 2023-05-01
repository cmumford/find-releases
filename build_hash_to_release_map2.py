# Copyright 2016 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import _pickle as cPickle
import os
import re
import subprocess
import sys
import uuid


def Git(*args):
  args = ('git',) + args
  return subprocess.check_output(args, shell=False).decode(sys.stdout.encoding)


def main(args):
  if len(Git('branch').splitlines()) != 1:
    print('WARNING: Should not have any local branches in this repo copy.')
    print('WARNING: Commits will be assigned to branches, rather than release ')
    print('WARNING: tags.')
    print('WARNING: Continuing anyway...\n')
  if 'remotes/branch-heads/' in Git('branch', '-a'):
    print('WARNING: Should not have branch-heads (--with_branch_heads) in this')
    print('WARNING: repo copy. Commits will be assigned to branch versions')
    print('WARNING: rather than release tags.')
    print('WARNING: Continuing anyway...\n')

  root = args[0]
  if not os.path.exists(root):
    os.makedirs(root)
  print('loading data...')
  try:
    with open(os.path.join(root, 'cache.pickle'), 'rb') as f:
      cache = cPickle.load(f)
  except:
    cache = {}
  cache.setdefault('sha1_to_release', {})
  cache.setdefault('commit_merged_as', {})
  cache.setdefault('blacklist', {})

  sha1_to_release = cache['sha1_to_release']
  blacklist = cache['blacklist']
  print('retrieving list of commits...')
  revs = set(Git('rev-list', '--all', '--after=\'48 months ago\'').splitlines())
  have_rev_data = set(sha1_to_release.keys())
  blacklist_revs = set(blacklist.keys())
  revs_to_get = revs - have_rev_data - blacklist_revs
  # If this crashes, `ulimit -s unlimited`.
  print('getting revs for %d commits...' % len(revs_to_get))
  p = subprocess.Popen(['xargs', 'git', 'name-rev'], shell=False,
                       stdin=subprocess.PIPE, stdout=subprocess.PIPE)
  ascii_revs = '\n'.join(revs_to_get).encode(sys.stdout.encoding)
  named_revs = p.communicate(ascii_revs)[0].decode(sys.stdout.encoding)
  print('munging output...')
  trailing_tilde_re = re.compile(r'~.*$')
  branch_heads_re = re.compile(r'remotes\/branch-heads\/(\d+)~.*$')
  for line in named_revs.splitlines():
    commit, _, name = line.partition(' ')
    # We want the tags, keep the ignore/foos too as we don't want them, but
    # we don't want to keep looking them up, either.
    if name.startswith('tags/'):
      sha1_to_release[commit] = trailing_tilde_re.sub('', name[5:])
    elif (name.startswith('remotes/origin/ignore/') or
          name.startswith('remotes/branch-heads/git-svn~') or
          name.startswith('remotes/origin/infra/config')):
      blacklist[commit] = trailing_tilde_re.sub('', name)
    else:
      print('not saving', commit, name)

  cache['sha1_to_release'] = sha1_to_release
  cache['blacklist'] = blacklist

  # TODO: Invalidate if tags updated.

  # Walk commit messages with the "cherry picked" annotation to try to gather
  # useful information on merges.
  print('getting merge information...')
  current_commit = None
  commit_prefix = str(uuid.uuid1())
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

  print('writing data...')
  try:
    with open(os.path.join(root, 'cache.pickle'), 'wb') as f:
      cPickle.dump(cache, f)
  except Exception as e:
    print('Failed to save cache', e, file=sys.stderr)

  return 0


if __name__ == '__main__':
  sys.exit(main(sys.argv[1:]))
