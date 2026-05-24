# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: trading\regime-recommend.spec.ts >> Regime detail shows conservation status
- Location: trading\regime-recommend.spec.ts:33:1

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: locator('section').filter({ has: getByRole('heading', { name: 'Market Regime' }) }).first().locator('div').filter({ has: getByRole('heading', { name: 'Detailed Recommendations' }) }).first().getByText(/Conservation confirmed|Conservation not confirmed/i).first()
Expected: visible
Timeout: 10000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" with timeout 10000ms
  - waiting for locator('section').filter({ has: getByRole('heading', { name: 'Market Regime' }) }).first().locator('div').filter({ has: getByRole('heading', { name: 'Detailed Recommendations' }) }).first().getByText(/Conservation confirmed|Conservation not confirmed/i).first()

```

# Page snapshot

```yaml
- generic [ref=e4]:
  - banner [ref=e5]:
    - generic [ref=e6]:
      - generic [ref=e7]: $
      - generic [ref=e8]:
        - heading "Trading Copilot" [level=1] [ref=e9]
        - paragraph [ref=e10]: Compounding intelligence workspace
    - generic [ref=e11]:
      - generic "IKS 25" [ref=e12]:
        - generic [ref=e14]: "25"
      - generic [ref=e15]: IKS
  - navigation [ref=e16]:
    - button "Dashboard" [ref=e17] [cursor=pointer]
    - button "Log Trade" [ref=e18] [cursor=pointer]
    - button "Analysis" [ref=e19] [cursor=pointer]
    - button "Performance" [ref=e20] [cursor=pointer]
    - button "Journal" [ref=e21] [cursor=pointer]
    - button "Trade Detail" [ref=e22] [cursor=pointer]
  - main [ref=e23]:
    - generic [ref=e25]:
      - generic [ref=e26]: P
      - generic [ref=e27]: Paper
    - generic [ref=e28]:
      - generic [ref=e29]:
        - generic [ref=e30]:
          - heading "Dashboard" [level=2] [ref=e31]
          - paragraph [ref=e32]: Trading Backend v2 context, analytics, and decision history.
        - button "Log New Trade" [ref=e33] [cursor=pointer]
      - generic [ref=e34]:
        - generic [ref=e36]:
          - heading "Market Context" [level=2] [ref=e37]
          - paragraph [ref=e38]: cached
        - generic [ref=e39]:
          - generic [ref=e40]:
            - generic [ref=e41]: SPY
            - generic [ref=e42]: SPY
            - generic [ref=e43]: $515.00 · -
          - generic [ref=e44]:
            - generic [ref=e45]: VIX
            - generic [ref=e46]: VIX
            - generic [ref=e47]: "- · -"
          - generic [ref=e48]:
            - generic [ref=e49]: Sectors
            - generic [ref=e50]: No sector context.
      - generic [ref=e51]:
        - generic [ref=e52]:
          - generic [ref=e53]:
            - heading "Market Regime" [level=2] [ref=e54]
            - paragraph [ref=e55]: default
          - generic [ref=e56]: RANGING
        - generic [ref=e57]:
          - generic [ref=e58]:
            - generic [ref=e59]: VIX
            - generic [ref=e60]: "20.0"
          - generic [ref=e61]:
            - generic [ref=e62]: ADX
            - generic [ref=e63]: "20.0"
          - generic [ref=e64]:
            - generic [ref=e65]: Source
            - generic [ref=e66]: default
        - generic [ref=e67]:
          - generic [ref=e68]: Regime accuracy
          - generic [ref=e69]:
            - generic [ref=e70]: crypto spot
            - generic [ref=e71]: increase
            - generic [ref=e72]: 50% accuracy
            - generic [ref=e73]: +17pp vs baseline
        - generic [ref=e74]:
          - generic [ref=e76]:
            - heading "Detailed Recommendations" [level=3] [ref=e77]
            - paragraph [ref=e78]: Allocation context by category and regime transition.
          - generic [ref=e79]: Loading detailed recommendations...
      - generic [ref=e80]:
        - generic [ref=e81]:
          - heading "Portfolio Summary" [level=2] [ref=e82]
          - paragraph [ref=e83]: Open risk and closed-trade quality
        - generic [ref=e84]:
          - generic [ref=e85]:
            - generic [ref=e86]: Open Positions
            - generic [ref=e87]: "3"
          - generic [ref=e88]:
            - generic [ref=e89]: Open Exposure
            - generic [ref=e90]: $75,840
            - generic [ref=e91]: 30%
          - generic [ref=e92]:
            - generic [ref=e93]: Closed Trades
            - generic [ref=e94]: "37"
          - generic [ref=e95]:
            - generic [ref=e96]: Win Rate
            - generic [ref=e97]: 68%
          - generic [ref=e98]:
            - generic [ref=e99]: YTD Return
            - generic [ref=e100]: 543.0%
      - generic [ref=e101]:
        - paragraph [ref=e102]: SC-12
        - heading "Accuracy Alerts" [level=2] [ref=e103]
        - paragraph [ref=e104]: Threshold 70% across 40 verified decisions.
        - generic [ref=e105]:
          - generic [ref=e107]:
            - generic [ref=e108]: crypto spot
            - strong [ref=e109]: 33%
          - generic [ref=e113]:
            - generic [ref=e114]: equity long
            - strong [ref=e115]: 67%
          - generic [ref=e119]:
            - generic [ref=e120]: etf
            - strong [ref=e121]: 83%
          - generic [ref=e125]:
            - generic [ref=e126]: options
            - strong [ref=e127]: 50%
      - generic [ref=e130]:
        - generic [ref=e131]:
          - heading "Portfolio Concentration" [level=2] [ref=e132]
          - generic [ref=e133]:
            - generic [ref=e134]:
              - generic [ref=e135]:
                - generic [ref=e136]: trendFollowing
                - generic [ref=e137]: 24 trades
              - generic [ref=e140]: P&L $10,201
            - generic [ref=e141]:
              - generic [ref=e142]:
                - generic [ref=e143]: eventDriven
                - generic [ref=e144]: 6 trades
              - generic [ref=e147]: P&L $-2,315
            - generic [ref=e148]:
              - generic [ref=e149]:
                - generic [ref=e150]: incomeStrategy
                - generic [ref=e151]: 4 trades
              - generic [ref=e154]: P&L $820
            - generic [ref=e155]:
              - generic [ref=e156]:
                - generic [ref=e157]: scalpIntraday
                - generic [ref=e158]: 6 trades
              - generic [ref=e161]: P&L $4,860
        - generic [ref=e162]:
          - heading "Thesis Breakdown" [level=2] [ref=e163]
          - generic [ref=e164]:
            - generic [ref=e166]:
              - generic [ref=e167]: momentum
              - generic [ref=e168]: 76% win rate
            - generic [ref=e172]:
              - generic [ref=e173]: event
              - generic [ref=e174]: 75% win rate
            - generic [ref=e178]:
              - generic [ref=e179]: meanReversion
              - generic [ref=e180]: 0% win rate
            - generic [ref=e184]:
              - generic [ref=e185]: technical
              - generic [ref=e186]: 100% win rate
            - generic [ref=e190]:
              - generic [ref=e191]: fundamental
              - generic [ref=e192]: 100% win rate
        - generic [ref=e195]:
          - heading "Dataset" [level=2] [ref=e196]
          - generic [ref=e197]:
            - generic [ref=e198]:
              - generic [ref=e199]: Total trades
              - generic [ref=e200]: "40"
            - generic [ref=e201]:
              - generic [ref=e202]: Open positions
              - generic [ref=e203]: "3"
            - generic [ref=e204]:
              - generic [ref=e205]: Source
              - generic [ref=e206]: computed_from_trading_seed_v2
      - generic [ref=e207]:
        - heading "Calendar Heatmap" [level=2] [ref=e208]
        - generic [ref=e209]:
          - generic "2026-03-26 NVDA" [ref=e210]
          - generic "2026-03-26 NVDA" [ref=e211]
          - generic "2026-03-26 NVDA" [ref=e212]
          - generic "2026-03-31 MSFT" [ref=e213]
          - generic "2026-03-31 MSFT" [ref=e214]
          - generic "2026-03-31 MSFT" [ref=e215]
          - generic "2026-03-31 MSFT" [ref=e216]
          - generic "2026-03-31 MSFT" [ref=e217]
          - generic "2026-03-31 MSFT" [ref=e218]
          - generic "2026-04-02 IWM" [ref=e219]
          - generic "2026-04-02 IWM" [ref=e220]
          - generic "2026-04-02 IWM" [ref=e221]
          - generic "2026-04-02 IWM" [ref=e222]
          - generic "2026-04-02 IWM" [ref=e223]
          - generic "2026-04-02 IWM" [ref=e224]
          - generic "2026-04-02 IWM" [ref=e225]
          - generic "2026-04-06 SPY" [ref=e226]
          - generic "2026-04-06 SPY" [ref=e227]
          - generic "2026-04-06 SPY" [ref=e228]
          - generic "2026-04-06 SPY" [ref=e229]
          - generic "2026-04-06 SPY" [ref=e230]
          - generic "2026-04-06 SPY" [ref=e231]
          - generic "2026-04-08 MSFT" [ref=e232]
          - generic "2026-04-08 MSFT" [ref=e233]
          - generic "2026-04-08 MSFT" [ref=e234]
          - generic "2026-04-08 MSFT" [ref=e235]
          - generic "2026-04-08 MSFT" [ref=e236]
          - generic "2026-04-08 MSFT" [ref=e237]
          - generic "2026-04-09 QQQ" [ref=e238]
          - generic "2026-04-09 QQQ" [ref=e239]
          - generic "2026-04-09 QQQ" [ref=e240]
          - generic "2026-04-09 QQQ" [ref=e241]
          - generic "2026-04-09 QQQ" [ref=e242]
          - generic "2026-04-09 QQQ" [ref=e243]
          - generic "2026-04-09 QQQ" [ref=e244]
          - generic "2026-04-10 AAPL" [ref=e245]
          - generic "2026-04-10 AAPL" [ref=e246]
          - generic "2026-04-10 AAPL" [ref=e247]
          - generic "2026-04-10 AAPL" [ref=e248]
          - generic "2026-04-10 AAPL" [ref=e249]
          - generic "2026-04-10 AAPL" [ref=e250]
          - generic "2026-04-10 AAPL" [ref=e251]
        - generic [ref=e252]:
          - generic [ref=e253]:
            - generic [ref=e254]: Monday
            - generic [ref=e255]: 13 trades
            - generic [ref=e256]: 23% win
          - generic [ref=e257]:
            - generic [ref=e258]: Tuesday
            - generic [ref=e259]: 3 trades
            - generic [ref=e260]: 100% win
          - generic [ref=e261]:
            - generic [ref=e262]: Wednesday
            - generic [ref=e263]: 4 trades
            - generic [ref=e264]: 50% win
          - generic [ref=e265]:
            - generic [ref=e266]: Thursday
            - generic [ref=e267]: 15 trades
            - generic [ref=e268]: 100% win
          - generic [ref=e269]:
            - generic [ref=e270]: Friday
            - generic [ref=e271]: 2 trades
            - generic [ref=e272]: 100% win
      - generic [ref=e273]:
        - generic [ref=e274]:
          - heading "Decision History" [level=2] [ref=e275]
          - generic [ref=e276]: "386"
        - generic [ref=e278]:
          - button "Unknown trade unclassified · timeframe n/a open - Hold open R:R - Research Conviction" [ref=e280] [cursor=pointer]:
            - generic [ref=e281]:
              - generic [ref=e282]:
                - generic [ref=e283]:
                  - generic [ref=e284]: Unknown
                  - generic [ref=e285]: trade
                - generic [ref=e286]: unclassified · timeframe n/a
              - generic [ref=e287]:
                - generic [ref=e288]: open
                - generic [ref=e289]: "-"
            - generic [ref=e290]:
              - generic [ref=e291]:
                - generic [ref=e292]: Hold
                - generic [ref=e293]: open
              - generic [ref=e294]:
                - generic [ref=e295]: R:R
                - generic [ref=e296]: "-"
              - generic [ref=e298]: Research
              - generic [ref=e306]: Conviction
          - button "Unknown trade unclassified · timeframe n/a open - Hold open R:R - Research Conviction" [ref=e314] [cursor=pointer]:
            - generic [ref=e315]:
              - generic [ref=e316]:
                - generic [ref=e317]:
                  - generic [ref=e318]: Unknown
                  - generic [ref=e319]: trade
                - generic [ref=e320]: unclassified · timeframe n/a
              - generic [ref=e321]:
                - generic [ref=e322]: open
                - generic [ref=e323]: "-"
            - generic [ref=e324]:
              - generic [ref=e325]:
                - generic [ref=e326]: Hold
                - generic [ref=e327]: open
              - generic [ref=e328]:
                - generic [ref=e329]: R:R
                - generic [ref=e330]: "-"
              - generic [ref=e332]: Research
              - generic [ref=e340]: Conviction
          - button "Unknown trade unclassified · timeframe n/a open - Hold open R:R - Research Conviction" [ref=e348] [cursor=pointer]:
            - generic [ref=e349]:
              - generic [ref=e350]:
                - generic [ref=e351]:
                  - generic [ref=e352]: Unknown
                  - generic [ref=e353]: trade
                - generic [ref=e354]: unclassified · timeframe n/a
              - generic [ref=e355]:
                - generic [ref=e356]: open
                - generic [ref=e357]: "-"
            - generic [ref=e358]:
              - generic [ref=e359]:
                - generic [ref=e360]: Hold
                - generic [ref=e361]: open
              - generic [ref=e362]:
                - generic [ref=e363]: R:R
                - generic [ref=e364]: "-"
              - generic [ref=e366]: Research
              - generic [ref=e374]: Conviction
          - button "Unknown trade unclassified · timeframe n/a open - Hold open R:R - Research Conviction" [ref=e382] [cursor=pointer]:
            - generic [ref=e383]:
              - generic [ref=e384]:
                - generic [ref=e385]:
                  - generic [ref=e386]: Unknown
                  - generic [ref=e387]: trade
                - generic [ref=e388]: unclassified · timeframe n/a
              - generic [ref=e389]:
                - generic [ref=e390]: open
                - generic [ref=e391]: "-"
            - generic [ref=e392]:
              - generic [ref=e393]:
                - generic [ref=e394]: Hold
                - generic [ref=e395]: open
              - generic [ref=e396]:
                - generic [ref=e397]: R:R
                - generic [ref=e398]: "-"
              - generic [ref=e400]: Research
              - generic [ref=e408]: Conviction
          - button "Unknown trade unclassified · timeframe n/a open - Hold open R:R - Research Conviction" [ref=e416] [cursor=pointer]:
            - generic [ref=e417]:
              - generic [ref=e418]:
                - generic [ref=e419]:
                  - generic [ref=e420]: Unknown
                  - generic [ref=e421]: trade
                - generic [ref=e422]: unclassified · timeframe n/a
              - generic [ref=e423]:
                - generic [ref=e424]: open
                - generic [ref=e425]: "-"
            - generic [ref=e426]:
              - generic [ref=e427]:
                - generic [ref=e428]: Hold
                - generic [ref=e429]: open
              - generic [ref=e430]:
                - generic [ref=e431]: R:R
                - generic [ref=e432]: "-"
              - generic [ref=e434]: Research
              - generic [ref=e442]: Conviction
          - button "Unknown trade unclassified · timeframe n/a open - Hold open R:R - Research Conviction" [ref=e450] [cursor=pointer]:
            - generic [ref=e451]:
              - generic [ref=e452]:
                - generic [ref=e453]:
                  - generic [ref=e454]: Unknown
                  - generic [ref=e455]: trade
                - generic [ref=e456]: unclassified · timeframe n/a
              - generic [ref=e457]:
                - generic [ref=e458]: open
                - generic [ref=e459]: "-"
            - generic [ref=e460]:
              - generic [ref=e461]:
                - generic [ref=e462]: Hold
                - generic [ref=e463]: open
              - generic [ref=e464]:
                - generic [ref=e465]: R:R
                - generic [ref=e466]: "-"
              - generic [ref=e468]: Research
              - generic [ref=e476]: Conviction
          - button "Unknown trade unclassified · timeframe n/a open - Hold open R:R - Research Conviction" [ref=e484] [cursor=pointer]:
            - generic [ref=e485]:
              - generic [ref=e486]:
                - generic [ref=e487]:
                  - generic [ref=e488]: Unknown
                  - generic [ref=e489]: trade
                - generic [ref=e490]: unclassified · timeframe n/a
              - generic [ref=e491]:
                - generic [ref=e492]: open
                - generic [ref=e493]: "-"
            - generic [ref=e494]:
              - generic [ref=e495]:
                - generic [ref=e496]: Hold
                - generic [ref=e497]: open
              - generic [ref=e498]:
                - generic [ref=e499]: R:R
                - generic [ref=e500]: "-"
              - generic [ref=e502]: Research
              - generic [ref=e510]: Conviction
          - button "Unknown trade unclassified · timeframe n/a open - Hold open R:R - Research Conviction" [ref=e518] [cursor=pointer]:
            - generic [ref=e519]:
              - generic [ref=e520]:
                - generic [ref=e521]:
                  - generic [ref=e522]: Unknown
                  - generic [ref=e523]: trade
                - generic [ref=e524]: unclassified · timeframe n/a
              - generic [ref=e525]:
                - generic [ref=e526]: open
                - generic [ref=e527]: "-"
            - generic [ref=e528]:
              - generic [ref=e529]:
                - generic [ref=e530]: Hold
                - generic [ref=e531]: open
              - generic [ref=e532]:
                - generic [ref=e533]: R:R
                - generic [ref=e534]: "-"
              - generic [ref=e536]: Research
              - generic [ref=e544]: Conviction
          - button "Unknown trade unclassified · timeframe n/a open - Hold open R:R - Research Conviction" [ref=e552] [cursor=pointer]:
            - generic [ref=e553]:
              - generic [ref=e554]:
                - generic [ref=e555]:
                  - generic [ref=e556]: Unknown
                  - generic [ref=e557]: trade
                - generic [ref=e558]: unclassified · timeframe n/a
              - generic [ref=e559]:
                - generic [ref=e560]: open
                - generic [ref=e561]: "-"
            - generic [ref=e562]:
              - generic [ref=e563]:
                - generic [ref=e564]: Hold
                - generic [ref=e565]: open
              - generic [ref=e566]:
                - generic [ref=e567]: R:R
                - generic [ref=e568]: "-"
              - generic [ref=e570]: Research
              - generic [ref=e578]: Conviction
          - button "Unknown trade unclassified · timeframe n/a open - Hold open R:R - Research Conviction" [ref=e586] [cursor=pointer]:
            - generic [ref=e587]:
              - generic [ref=e588]:
                - generic [ref=e589]:
                  - generic [ref=e590]: Unknown
                  - generic [ref=e591]: trade
                - generic [ref=e592]: unclassified · timeframe n/a
              - generic [ref=e593]:
                - generic [ref=e594]: open
                - generic [ref=e595]: "-"
            - generic [ref=e596]:
              - generic [ref=e597]:
                - generic [ref=e598]: Hold
                - generic [ref=e599]: open
              - generic [ref=e600]:
                - generic [ref=e601]: R:R
                - generic [ref=e602]: "-"
              - generic [ref=e604]: Research
              - generic [ref=e612]: Conviction
          - button "Unknown trade unclassified · timeframe n/a open - Hold open R:R - Research Conviction" [ref=e620] [cursor=pointer]:
            - generic [ref=e621]:
              - generic [ref=e622]:
                - generic [ref=e623]:
                  - generic [ref=e624]: Unknown
                  - generic [ref=e625]: trade
                - generic [ref=e626]: unclassified · timeframe n/a
              - generic [ref=e627]:
                - generic [ref=e628]: open
                - generic [ref=e629]: "-"
            - generic [ref=e630]:
              - generic [ref=e631]:
                - generic [ref=e632]: Hold
                - generic [ref=e633]: open
              - generic [ref=e634]:
                - generic [ref=e635]: R:R
                - generic [ref=e636]: "-"
              - generic [ref=e638]: Research
              - generic [ref=e646]: Conviction
          - button "Unknown trade unclassified · timeframe n/a open - Hold open R:R - Research Conviction" [ref=e654] [cursor=pointer]:
            - generic [ref=e655]:
              - generic [ref=e656]:
                - generic [ref=e657]:
                  - generic [ref=e658]: Unknown
                  - generic [ref=e659]: trade
                - generic [ref=e660]: unclassified · timeframe n/a
              - generic [ref=e661]:
                - generic [ref=e662]: open
                - generic [ref=e663]: "-"
            - generic [ref=e664]:
              - generic [ref=e665]:
                - generic [ref=e666]: Hold
                - generic [ref=e667]: open
              - generic [ref=e668]:
                - generic [ref=e669]: R:R
                - generic [ref=e670]: "-"
              - generic [ref=e672]: Research
              - generic [ref=e680]: Conviction
          - button "Unknown trade unclassified · timeframe n/a open - Hold open R:R - Research Conviction" [ref=e688] [cursor=pointer]:
            - generic [ref=e689]:
              - generic [ref=e690]:
                - generic [ref=e691]:
                  - generic [ref=e692]: Unknown
                  - generic [ref=e693]: trade
                - generic [ref=e694]: unclassified · timeframe n/a
              - generic [ref=e695]:
                - generic [ref=e696]: open
                - generic [ref=e697]: "-"
            - generic [ref=e698]:
              - generic [ref=e699]:
                - generic [ref=e700]: Hold
                - generic [ref=e701]: open
              - generic [ref=e702]:
                - generic [ref=e703]: R:R
                - generic [ref=e704]: "-"
              - generic [ref=e706]: Research
              - generic [ref=e714]: Conviction
          - button "Unknown trade unclassified · timeframe n/a open - Hold open R:R - Research Conviction" [ref=e722] [cursor=pointer]:
            - generic [ref=e723]:
              - generic [ref=e724]:
                - generic [ref=e725]:
                  - generic [ref=e726]: Unknown
                  - generic [ref=e727]: trade
                - generic [ref=e728]: unclassified · timeframe n/a
              - generic [ref=e729]:
                - generic [ref=e730]: open
                - generic [ref=e731]: "-"
            - generic [ref=e732]:
              - generic [ref=e733]:
                - generic [ref=e734]: Hold
                - generic [ref=e735]: open
              - generic [ref=e736]:
                - generic [ref=e737]: R:R
                - generic [ref=e738]: "-"
              - generic [ref=e740]: Research
              - generic [ref=e748]: Conviction
          - button "Unknown trade unclassified · timeframe n/a open - Hold open R:R - Research Conviction" [ref=e756] [cursor=pointer]:
            - generic [ref=e757]:
              - generic [ref=e758]:
                - generic [ref=e759]:
                  - generic [ref=e760]: Unknown
                  - generic [ref=e761]: trade
                - generic [ref=e762]: unclassified · timeframe n/a
              - generic [ref=e763]:
                - generic [ref=e764]: open
                - generic [ref=e765]: "-"
            - generic [ref=e766]:
              - generic [ref=e767]:
                - generic [ref=e768]: Hold
                - generic [ref=e769]: open
              - generic [ref=e770]:
                - generic [ref=e771]: R:R
                - generic [ref=e772]: "-"
              - generic [ref=e774]: Research
              - generic [ref=e782]: Conviction
          - button "Unknown trade unclassified · timeframe n/a open - Hold open R:R - Research Conviction" [ref=e790] [cursor=pointer]:
            - generic [ref=e791]:
              - generic [ref=e792]:
                - generic [ref=e793]:
                  - generic [ref=e794]: Unknown
                  - generic [ref=e795]: trade
                - generic [ref=e796]: unclassified · timeframe n/a
              - generic [ref=e797]:
                - generic [ref=e798]: open
                - generic [ref=e799]: "-"
            - generic [ref=e800]:
              - generic [ref=e801]:
                - generic [ref=e802]: Hold
                - generic [ref=e803]: open
              - generic [ref=e804]:
                - generic [ref=e805]: R:R
                - generic [ref=e806]: "-"
              - generic [ref=e808]: Research
              - generic [ref=e816]: Conviction
          - button "Unknown trade unclassified · timeframe n/a open - Hold open R:R - Research Conviction" [ref=e824] [cursor=pointer]:
            - generic [ref=e825]:
              - generic [ref=e826]:
                - generic [ref=e827]:
                  - generic [ref=e828]: Unknown
                  - generic [ref=e829]: trade
                - generic [ref=e830]: unclassified · timeframe n/a
              - generic [ref=e831]:
                - generic [ref=e832]: open
                - generic [ref=e833]: "-"
            - generic [ref=e834]:
              - generic [ref=e835]:
                - generic [ref=e836]: Hold
                - generic [ref=e837]: open
              - generic [ref=e838]:
                - generic [ref=e839]: R:R
                - generic [ref=e840]: "-"
              - generic [ref=e842]: Research
              - generic [ref=e850]: Conviction
          - button "Unknown trade unclassified · timeframe n/a open - Hold open R:R - Research Conviction" [ref=e858] [cursor=pointer]:
            - generic [ref=e859]:
              - generic [ref=e860]:
                - generic [ref=e861]:
                  - generic [ref=e862]: Unknown
                  - generic [ref=e863]: trade
                - generic [ref=e864]: unclassified · timeframe n/a
              - generic [ref=e865]:
                - generic [ref=e866]: open
                - generic [ref=e867]: "-"
            - generic [ref=e868]:
              - generic [ref=e869]:
                - generic [ref=e870]: Hold
                - generic [ref=e871]: open
              - generic [ref=e872]:
                - generic [ref=e873]: R:R
                - generic [ref=e874]: "-"
              - generic [ref=e876]: Research
              - generic [ref=e884]: Conviction
          - button "Unknown trade unclassified · timeframe n/a open - Hold open R:R - Research Conviction" [ref=e892] [cursor=pointer]:
            - generic [ref=e893]:
              - generic [ref=e894]:
                - generic [ref=e895]:
                  - generic [ref=e896]: Unknown
                  - generic [ref=e897]: trade
                - generic [ref=e898]: unclassified · timeframe n/a
              - generic [ref=e899]:
                - generic [ref=e900]: open
                - generic [ref=e901]: "-"
            - generic [ref=e902]:
              - generic [ref=e903]:
                - generic [ref=e904]: Hold
                - generic [ref=e905]: open
              - generic [ref=e906]:
                - generic [ref=e907]: R:R
                - generic [ref=e908]: "-"
              - generic [ref=e910]: Research
              - generic [ref=e918]: Conviction
          - button "Unknown trade unclassified · timeframe n/a open - Hold open R:R - Research Conviction" [ref=e926] [cursor=pointer]:
            - generic [ref=e927]:
              - generic [ref=e928]:
                - generic [ref=e929]:
                  - generic [ref=e930]: Unknown
                  - generic [ref=e931]: trade
                - generic [ref=e932]: unclassified · timeframe n/a
              - generic [ref=e933]:
                - generic [ref=e934]: open
                - generic [ref=e935]: "-"
            - generic [ref=e936]:
              - generic [ref=e937]:
                - generic [ref=e938]: Hold
                - generic [ref=e939]: open
              - generic [ref=e940]:
                - generic [ref=e941]: R:R
                - generic [ref=e942]: "-"
              - generic [ref=e944]: Research
              - generic [ref=e952]: Conviction
