# Vercel Environment Variables Setup

## Backend Environment Variables

Go to your Vercel project dashboard: https://vercel.com/avatars2s-projects/plant-disease-detecations-q6x1

1. Click on **Settings** tab
2. Click on **Environment Variables**
3. Add the following variables:

### Required Variables:
```
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/plant_disease?retryWrites=true&w=majority
JWT_SECRET_KEY=your-super-secret-jwt-key-here
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216
```

### Optional Variables:
```
MODEL_API_URL=https://your-model-api.com/predict
MODEL_URL=https://your-model-storage.com/model.h5
```

## Frontend Environment Variables

The frontend automatically uses the current domain for API calls, so no additional frontend environment variables are needed.

## Notes:

1. **MongoDB Atlas Setup**:
   - Create a free MongoDB Atlas account
   - Create a cluster
   - Get your connection string
   - Add your IP to the whitelist (0.0.0.0/0 for Vercel)

2. **JWT Secret**:
   - Generate a secure random string
   - Use: `openssl rand -base64 32` or visit https://randomkeygen.com/

3. **Model API** (Optional):
   - If you want real ML predictions instead of mock data
   - Deploy your model as a separate API service
   - Add the URL to MODEL_API_URL

4. **After adding variables**:
   - Redeploy your Vercel project
   - Go to the **Deployments** tab
   - Click the latest deployment and choose **Redeploy**

## Testing:

Once deployed, test:
- Frontend: https://plant-disease-detecations-q6x1.vercel.app/
- API Health: https://plant-disease-detecations-q6x1.vercel.app/api/health
- API Classes: https://plant-disease-detecations-q6x1.vercel.app/api/predict/classes
