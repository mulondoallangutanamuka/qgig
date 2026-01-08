# Supabase Connection String for Render

## Exact DATABASE_URL for Render Environment

Use this **exact** connection string in Render Dashboard → Environment:

```
postgresql://postgres.bbwegjrxnoijlpcuiocs:YOUR_PASSWORD@aws-0-us-west-2.pooler.supabase.com:6543/postgres
```

## Replace YOUR_PASSWORD with your actual Supabase database password

### Step-by-Step:

1. **Go to Render Dashboard**
   - Navigate to your `qgig-backend` service
   - Click **Environment** tab

2. **Find or Add DATABASE_URL**
   - If it exists, click **Edit**
   - If not, click **Add Environment Variable**

3. **Set the value to:**
   ```
   postgresql://postgres.bbwegjrxnoijlpcuiocs:YOUR_ACTUAL_PASSWORD@aws-0-us-west-2.pooler.supabase.com:6543/postgres
   ```

4. **Important Details:**
   - Username MUST be: `postgres.bbwegjrxnoijlpcuiocs` (includes project ref)
   - Host: `aws-0-us-west-2.pooler.supabase.com`
   - Port: `6543` (pooler port, NOT 5432)
   - Database: `postgres`
   - NO square brackets around password
   - NO spaces in the connection string

5. **Save and Deploy**
   - Click **Save Changes**
   - Render will automatically redeploy

## Why This Format?

- **Pooler connection** avoids IPv6 routing issues on Render
- **Username format** `postgres.<project_ref>` is required by Supabase pooler
- **Port 6543** is the connection pooler (not direct 5432)

## Troubleshooting

If you still get errors:
1. Verify password has no typos
2. Check for extra spaces in the connection string
3. Ensure DATABASE_URL is set in Render (not empty)
4. Check Render logs for the exact error message
