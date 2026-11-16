---
name: go
version: 1.0.0
description: minimal 2-char-name regression skill (findable only via its 2-char name term)
---

Regression fixture for the short-query filter fix (v2.2.9): the query is
"go"; under the old `len(t) > 2` filter the only term was dropped and this
library returned exit 1 (no match). Now 2-char terms are kept -> exit 0.
