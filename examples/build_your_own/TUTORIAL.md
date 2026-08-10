# Build Your Own Copilot tutorial

## Step 1: Read the two skins

Compare `domains/email.py` and `domains/reading.py`. Their actions, metadata
factors, categories, and asymmetric penalties are the only domain-specific
choices in the template.

## Step 2: Define your domain

Copy a skin. Name three or more actions, categories, and metadata factors.
Do not add message bodies, article text, or other content. Keep verified
correctness in the oracle or real outcome stream.

## Step 3: Choose the asymmetry

Set `PENALTY_RATIO` to express which mistake is more costly. This feeds the
same SDK `RewardComputer` used by the reward-max comparison arm.

## Step 4: Run the governed path

Run `python -m examples.build_your_own.run --domain email --decisions 300`.
Read the quality curve, decisions, and conservation statuses in `report.html`.

## Step 5: Toggle governance

Run again with `--ungoverned`. The baseline is a contextual LinUCB reward
maximizer, not a random strawman. Compare the two arms on the same synthetic
metadata stream and inspect the high-risk slice.

## Step 6: Connect verified outcomes

Replace the synthetic oracle adapter with verified outcomes from your product.
Keep the generator and decision code unaware of correctness. The five SDK
copilots are deeper references for production wiring, persistence, and UI.
