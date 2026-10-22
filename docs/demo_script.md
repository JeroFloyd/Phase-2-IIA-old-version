# Suggested Part A Demo

## Case 1: MED1001
Expected integrated evidence:
- Manufacturer exists
- Distributor exists
- Retailer exists
- Item scan exists
- Authority record is `NO_ADVERSE_REPORT`

Expected application outcome: `ASALI`

## Case 2: MED1002
Expected integrated evidence:
- Manufacturer exists
- Distributor exists
- Retailer exists
- Item scan exists
- Authority record is `CONFIRMED_NAKALI`

Expected application outcome: `NAKALI`

## Case 3: MED1008
Expected integrated evidence:
- Manufacturer exists
- Retailer record is absent
- Item scan record is absent
- Distributor record is absent
- Authority record is `UNDER_REVIEW`

Expected application outcome: `UNVERIFIED`

## Case 4: MED9999
Expected integrated evidence:
- Retailer exists
- Item scan exists
- Manufacturer record is absent
- Distributor record is absent
- Authority record is absent

Expected application outcome: `UNVERIFIED`

These are synthetic demonstration records created specifically to exercise the integration paths. They are not claims about real medicines, companies, or government cases.