```

# Test source

```ts
  1  | import type { Page } from "@playwright/test";
  2  | import { test, expect } from "../fixtures/copilot-fixture";
  3  | import { collectConsoleErrors, expectNoConsoleErrors } from "../helpers/ui";
  4  | 
  5  | function regimePanel(page: Page) {
  6  |   return page.locator("section", { has: page.getByRole("heading", { name: "Market Regime" }) }).first();
  7  | }
  8  | 
  9  | function detailPanel(page: Page) {
  10 |   return regimePanel(page).locator("div", { has: page.getByRole("heading", { name: "Detailed Recommendations" }) }).first();
  11 | }
  12 | 
  13 | test("Regime detail shows recommendations or unavailable state", async ({ page }) => {
  14 |   await page.goto("/");
  15 | 
  16 |   const detail = detailPanel(page);
  17 |   await expect(detail).toBeVisible({ timeout: 15_000 });
  18 |   await expect(
  19 |     detail
  20 |       .getByText(/Allocation context|Shift suggestion|No detailed regime recommendations available|Detailed regime recommendations unavailable/i)
  21 |       .first(),
  22 |   ).toBeVisible();
  23 | });
  24 | 
  25 | test("Regime detail shows regime-neutral context or summary", async ({ page }) => {
  26 |   await page.goto("/");
  27 | 
  28 |   const detail = detailPanel(page);
  29 |   await expect(detail).toBeVisible({ timeout: 15_000 });
  30 |   await expect(detail.getByText(/regime-neutral|regime-sensitive|avoid|reduce|increase|hold|Conservation not confirmed|Detailed regime recommendations unavailable|Allocation context/i).first()).toBeVisible();
  31 | });
  32 | 
  33 | test("Regime detail shows conservation status", async ({ page }) => {
  34 |   await page.goto("/");
  35 | 
  36 |   const detail = detailPanel(page);
  37 |   await expect(detail).toBeVisible({ timeout: 15_000 });
> 38 |   await expect(detail.getByText(/Conservation confirmed|Conservation not confirmed/i).first()).toBeVisible();
     |                                                                                                ^ Error: expect(locator).toBeVisible() failed
  39 | });
  40 | 
  41 | test("Regime detail avoids investment-advice wording", async ({ page }) => {
  42 |   await page.goto("/");
  43 | 
  44 |   const detail = detailPanel(page);
  45 |   await expect(detail).toBeVisible({ timeout: 15_000 });
  46 |   await expect(detail).not.toContainText(/you should buy|financial advice/i);
  47 | });
  48 | 
  49 | test("Regime detail has no console errors", async ({ page }) => {
  50 |   const errors = collectConsoleErrors(page);
  51 |   await page.goto("/");
  52 |   await expect(detailPanel(page)).toBeVisible({ timeout: 15_000 });
  53 | 
  54 |   expectNoConsoleErrors(errors);
  55 | });
  56 | 
  57 | 
```