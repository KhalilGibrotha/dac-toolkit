<!-- What changes, and why. Link the issue if one exists. -->

## Checklist

- [ ] **Does any README or guide now disagree with, or omit, this behavior?**
      Three changes in a row (table widths, cell autolinks, the status enum)
      shipped behavior no prose documented. If the answer is "it was never
      documented," this PR is where that ends.
- [ ] Tests cover the change, or the PR says why they cannot
      (render-inspection evidence counts — say what was measured).
- [ ] If the render path changed: a real document was rendered and read,
      not just built.
- [ ] If a status value, front-matter field, or config key changed: the
      consuming repos' synced copies and ship lists are accounted for.
