# Results

`output/eval.json` on this machine, five synthetic menus, 71 ground-truth items:

| Measure | Value |
|---|---|
| Item recall | 1.00 |
| Price accuracy on found items | 1.00 |
| Category recall | 1.00 |
| Files failed | 0 of 5 |
| Seconds per menu (CPU) | 8.1 average (first file includes model load), 4-6 steady |

The original write-up claimed 94% item-price association; on these clean renders the pipeline is at 100%, which is
the ceiling for the synthetic set and not a number to expect on photographs. A good number on real menu photos would
be 85-90% with the error log catching the rest.
