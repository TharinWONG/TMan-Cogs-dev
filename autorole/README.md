
注意事項
1. 在主機上把檔案放好： cogs/autorole/autorole.py、__init__.py、info.json。
2. 在 Discord 裡用 Red 的管理前綴執行： [p]load autorole（或在 console 執行 load autorole）。
3. 設定示例：
   - [p]autorole set @RoleName  （用 role mention 或 ID）
   - [p]autorole enable
   - [p]autorole delay 10
   - [p]autorole dm 歡迎加入 {guild}，{mention}！
   - [p]autorole test @SomeUser
   - [p]autorole show

注意事項與建議
- Bot 必須開啟 members intent（Red 一般有啟用，但 host 端與 Discord Developer Portal 需要設定 intents.members=True）。
- Bot 需要 Manage Roles 權限，且 bot 的最高角色要高於欲指派的角色。
- 我把 info.json 的 requirements 留空，因為 Red 已提供 discord API。原專案 pyproject 裡的 python-dotenv / discord.py 是 standalone bot 的依賴，改成 Red cog 後通常唔需要。
- 若你原本係用原專案的 .env（DISCORD_GUILD_ID、DISCORD_ROLE_ID/NAME）並想把單一 guild 的設定自動遷移到 Red：可手動在 Red 執行 [p]autorole set / [p]autorole setname 並 [p]autorole enable，或者我可以加一個簡單的「從 .env 匯入」功能（需要你提供 .env 內容或放到 Red 主機上讓 cog 讀取），要我做就講。


指令清單與範例
- [p]autorole set <role>
  - 功能：設定要自動指派的身分組。
  - 範例：[p]autorole set @NewMemberRole
  - 也可用角色 ID： [p]autorole set 123456789012345678

- [p]autorole enable
  - 功能：啟用自動指派。
  - 範例：[p]autorole enable

- [p]autorole disable
  - 功能：停用自動指派。
  - 範例：[p]autorole disable

- [p]autorole delay <seconds>
  - 功能：設定加入後等待多少秒才指派（整數，預設 0）。
  - 範例：[p]autorole delay 30  （加入後等 30 秒再指派）

- [p]autorole dm <message>
  - 功能：在成功指派後發送私訊給新成員（可留空清除）。
  - 支援佔位符：{guild}（伺服器名）、{member}（成員名）。
  - 範例：[p]autorole dm 歡迎加入 {guild}，{member}！已自動給你身分組。
  - 清除私訊： [p]autorole dm

- [p]autorole show
  - 功能：顯示目前伺服器的 autorole 設定（是否啟用、設定的身分組、延遲、DM 內容）。
  - 範例：[p]autorole show

- [p]autorole test [member]
  - 功能：測試指派（會臨時給予並移除目標身分組以驗證權限）；可指定成員，不指定則測試執行者自己。
  - 範例：[p]autorole test @SomeUser
  - 範例（不指定）：[p]autorole test

其他小提示
- 若 bot 沒有 Manage Roles 或者 bot 的最高角色低於目標角色，指派會失敗／被拒絕；使用 [p]autorole test 可以先驗證。
- 想看說明可以用 [p]help autorole（或 [p]help autorole set 等子指令）。
- 若你未 load cog：在 Red console 或 bot 管理界面用 load/咩前綴（例如 [p]load autorole）去載入。
