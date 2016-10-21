# Copyright 2016 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import cPickle
import json
import os
import shutil
import sys


SELF_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = None


def main(args):
  global ROOT
  pickle = args[0]
  ROOT = args[1]

  print 'loading...'
  try:
    with open(pickle, 'rb') as f:
      cache = cPickle.load(f)
  except:
    print >>sys.stderr, 'couldn\'t load cached data'
    return 1

  sha1_to_release = cache['sha1_to_release']
  commit_merged_as = cache['commit_merged_as']
  data_updated = cache['data_updated']

  print 'paritioning...'
  partitioned = {}
  for commit in sorted(sha1_to_release):
    if not commit:
      continue
    bucket = commit[0:3]
    partitioned.setdefault(bucket, [])
    partitioned[bucket].append(commit)

  TEMPLATE = '''<!DOCTYPE html><html><head>''' \
             '''<style>''' \
             '''body{font-family:'Helvetica','Arial',sans-serif;}''' \
             '''footer{font-size:smaller;}''' \
             '''a,code{font-family:'Monaco','Consolas',monospace;}''' \
             '''</style>''' \
             '''<script src="handler.js"></script>''' \
             '''<script>%s</script>''' \
             '''<body onload="go()">''' \
             '''<div id="content"></div>''' \
             '''<footer>Data updated at %s.</footer>''' \
             '''</body></html>'''

  if not os.path.exists(ROOT):
    os.makedirs(ROOT)

  print 'generating data files...'
  for bucket, commits in partitioned.iteritems():
    data_obj = {}
    for commit in commits:
      data_obj[commit] = [sha1_to_release[commit], []]
      for merge in commit_merged_as.get(commit, []):
        data_obj[commit][1].append([sha1_to_release.get(merge, '???'),
                                    merge])

    output_path = os.path.join(ROOT, bucket + '.html')
    with open(output_path, 'wb') as f:
      print >>f, TEMPLATE % ('data=' + json.dumps(data_obj), data_updated)

  shutil.copy(os.path.join(SELF_DIR, 'handler.js'),
              os.path.join(ROOT, 'handler.js'))

  return 0


if __name__ == '__main__':
  sys.exit(main(sys.argv[1:]))
