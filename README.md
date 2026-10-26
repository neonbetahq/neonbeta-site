# NeonBeta site and deals feed

Files
- `index.html` is the website (Cloudflare Pages serves it).
- `fetch_deals.py` + `post_discord.py` + `.github/workflows/update.yml` fetch deals from CheapShark every 6 hours, save `data/deals.json`, and post new historical lows to Discord.
- `data/picks.json` holds your hand-picked deals (NeonBeta Picks).

## Setup
1. Create a **public** GitHub repo (for example `neonbeta-site`) under the NeonBeta account and upload everything here, including the `.github` folder.
2. In Discord, make a webhook in #historical-lows (Edit Channel, Integrations, Webhooks) and copy its URL.
3. In the repo go to Settings, Secrets and variables, Actions, and add:
   - `DISCORD_WEBHOOK_LOWS` = the webhook URL
   - `DISCORD_ROLE_PRICE_DROP` = the Price Drop Pings role ID (optional)
4. Open the Actions tab, pick "Update deals", press Run workflow. `data/deals.json` should appear.
5. Host the site: Cloudflare, Pages, connect to Git, choose the repo, no build command, output directory `/`.

## Adding a pick
Edit `data/picks.json` (in the GitHub app or website). Prices are in USD.
```
{"updated":"2026-10-26","picks":[
 {"title":"Game name","store":"GOG","price":13.49,"regular":29.99,
  "url":"https://store link or your affiliate link","note":"Lowest we have seen. Checked 26 Oct.",
  "date":"2026-10-26","active":true}
]}
```
Set `"active":false` when a deal ends. Keep old entries, they become your own price history.

## Rules
- Never put the webhook URL or any key in a file. Only in repo secrets.
- CheapShark deals must use CheapShark links (the script does this). Picks must not use CheapShark data.
- Picks links must start with https://.
