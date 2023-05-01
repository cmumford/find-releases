# Copyright 2016 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import _pickle as cPickle
import sys

def main(args):
  if len(args) != 1:
    print('expecting one arg, the commit to look up', file=sys.stderr)
    return 1

  try:
    with open('cache.pickle', 'rb') as f:
      cache = cPickle.load(f)
  except:
    print('couldn\'t load cached data', file=sys.stderr)
    return 1

  commit = args[0]
  sha1_to_release = cache['sha1_to_release']
  commit_merged_as = cache['commit_merged_as']
  print('commit %s landed in %s' % (commit, sha1_to_release.get(commit, '???')))
  print('Merges:')
  merges = commit_merged_as.get(commit, [])
  if not merges:
    print('  None found.')
  else:
    for merge in merges:
      print('  %s (as %s)' % (sha1_to_release.get(merge, '???'), merge))


if __name__ == '__main__':
  sys.exit(main(sys.argv[1:]))
