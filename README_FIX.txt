HOTFIX for /admin/assets

Причина:
AssetService вызывал self.assets.list_assets(...),
но в репозитории существует метод list_all(...)

Что сделать:
1. заменить файл app/services/asset_service.py
2. git add .
3. git commit -m "fix admin assets list"
4. git push
5. redeploy
