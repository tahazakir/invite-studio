# Evaluation

Confidence threshold (picked on seen styles): **0.92**

| method / split | n | valid JSON | full order exact | names | date | time | venue | theme | auto-approved | accuracy of auto-approved | errors sent to review |
|---|---|---|---|---|---|---|---|---|---|---|---|
| rules/test_seen | 100 | 100.0% | 12.0% | 45.0% | 100.0% | 89.0% | 38.0% | 99.0% | 74.0% | 12.2% | 26.1% |
| rules/test_heldout | 200 | 100.0% | 0.0% | 56.5% | 100.0% | 91.5% | 8.5% | 98.5% | 79.5% | 0.0% | 20.5% |
| finetuned/test_seen | 100 | 100.0% | 97.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 82.0% | 100.0% | 100.0% |
| finetuned/test_heldout | 200 | 100.0% | 96.0% | 100.0% | 99.0% | 100.0% | 99.0% | 99.5% | 68.0% | 100.0% | 100.0% |
| base_2shot/test_seen | 100 | 100.0% | 17.0% | 97.0% | 76.0% | 94.0% | 99.0% | 33.0% | 2.0% | 100.0% | 100.0% |
| base_2shot/test_heldout | 100 | 100.0% | 10.0% | 95.0% | 79.0% | 86.0% | 96.0% | 31.0% | 1.0% | 100.0% | 100.0% |
