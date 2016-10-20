# Copyright 2016 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import cPickle
import os
import sys


ROOT = None


def PathForCommit(commit):
  return os.path.join(ROOT, commit[0:2], commit[2:] + '.html')


def main(args):
  global ROOT
  pickle = args[0]
  OUTPUT = args[1]

  for i in range(256):
    path = os.path.join(ROOT, '%02x' % i)
    if not os.path.exists(path):
      os.makedirs(path)

  try:
    with open(pickle, 'rb') as f:
      cache = cPickle.load(f)
  except:
    print >>sys.stderr, 'couldn\'t load cached data'
    return 1

  sha1_to_release = cache['sha1_to_release']
  commit_merged_as = cache['commit_merged_as']
  count = 0
  for commit in sha1_to_release:
    output_path = PathForCommit(commit)
    with open(output_path, 'wb') as f:
      print >>f, '<!DOCTYPE html><body><pre>'
      print >>f, 'commit <a href="https://crrev.com/%s">%s</a> landed in %s' % (
          commit, commit, sha1_to_release.get(commit, '???'))
      print >>f, 'Merges:'
      merges = commit_merged_as.get(commit, [])
      if not merges:
        print >>f, '  None found.'
      else:
        for merge in merges:
          print >>f, '  %s (as <a href="https://crrev.com/%s">%s</a>)' % (
              sha1_to_release.get(merge, '???'), merge, merge)
      print >>f, '</pre></body>'
    count += 1
    if count == 100:
      break

  return 0


if __name__ == '__main__':
  sys.exit(main(sys.argv[1:]))
