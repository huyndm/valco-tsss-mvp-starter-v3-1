# PHASE 3.2 Big Patch Note

Implemented deterministic ValCo TSSS rule layer:

- Land conversion standard:
  - Residential / ONT / ODT / đất ở = 100%
  - TMDV = 85%
  - SKC = 75%
  - CLN = 60%

- Adjustment ratio guard:
  - Total adjustment ratio must be < 40%
  - >= 40% is flagged by hard filter logic

- No double-counting:
  - Rule module supports land_type_already_adjusted=True
  - Land type component is skipped and warning is recorded

Patch was applied by local Python script, not by Roo/LLM.
