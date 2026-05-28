# BM25 Algorithm: A Step-by-Step Mathematical Example

This document breaks down the exact math behind the BM25 algorithm using a real-world example.

## The Setup
Imagine our "database" has three documents:
* **Doc 1 (Standard):** 13 words total.
* **Doc 2 (Expedited):** 19 words total.
* **Doc 3 (Tracking):** 14 words total.

**Database Averages:**
* Total Documents (N): `3`
* Average Document Length (avgdl): `15.33` words

We want to calculate the score for **Doc 2** when a user searches for the query: **"expedited fees refundable"**.

## The BM25 Formula
For every word in the search query, BM25 calculates two things and multiplies them together:
1. **IDF (Inverse Document Frequency):** How rare is the word overall?
2. **TF Payload (Term Frequency):** How many times does the word appear in this specific document, adjusted for length?

**Tuning Constants:**
* `k1 = 1.5` (Controls weight for repeated words)
* `b = 0.75` (Controls how much a document's length penalizes its score)

---

## Step 1: Calculate Rarity (IDF) for "expedited"
* Total documents = `3`
* Documents containing "expedited" = `1` (Only Doc 2)

```text
IDF = ln( 1 + (Total Docs - Docs with word + 0.5) / (Docs with word + 0.5) )
IDF = ln( 1 + (3 - 1 + 0.5) / (1 + 0.5) )
IDF = ln( 1 + 1.667 )
IDF = 0.98
```
*(Note: The words "fees" and "refundable" also appear in exactly 1 document, so their IDF is also 0.98).*

## Step 2: Calculate Frequency (TF Payload) for "expedited"
The word "expedited" appears `2` times in Doc 2. Doc 2 is 19 words long.

**A. Calculate Length Penalty:**
```text
Penalty = 1 - b + (b * (Doc Length / Avg Doc Length))
Penalty = 1 - 0.75 + (0.75 * (19 / 15.33))
Penalty = 0.25 + 0.929 = 1.179
```

**B. Calculate Denominator:**
```text
Denominator = Frequency + (k1 * Penalty)
Denominator = 2 + (1.5 * 1.179) = 3.768
```

**C. Calculate Numerator:**
```text
Numerator = Frequency * (k1 + 1)
Numerator = 2 * (1.5 + 1) = 5.0
```

**D. Final TF Payload:**
```text
TF Payload = Numerator / Denominator
TF Payload = 5.0 / 3.768 = 1.326
```

## Step 3: Combine Rarity and Frequency
```text
Word Score = IDF * TF Payload
Word Score = 0.98 * 1.326 = 1.30
```

## Step 4: Add up all words in the query
Repeating the math for "fees" (frequency `1`) and "refundable" (frequency `1`):
* Score for "fees" = `0.98 * 0.903 = 0.88`
* Score for "refundable" = `0.98 * 0.903 = 0.88`

**Final Score for Doc 2:**
```text
Total Score = Score("expedited") + Score("fees") + Score("refundable")
Total Score = 1.30 + 0.88 + 0.88 = 3.06
```
Because Docs 1 and 3 do not contain any of these words, their scores are exactly **0**. Doc 2 is the most relevant!