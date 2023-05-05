## Possible problems and solutions

`[1]` __BinanceAPIException__ <br>
&emsp; &ensp; &ensp; Invalid API-key, IP, or permissions for action

- API key is corrupted:
  - check a correct `--api` option is given
  - check if `--testnet` flag is set or not
  - check API key in `credentials.json` vs `binance.com`
- Trusted IP is invalid:
  - check if any VPN is turned on your computer on
  - check current IP vs `binance.com`
- Permissions are invalid:
  - check permissions in `credentials.json` vs `binance.com`
  - check specified permissions corresponds to API is used

`[2]`