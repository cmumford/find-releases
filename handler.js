// Copyright 2016 The Chromium Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

function go() {
  var content = document.getElementById('content');
  var p = document.createElement('p');
  var wrap_commit = function(commit) {
    return '<a href="https://crrev.com/' + commit + '">' + commit.substr(0, 8) + '...</a>';
  }
  var html_data = '';
  if (window.location.hash) {
    var commit = window.location.hash.substring(1);
    var commit_data = null;
    if (!data.hasOwnProperty(commit)) {
      var html_data = '<p>Commit "' + commit + '" data not found.</p>';
      html_data += '<p>Looking at prefix short commits...</p>';
      // See if the given commit was just the beginning of a full SHA1.
      for (var candidate in data) {
        if (data.hasOwnProperty(candidate)) {
          if (candidate.startsWith(commit)) {
            if (commit_data) {
              html_data += '<p>"' + commit + '" is ambiguous.</p>';
              commit_data = null;
              break;
            }
            commit_data = data[candidate];
            commit = candidate;
          }
        }
      }
    } else {
      var commit_data = data[commit];
    }

    if (commit_data) {
      html_data += '<p>Commit ' + wrap_commit(commit);
      html_data += ' initially landed in <code>' + commit_data[0] + '</code></p>';
      var num_merges = commit_data[1].length;
      if (num_merges == 0) {
        html_data += '<p>No merges found.</p>';
      } else {
        html_data += '<ul>';
        for (var i = 0; i < num_merges; ++i) {
          var merge = commit_data[1][i];
          html_data += '<li>Merged to <code>' + merge[0] + '</code>';
          html_data += ' (as ' + wrap_commit(merge[1]) + ').</li>';
        }
        html_data += '</ul>';
      }
    }
  } else {
    html_data = 'No commit specified.';
  }
  p.innerHTML = html_data;
  content.appendChild(p);
}
