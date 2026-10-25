# Sample documents

**Mock documents only.** Never put a real person's fine, visa or contract in this repo.

How to make a mock document:
1. Find the layout of a real document type (fine, residency notice, tenancy contract).
2. Recreate it in Word, Canva or Google Docs with fake names, fake reference numbers and a fake plate number.
3. Print it and take a phone photo (realistic for testing), or export it as PDF/PNG.
4. Save it here as `traffic_fine_01.jpg`, `residency_01.jpg`, `tenancy_01.pdf` and so on.

For each sample, add a row to `expected.csv` so we can measure accuracy for the pitch:

```
file,doc_type,emirate,amount_aed,deadline_date,service_id
traffic_fine_01.jpg,traffic_fine,Dubai,600,,dubai-traffic-fine
```

Real documents (for private testing only, e.g. a teammate's own old fine) go in `samples/private/`, which git ignores.
