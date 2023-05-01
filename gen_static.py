# Copyright 2016 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import _pickle as cPickle
import collections
import json
import os
import shutil
import sys


SELF_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = None

def WriteIfChanged(output_path, contents):
  old_contents = ''
  if os.path.exists(output_path):
    with open(output_path, 'rb') as f:
      old_contents = f.read()
  if old_contents != contents:
    with open(output_path, 'wb') as f:
      f.write(contents.encode(sys.stdout.encoding))
    return True
  return False


def main(args):
  global ROOT
  pickle = args[0]
  ROOT = args[1]

  print('loading...')
  try:
    with open(pickle, 'rb') as f:
      cache = cPickle.load(f)
  except:
    print('couldn\'t load cached data', file=sys.stderr)
    return 1

  sha1_to_release = cache['sha1_to_release']
  commit_merged_as = cache['commit_merged_as']

  print('partitioning...')
  partitioned = {}
  for commit in sorted(sha1_to_release):
    bucket = commit[0:3]
    partitioned.setdefault(bucket, [])
    partitioned[bucket].append(commit)

  TEMPLATE = '''<!DOCTYPE html><html><head>''' \
             '''<style>''' \
             '''body{font-family:'Helvetica','Arial',sans-serif;}''' \
             '''a,code{font-family:'Monaco','Consolas',monospace;}''' \
             '''</style>''' \
             '''<script src="handler.js"></script>''' \
             '''<script>%s</script>''' \
             '''<body onload="go()">''' \
             '''<div id="content"></div>''' \
             '''</body></html>'''

  if not os.path.exists(ROOT):
    os.makedirs(ROOT)

  print('generating data files...')
  count = 0
  for bucket, commits in partitioned.items():
    data_obj = collections.OrderedDict()
    for commit in sorted(commits):
      data_obj[commit] = [sha1_to_release[commit], []]
      for merge in sorted(commit_merged_as.get(commit, [])):
        data_obj[commit][1].append([sha1_to_release.get(merge, '???'),
                                    merge])

    output_path = os.path.join(ROOT, bucket + '.html')
    to_write = TEMPLATE % ('data=' + json.dumps(data_obj, sort_keys=True,
                                                separators=(',',':')))
    if WriteIfChanged(output_path, to_write):
      count += 1
  print('updated %d files.' % count)

  shutil.copy2(os.path.join(SELF_DIR, 'handler.js'),
               os.path.join(ROOT, 'handler.js'))
  shutil.copy2(os.path.join(SELF_DIR, 'index.html'),
               os.path.join(ROOT, 'index.html'))
  return 0


if __name__ == '__main__':
  sys.exit(main(sys.argv[1:]))
