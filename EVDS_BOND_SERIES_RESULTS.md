# EVDS Bond Series Search Results

## Summary

- **TP.TAHVIL.Y2** and **TP.TAHVIL.Y10** return N/A in your app (likely discontinued or restricted).
- EVDS metadata endpoints (categories, datagroups, serieList) return **403 Forbidden** from the sandbox.
- EVDS series data endpoint responds with **403** for bond-related codes in automated runs; API key authentication can be inconsistent depending on environment.

## Recommended Manual Steps

1. **Log into EVDS:** https://evds2.tcmb.gov.tr/ → Giriş Yap
2. **Open "Tüm Seriler" (All Series):** https://evds2.tcmb.gov.tr/index.php?/evds/serieMarket
3. **Check these groups:**
   - **FAİZ VE KÂR PAYI İSTATİSTİKLERİ** (Interest Statistics) – collapse_3
   - **MENKUL KIYMET İSTATİSTİKLERİ** (Securities Statistics) – collapse_5
   - **DİĞER FİNANSAL VERİLER** (Other Financial Data) – collapse_31
4. **Search terms:** "gösterge", "tahvil", "2 yıl", "10 yıl", "devlet borçlanma"
5. **Use "Sık Kullanılan Seriler" (Frequently Used Series)** if bond series are listed there.

## Candidate Series Codes to Test

Use your EVDS API key and test these codes. The script `search_evds_bonds.py` runs these checks.

| Code | Description |
|------|-------------|
| TP.TAHVIL.Y2 | TR 2Y Tahvil (old – likely discontinued) |
| TP.TAHVIL.Y10 | TR 10Y Tahvil (old – likely discontinued) |
| TP.DK.GSY.G02 | Gösterge 2Y variant |
| TP.DK.GSY.G10 | Gösterge 10Y variant |
| TP.DK.GSY.2Y | Gösterge 2Y |
| TP.DK.GSY.10Y | Gösterge 10Y |
| TP.FB.TAHVIL.2Y | Secondary market 2Y |
| TP.FB.TAHVIL.10Y | Secondary market 10Y |

## Datagroup API (Alternative)

You can also fetch data by datagroup:

```
https://evds2.tcmb.gov.tr/service/evds/datagroup=bie_xxx&startDate=DD-MM-YYYY&endDate=DD-MM-YYYY&type=json
```

Header: `key: YOUR_EVDS_API_KEY`

Possible datagroups:
- **bie_abtkry** – Açık Borsa Tahvil (Open Market Bonds)
- **bie_abtkfaiz** – Açık Borsa Tahvil Faiz (Bond rates)
- **bie_dkdovytl** – Debt/FX (example from evdspy)

## Run the Search Script

```bash
cd my_terminal
python search_evds_bonds.py
```

This will test all candidate codes and report which ones return valid recent data. If EVDS_API_KEY is set correctly and the API allows access, the script will list working codes.

## If EVDS Has No Working Bond Series

Consider alternatives:

1. **Trading Economics** or **Investing.com** – not free
2. **Borsa Istanbul API** – for secondary market bond data
3. **Bloomberg/Reuters** – professional feeds
4. **TCMB “Gösterge Niteliğindeki Merkez Bankası Kurları”** – FX benchmarks (not bonds)
