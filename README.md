# 2024 QuantMinds-CompatibL TradeEntry Hackathon

# Overview

- **Date**: Monday, November 18
- **Format**: In person at the QuantMinds venue and online
- **Topic**: Trade entry for what-if analysis
- **Trades**: Non-callable interest rate swaps
- **Streams**: Non-coding and coding
- **Models**: GPT-4o and LLAMA3 70b
- **Awards**:
  - Certificates for the top three spots in each stream and model combination
  - A free QuantMinds 2025 pass for the Grand Prize winner (one individual pass per team)
- **Stay Updated**:
  - Due to restrictions on bulk email, announcements and updates will be on LinkedIn at [https://www.linkedin.com/company/tradeentry](https://www.linkedin.com/company/tradeentry)
  - Follow the page to receive notifications

# Rules

- Non-coding participants will submit their entry via the online playground at [https://hackathon.tradeentry.ai](https://hackathon.tradeentry.ai)
- Coding participants will submit their entry via GitHub
- Limit of 50 model API calls per trade for each model
- Scoring will be done using OpenAI.com for gpt-4o and Fireworks.ai for LLAMA3-70b. Development can be done using any provider or in-house GPUs.
- Participants will be able to specify temperature for scoring. All other model parameters will use the default values from OpenAI and Fireworks.

# Scoring

- 20 real-life examples of non-callable swap descriptions for what-if analysis will be sourced from trader messages and anonymized
- At the hackathon start, 10 of these examples will be randomly drawn and posted to LinkedIn at [https://www.linkedin.com/company/tradeentry](https://www.linkedin.com/company/tradeentry)
- The online playground and GitHub repository will be updated with these examples
- At the end of the hackathon, the remaining 10 examples will be used for scoring
- The score will be calculated as the fraction of correctly extracted fields from 10 scoring runs on each of the 10 examples

# Score Calculation

- Each individual or team will submit one entry in either the non-coding or coding category
- All submissions will be scored on gpt-4o and LLAMA3 70b models to produce the leaderboard for each stream/model combination
- The maximum score from these four combinations wins the Grand Prize
- The score will be calculated as the number of correctly extracted fields from 10 scoring runs on each of the 10 examples
- Empty values for which the correct value is not empty (and vice versa) will be counted as zero
- The score will be expressed in percentage points

## Copyright

Each individual contributor holds copyright over their contributions to the
project. The project versioning is the sole means of recording all such
contributions and copyright details. Specifying corporate affiliation or
work email along with the commit shall have no bearing on copyright ownership
and does not constitute copyright assignment to the employer. Submitting a
contribution to this project constitutes your acceptance of these terms.

Because individual contributions are often changes to the existing code,
copyright notices in project files must specify The Project Contributors and
never an individual copyright holder.

