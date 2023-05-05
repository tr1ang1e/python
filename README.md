## Quickstart guide

<br>

`[1]` Install Python if necessary (https://www.python.org/downloads/windows/) <br>
`[2]` **Win+R > "cmd" > Enter** <br>
`[3]` Commands:

        $ dir                                         # to see current directory content`
        $ cd <path>                                   # destination directory path
        $ git clone --single-branch --branch bnc https://github.com/tr1ang1e/python.git bnc
        $ dir                                         # ensure that repo was cloned
        $ cd bnc                                      # go iside coned repo
        $ python.exe install -r requirements.txt      # install python required libraries

`[4]` Leave terminal but keep it opened <br>
`[5]` Go to `<path>/bnc/settings/` <br>
`[6]` Rename "credentials.json.template" to "credentials.json" <br>
`[7]` Open credentials.json and change values of the following fields: <br>
    &emsp; &emsp; &emsp; `api::testnet::key_api` <br>
    &emsp; &emsp; &emsp; `api::testnet::key_secret` <br>
`[8]` Save the file and go back to the terminal again <br>
`[9]` Commands:

        $ python.exe ./bnc.py --help                  # prompt
        $ python.exe ./bnc.py --testnet               # start program execution

<br>

## Possible problems and solutions

<br>

`[1]` __BinanceAPIException__ <br>
&emsp; &ensp; &ensp; Invalid API-key, IP, or permissions for action

- API key is corrupted:
  - check a correct `--api` option is given
  - check if `--testnet` flag is set or not
  - check API key in `credentials.json` vs `binance.com`
- Trusted IP is invalid:
  - check if any VPN is turned on your computer on
  - check current IP vs. `binance.com`
- Permissions are invalid:
  - check permissions in `credentials.json` vs `binance.com`
  - check specified permissions corresponds to API is used

<br>

`[2]`