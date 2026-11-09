# Limits and next steps

- Synthetic menus only; photographed menus (shadows, curved pages, decorative fonts, multi-line descriptions) are
  untested and will be worse.
- Two columns are handled, three or more and boxed layouts are not; LayoutLM-style document models are the next step.
- The currency-glyph fix is a page-level heuristic; a real menu where most prices start with 8 and no `$` is shown
  would be mis-corrected (prices >= 80 only).
- No dedupe or normalisation across restaurants ("Fries" vs "French Fries"); that is the competitive-database step.
- Throughput is about 8 s per menu on CPU; 1,000 menus is hours, not the 30 minutes claimed, until batched on a GPU.
