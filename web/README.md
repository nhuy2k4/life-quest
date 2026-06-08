# LifeQuest Admin Web

React + Vite admin web for LifeQuest.

## Local development

```bash
npm install
npm run dev
```

The local `.env` can use the Vite proxy:

```env
VITE_API_URL=/api/v1
```

## Deploy to Vercel with Render backend

Use `web` as the Vercel project root.

Vercel settings:

- Framework Preset: `Vite`
- Build Command: `npm run build`
- Output Directory: `dist`
- Install Command: `npm install`

Environment Variables on Vercel:

```env
VITE_API_URL=https://life-quest-fxy1.onrender.com/api/v1
```

After Vercel creates the frontend URL, add it to the backend service on Render:

```env
CORS_ORIGINS=["https://life-quest-gf7wj8c1c-huys-projects-672b143e.vercel.app"]
```

If you have a custom domain, include it too:

```env
CORS_ORIGINS=["https://your-vercel-app.vercel.app","https://your-domain.com"]
```
