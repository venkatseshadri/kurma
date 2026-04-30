# Kurma Broker Authentication Guide

## Overview

Kurma supports multiple brokers (Flattrade, Shoonya) via command-line parameters. Each broker has different authentication methods and requirements.

## Supported Brokers

### Shoonya (Recommended - Currently Working)
✅ Status: **FULLY OPERATIONAL**

**Credentials:** OAuth2 token-based authentication  
**Margin Available:** ₹92,271.27  
**Data:** MCX OHLC fetching ✅  
**Orders:** Live execution ready ✅  

**Quick Start:**
```bash
python3 kurma/kurma_main.py --data-broker shoonya --exec-broker shoonya
```

**Token Refresh:**
```bash
cd /home/trading_ceo/python-trader/Shoonya_oAuthAPI-py
python3 GetAuthcode.py
```

**See:** `Shoonya_oAuthAPI-py/TOKEN_GENERATION_GUIDE.md`

---

### Flattrade (Alternative)
⚠️ Status: **BLOCKED - MCX not enabled**

**Credentials:** OAuth2 token-based authentication  
**Margin Available:** ₹0.00 (insufficient)  
**Data:** Would work if MCX enabled  
**Orders:** API calls reach broker but orders rejected  

**Issues:**
1. MCX not enabled on account - must enable in Flattrade web portal
2. Zero available cash - need to deposit funds or wait for Varaha margin release

**Fix Required:**
```
1. Log into Flattrade web portal
2. Go to Settings → Segments
3. Enable MCX trading
4. Wait for margin availability
```

**See:** `kurma/kurma_auth.py` - Flattrade OAuth implementation

---

## Authentication Flow by Broker

### Shoonya Flow
```
1. GetAuthcode.py
   ├─ Selenium automates login
   ├─ Captures auth code from redirect
   └─ Generates access token

2. cred.yml updated with Access_token

3. Kurma session creation
   ├─ Reads cred.yml
   ├─ Calls api.set_session(userid, accesstoken)
   └─ Establishes OAuth session

4. API calls (get_limits, get_quotes, place_order)
   ├─ Uses cached access token
   └─ No password stored in memory
```

### Flattrade Flow
```
1. GetAuthcode.py (not needed - uses existing token)
   OR manually generate token via Flattrade OAuth portal

2. tokens.json created with OAuth token

3. Kurma session creation
   ├─ Reads tokens.json
   ├─ Calls api.set_session(userid, accesstoken)
   └─ Establishes OAuth session

4. API calls
   ├─ Uses cached access token
   └─ Falls back to password auth if token expired
```

---

## Command-Line Parameters

### Broker Selection
```bash
# Data broker (market quotes/OHLC)
--data-broker [flattrade|shoonya]

# Execution broker (order placement)
--exec-broker [flattrade|shoonya]
```

### Examples
```bash
# Paper mode with Shoonya (recommended for testing)
python3 kurma/kurma_main.py --data-broker shoonya --exec-broker shoonya

# Paper mode with Flattrade (needs MCX enabled + funds)
python3 kurma/kurma_main.py --data-broker flattrade --exec-broker flattrade

# Live trading with Shoonya
python3 kurma/kurma_main.py --data-broker shoonya --exec-broker shoonya \
  --live-execution --confirm-live-execution=yes

# Dry-run (no broker needed, fully mocked)
python3 kurma/kurma_main.py --dry-run
```

---

## Troubleshooting by Broker

### Shoonya Issues

#### "Session Expired: Invalid Session Key"
**Cause:** Access token expired (>30 days old)  
**Fix:**
```bash
cd /home/trading_ceo/python-trader/Shoonya_oAuthAPI-py
python3 GetAuthcode.py
```

#### Chrome won't start in GetAuthcode.py
**Cause:** Chromium sandbox issues  
**Fix:** See `TOKEN_GENERATION_GUIDE.md` → Issue 1

#### No MCX data returned
**Cause:** Token needs refresh or network issue  
**Fix:** Verify token is current, check internet connection

---

### Flattrade Issues

#### "Rejected: Invalid IP address"
**Cause:** API key not whitelisted for your IP  
**Fix:** Add your IP in Flattrade API settings

