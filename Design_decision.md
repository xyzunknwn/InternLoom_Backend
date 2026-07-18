InternLoom Backend - Design Decisions

1. Handling Email Re-verification (Section 3.1)

Question: A student who is verified and then changes their email must re-verify. How does your system handle this without locking them out immediately?

Decision: To prevent a verified student from being abruptly locked out, the system will temporarily store the newly requested email in a separate pending_email database column, while their original email remains active for login and platform access. The student continues to use the platform normally. Once they click the OTP verification link sent to the new address, the API seamlessly replaces the active email field with the pending_email value and clears the pending field. This ensures a zero-downtime transition while strictly enforcing the verification rule.

2. Dynamic Match Score Updates (Section 3.3)

Question: What happens if a company edits the required skills of an Active listing that already has 15 applicants? Do the existing applicants' match scores change? Does the company see stale data?

Decision: The company will never see stale data. Because the matching scores are computed dynamically at query time (in-memory) rather than being hardcoded into a database column, any changes to a job's required_skills take immediate effect. When the company loads their applicant dashboard, the MatchingEngine recalculates the scores for all 15 existing applicants against the newly updated job requirements. The existing applicants are not penalized or removed, but their visible match scores will shift in real-time to accurately reflect their alignment with the new criteria.

3. Matching Engine Optimization (Section 3.4)

Question: The matching score is computed at query time, not stored. Your implementation must not be an $O(n^2)$ naive approach. How do you optimize it?

Decision: To prevent an $O(n^2)$ bottleneck at scale, the system avoids fetching and scoring every single active job in the database. Instead, it utilizes database-level pre-filtering (using PostgreSQL's indexing) to drastically reduce the search space before any Python memory is used. The initial SQL query filters out listings based on hard constraints (like an exact target_batch mismatch or jobs outside the student's geographic preference). Once the dataset is reduced from potentially hundreds of thousands to a highly relevant subset, the in-memory Python algorithm calculates the weighted skill overlaps and recency decay. At massive scale, this logic would be offloaded entirely to a specialized search index like Elasticsearch or PostgreSQL's JSONB indexing capabilities.