# Railway Deployment Instructions

## Option 1: Deploy FastAPI Backend Only (Connect to External ChromaDB)

1. **Sign up or login to Railway**:
   - Visit [Railway.app](https://railway.app) and create an account or login

2. **Install Railway CLI** (optional but recommended):
   ```bash
   npm i -g @railway/cli
   railway login
   ```

3. **Create a new Railway project**:
   - In the Railway dashboard, click "New Project"
   - Select "Deploy from GitHub"
   - Connect your GitHub account and select your repository

4. **Set Environment Variables**:
   - Go to the "Variables" tab
   - Add the variables from `railway.env.example`
   - Make sure to set the correct `CHROMA_HOST` to your hosted ChromaDB instance

5. **Deploy your project**:
   - Railway will automatically detect your Procfile and requirements
   - Your project will be deployed
   - You can find your project URL in the "Settings" tab

## Option 2: Deploy Both FastAPI Backend and ChromaDB

1. **Create a new Railway project**

2. **Add two services**:
   - First service: Your FastAPI backend
   - Second service: ChromaDB

   ### For Your FastAPI Backend:
   - Follow the steps from Option 1

   ### For ChromaDB Service:
   - Click "New Service" > "Empty Service"
   - Set the following environment variables:
     ```
     PORT=8000
     ```
   - In the "Settings" tab, set the service command to:
     ```
     pip install chromadb && chroma run --host 0.0.0.0 --port $PORT
     ```
   - Link your ChromaDB service to your FastAPI backend by setting:
     ```
     CHROMA_HOST=your_chromadb_service_name
     ```

3. **Configure Networking**:
   - In your project settings, create a private network between the services
   - This allows the services to communicate using their service names

## Additional Tips

1. **Persistent Storage**:
   - Railway provides persistent disk for your services
   - For ChromaDB, configure persistent volume in service settings

2. **Updating Your Deployment**:
   - Any changes pushed to your connected GitHub repository will trigger a redeployment

3. **Monitoring**:
   - Use the "Metrics" tab to monitor your service performance
   - Check logs under the "Logs" tab for debugging

4. **Custom Domains**:
   - In the "Settings" tab, you can set up a custom domain for your API

5. **Scaling**:
   - Adjust service resources in the "Settings" tab as your needs grow 