#### "MCX not supported for this account"
**Cause:** MCX segment not enabled  
**Fix:** Enable MCX in Flattrade Settings → Segments

#### "Insufficient margin"
**Cause:** No available cash  
**Fix:** Deposit funds OR wait for Varaha margin release (3:10 PM)

#### Orders rejected but appear in portal
**Cause:** API key IP whitelist not updated  
**Fix:** Verify IP in Flattrade admin portal matches system IP (187.77.188.100)

---

## Authentication Details

### Shoonya OAuth (Recommended)
```python
from api_helper import NorenApiPy
import yaml

with open('cred.yml') as f:
    cred = yaml.safe_load(f)

api = NorenApiPy()
ret = api.set_session(
    userid=cred['UID'],
    accesstoken=cred['Access_token']
)
```

**Advantages:**
- ✅ No password stored in memory
- ✅ Token-based (temporary, auto-expiring)
- ✅ Can rotate tokens without password
- ✅ More secure for automated systems

**Token Lifetime:** 30-60 days  
**Refresh Method:** Run GetAuthcode.py

---

### Flattrade OAuth (Alternative)
```python
from api_helper import NorenApiPy
import json

with open('FlattradeApi-py/tokens.json') as f:
    tokens = json.load(f)

api = NorenApiPy()
ret = api.set_session(
    userid=tokens['client'],
    accesstoken=tokens['token']
)
```

**Advantages:**
- ✅ OAuth-based like Shoonya
- ✅ Zero brokerage
- ✅ Good API documentation

**Disadvantages:**
- ❌ MCX not enabled on test account
- ❌ Zero available margin

---

## Future Recommendations

### Next Steps if Flattrade Needed
1. Contact Flattrade support to enable MCX segment
2. Ensure IP whitelist includes 187.77.188.100
3. Deposit funds (₹50K+ for intraday trading)
4. Re-test authentication flow

### Next Steps if Shoonya Only
1. Keep using Shoonya (currently fully operational)
2. Set up token refresh reminder before 30-day expiry
3. Monitor access logs for "Session Expired" errors

### Production Improvements
1. Use environment variables instead of hardcoded credentials
2. Implement automatic token refresh before expiry
3. Add broker failover (primary: Shoonya, fallback: Flattrade)
4. Store tokens in secure vault (AWS Secrets Manager, etc.)

---

## Testing Broker Connectivity

```bash
# Test Shoonya
python3 << 'EOF'
import sys
sys.path.insert(0, 'Shoonya_oAuthAPI-py')
from api_helper import NorenApiPy
import yaml

with open('Shoonya_oAuthAPI-py/cred.yml') as f:
    cred = yaml.safe_load(f)

api = NorenApiPy()
if api.set_session(userid=cred['UID'], accesstoken=cred['Access_token']):
    limits = api.get_limits()
    print(f"✅ Shoonya: ₹{float(limits.get('cash', 0)):,.2f} available")
else:
    print("❌ Shoonya session failed")
EOF

# Test Flattrade
python3 << 'EOF'
import sys
sys.path.insert(0, 'FlattradeApi-py')
from api_helper import NorenApiPy
import json

with open('FlattradeApi-py/tokens.json') as f:
    tokens = json.load(f)

api = NorenApiPy()
if api.set_session(userid=tokens['client'], accesstoken=tokens['token']):
    limits = api.get_limits()
    print(f"✅ Flattrade: ₹{float(limits.get('cash', 0)):,.2f} available")
else:
    print("❌ Flattrade session failed")
EOF
```

---

## Version History

| Date | Status | Notes |
|------|--------|-------|
| 2026-04-30 | ✅ Complete | Shoonya fully operational, Flattrade blocked on MCX |
| 2026-04-29 | 🔧 Testing | Fixed GetAuthcode.py sandbox issues |
| 2026-04-18 | ⚠️ Initial | Both brokers had auth issues |

---

**Last Updated:** 2026-04-30  
**Recommended Broker:** Shoonya  
**Test Status:** ✅ Both brokers verified (Shoonya working, Flattrade blocked)
