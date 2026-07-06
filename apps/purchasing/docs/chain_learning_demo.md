# Chain Learning Demo

Lisa's pitch: your best location's purchasing discipline becomes the baseline for all four.

## Walkthrough

1. Seed the chain demo:

   ```bash
   curl -X POST http://localhost:8020/api/purchasing/demo/chain-seed
   ```

   Expected response:

   ```json
   {"locations_seeded": 4, "total_decisions": 415, "provenance": "demo"}
   ```

2. Open the Purchasing dashboard and show the group view:

   - Downtown: 200 verified decisions, IKS 58, GREEN.
   - Airport: 120 decisions, IKS 31, AMBER.
   - Suburb: 80 decisions, IKS 18, AMBER.
   - New: 15 decisions, IKS 3, RED.

3. Click Downtown as the best location.

   Explain: Downtown has the cleanest purchasing discipline: lower waste, stronger supplier reliability, and GREEN learning.

4. Click **Transfer Now** on the Chain Learning card.

   The demo sends:

   ```json
   {
     "source_location": "downtown",
     "target_locations": ["airport", "suburb", "new"]
   }
   ```

5. Show the result:

   - Airport IKS jumps from 31 to 42.
   - Suburb IKS jumps from 18 to 29.
   - New IKS jumps from 3 to 15.

6. Key narrative:

   "Your best location's discipline became the baseline for all four. No training. No consultants. Just learned patterns, transferred in one click."

## What Transfers

- 140 centroids: 5 categories x 4 actions x 7 factors.
- 35 DK weights: 5 categories x 7 factors.
- Pattern families: weather sensitivity and event lead time.

All generated data carries `provenance="demo"`.
