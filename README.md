# ffbuild

An FFmpeg filter graph and command line (coming soon) builder for Python.

Code:

```Python
from ffbuild import FilterGraph, Filter


graph = FilterGraph()

(split,) = graph.append_filter('split', input='0:v', output=('a', 'b'))
link_a, link_b = split.output

graph.append_filter('select', 'eq(n, 0)', input=link_a, output='c')

graph.append(
    Filter('trim', start_frame=10, end_frame=150, input=link_b),
    Filter('scale', 1280, -1, output='d'),
)

print(graph)
```

Output:

```
[0:v] split [a][b];
[a] select='eq(n\, 0)' [c];
[b] trim=start_frame=10:end_frame=150, scale=1280:-1 [d]
```

## Install

```ShellSession
$ git clone https://github.com/petersuttondev/ffbuild.git
$ cd ffbuild
$ pip install .
```
