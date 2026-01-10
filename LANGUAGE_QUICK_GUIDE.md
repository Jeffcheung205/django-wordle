# 繁體中文切換快速指南 / Quick Chinese Language Guide

## 快速測試 / Quick Test

### 1. 啟動伺服器 / Start Server
```bash
cd D:\django-wordle\christmax
poetry run python manage.py runserver
```

### 2. 訪問網站 / Visit Website
- **英文版 English**: http://127.0.0.1:8000/
- **中文版 Chinese**: http://127.0.0.1:8000/zh/

### 3. 切換語言 / Switch Language
在導航欄右上角點擊語言選擇器 / Click language selector in top-right navbar:
- Select "繁體中文" → Entire site switches to Chinese
- Select "English" → Entire site switches to English

## 主要頁面 / Main Pages

| Page | English URL | 中文 URL |
|------|-------------|---------|
| Home | `/` | `/zh/` |
| Membership Plans | `/membership/plans/` | `/zh/membership/plans/` |
| My Subscription | `/membership/my-subscription/` | `/zh/membership/my-subscription/` |
| Upgrade | `/membership/upgrade/` | `/zh/membership/upgrade/` |
| Login | `/accounts/login/` | `/zh/accounts/login/` |
| Sign Up | `/accounts/signup/` | `/zh/accounts/signup/` |
| Settings | `/settings/` | `/zh/settings/` |

## 語言檔案位置 / Translation Files

```
christmax/base/locale/zh/LC_MESSAGES/
├── app.po       ← 編輯此檔案新增翻譯 / Edit to add translations
├── app.mo       ← 編譯檔案 / Compiled file
├── allauth.po   ← Django-allauth 翻譯
├── allauth.mo
├── djangojs.po  ← JavaScript 翻譯
└── djangojs.mo
```

## 新增翻譯流程 / Adding Translations

### 1. 在範本中標記文字 / Mark Text in Templates
```django
{% load i18n %}
<h1>{% trans "Hello World" %}</h1>
```

### 2. 加入中文翻譯 / Add Chinese Translation
Edit `base/locale/zh/LC_MESSAGES/app.po`:
```po
msgid "Hello World"
msgstr "你好世界"
```

### 3. 編譯翻譯 / Compile Translations
```bash
poetry run python manage.py compile_mo
```

### 4. 重啟伺服器 / Restart Server
Ctrl+C, then:
```bash
poetry run python manage.py runserver
```

## 會員系統翻譯 / Membership Translations

| English | 繁體中文 |
|---------|---------|
| Membership Plans | 會員方案 |
| Free | 免費 |
| Premium | 高級會員 |
| My Subscription | 我的訂閱 |
| Upgrade Now | 立即升級 |
| Cancel Subscription | 取消訂閱 |
| Days Remaining | 剩餘天數 |
| Payment Method | 付款方式 |
| Unlimited quiz attempts | 無限測驗機會 |
| Progress tracking | 進度追蹤 |

## 故障排除 / Troubleshooting

### 翻譯沒有顯示 / Translations Not Showing
1. 確認已編譯 / Check compiled:
   ```bash
   poetry run python manage.py compile_mo
   ```
2. 重啟伺服器 / Restart server
3. 清除瀏覽器快取 / Clear browser cache
4. 確認 URL 有 `/zh/` 前綴 / Check URL has `/zh/` prefix

### 語言選擇器沒反應 / Language Selector Not Working
1. 檢查瀏覽器控制台錯誤 / Check browser console for errors
2. 確認 JavaScript 已載入 / Ensure JavaScript is loaded
3. 確認 LocaleMiddleware 在 settings.py 中 / Check LocaleMiddleware in settings

## 檔案編碼 / File Encoding
所有 `.po` 檔案使用 UTF-8 編碼 / All `.po` files use UTF-8 encoding

## 支援 / Support
- 文檔: `I18N_INTEGRATION_COMPLETE.md`
- 會員系統文檔: `docs/membership-system.md`
- Django i18n 文檔: https://docs.djangoproject.com/en/5.2/topics/i18n/

---

**✅ 系統已完全支援繁體中文！**
**✅ System fully supports Traditional Chinese!**
