# Deployment Guide

## Deployment Options

### Option 1: Local Development

**Quick Start:**
```bash
# Backend
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Frontend (new terminal)
cd frontend
npm run dev -- --host 0.0.0.0 --port 5173
```

Access:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

### Option 2: Docker Compose (Recommended for Production)

**Prerequisites:**
- Docker installed
- Docker Compose installed

**Deploy:**
```bash
# Build and start all services
docker-compose up --build

# Or in detached mode
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

**Access:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000

**Production Configuration:**
Edit `docker-compose.yml` to:
- Change environment variables
- Add database (PostgreSQL)
- Add caching (Redis)
- Configure volumes for persistence

---

### Option 3: Cloud Deployment

#### A. **Backend on Heroku/Render**

**Heroku:**
```bash
# Install Heroku CLI
brew install heroku/brew/heroku  # macOS

# Login and create app
heroku login
heroku create akriti-backend

# Deploy
git push heroku main

# Set environment variables
heroku config:set PYTHONUNBUFFERED=1
```

**Render:**
1. Connect GitHub repo
2. Create new Web Service
3. Set:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`

#### B. **Frontend on Vercel/Netlify**

**Vercel:**
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy from frontend directory
cd frontend
vercel
```

**Netlify:**
1. Connect GitHub repo
2. Set build settings:
   - Base directory: `frontend`
   - Build command: `npm run build`
   - Publish directory: `frontend/dist`

#### C. **Complete Stack on AWS**

**Architecture:**
```
User → CloudFront → S3 (Frontend)
                  ↓
                  ELB → EC2/ECS (Backend)
                        ↓
                        RDS (Database)
```

**Steps:**
1. **Frontend on S3 + CloudFront:**
   ```bash
   cd frontend
   npm run build
   aws s3 sync dist/ s3://akriti-frontend/
   ```

2. **Backend on EC2/ECS:**
   - Create EC2 instance
   - Install Docker
   - Clone repo and run backend
   - Or use ECS for container orchestration

3. **Database (Optional):**
   - Create RDS PostgreSQL instance
   - Update backend connection string

---

### Option 4: GPU-Enabled Deployment (for Model Inference)

If using the trained model in production, you need GPU:

#### RunPod Deployment
```bash
# 1. Create RunPod instance with GPU
# 2. Upload code and model
scp -r . runpod:/workspace/

# 3. Run on RunPod
docker run -p 8000:8000 \
  --gpus all \
  -v /workspace/checkpoints:/app/checkpoints \
  akriti-backend
```

#### AWS EC2 with GPU (p3.2xlarge)
```bash
# 1. Launch GPU instance
# 2. Install CUDA and Docker
# 3. Deploy with GPU support
docker run --gpus all -p 8000:8000 akriti-backend
```

---

## Environment Variables

Create `.env` file:

```bash
# Backend
MODEL_PATH=/app/checkpoints/codet5-floorplan-v1/final_model
MAX_WORKERS=4
LOG_LEVEL=info

# Database (if using)
DATABASE_URL=postgresql://user:password@localhost:5432/akriti

# Redis (if using)
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=your-secret-key-here
ALLOWED_ORIGINS=https://your-frontend.com
```

---

## Production Checklist

### Security
- [ ] Change default passwords
- [ ] Enable HTTPS (use Let's Encrypt)
- [ ] Set CORS origins to specific domains
- [ ] Add rate limiting
- [ ] Enable API key authentication
- [ ] Sanitize user inputs
- [ ] Keep dependencies updated

### Performance
- [ ] Enable gzip compression
- [ ] Use CDN for frontend assets
- [ ] Cache API responses (Redis)
- [ ] Optimize SVG generation
- [ ] Use connection pooling for database
- [ ] Enable logging and monitoring

### Monitoring
- [ ] Set up error tracking (Sentry)
- [ ] Enable logging (CloudWatch/Datadog)
- [ ] Monitor API performance
- [ ] Set up health checks
- [ ] Configure alerts

### Backup
- [ ] Regular database backups
- [ ] Backup model checkpoints
- [ ] Backup user data
- [ ] Test restore procedures

---

## Scaling

### Horizontal Scaling

**Backend:**
```yaml
# docker-compose.yml
backend:
  image: akriti-backend
  deploy:
    replicas: 3  # Run 3 instances
  ports:
    - "8000-8002:8000"
```

**Load Balancer:**
- Use Nginx/HAProxy for load balancing
- Or use cloud load balancers (AWS ELB, Google Cloud LB)

### Vertical Scaling

If generation is slow:
- Increase CPU/RAM for backend instances
- Use GPU instances for model inference
- Optimize model (quantization, pruning)

---

## Monitoring & Logging

### Application Monitoring

**Prometheus + Grafana:**
```bash
# Add to docker-compose.yml
prometheus:
  image: prom/prometheus
  volumes:
    - ./prometheus.yml:/etc/prometheus/prometheus.yml

grafana:
  image: grafana/grafana
  ports:
    - "3000:3000"
```

### Log Aggregation

**ELK Stack (Elasticsearch, Logstash, Kibana):**
- Collect logs from all services
- Search and analyze
- Create dashboards

---

## Troubleshooting

### Backend not starting
```bash
# Check logs
docker-compose logs backend

# Check dependencies
pip list

# Test manually
cd backend
python -c "import fastapi, torch, transformers"
```

### Frontend build fails
```bash
# Clear cache
rm -rf node_modules package-lock.json
npm install

# Check Node version
node --version  # Should be 18+
```

### Model not loading
```bash
# Check model path
ls checkpoints/codet5-floorplan-v1/final_model/

# Check GPU availability
python -c "import torch; print(torch.cuda.is_available())"
```

---

## Cost Estimation

### Development (Local)
- **Cost:** $0 (use your computer)
- **Limitations:** No public access

### Small Deployment
- **Frontend:** Vercel/Netlify (Free tier)
- **Backend:** Heroku/Render ($5-10/month)
- **Database:** PostgreSQL free tier
- **Total:** ~$5-10/month

### Medium Deployment
- **Frontend:** AWS S3 + CloudFront ($1-5/month)
- **Backend:** AWS EC2 t3.medium ($30/month)
- **Database:** RDS db.t3.micro ($15/month)
- **Total:** ~$50/month

### Production with GPU
- **Frontend:** Same as medium
- **Backend:** AWS p3.2xlarge ($3/hour when running)
- **Database:** RDS with backups ($50/month)
- **Total:** ~$200-500/month (depending on usage)

---

## Next Steps After Deployment

1. **Test in production:**
   - Generate multiple floor plans
   - Test different input types
   - Verify export functionality

2. **Monitor performance:**
   - Track API response times
   - Monitor error rates
   - Check resource usage

3. **Gather feedback:**
   - User testing
   - Bug reports
   - Feature requests

4. **Iterate and improve:**
   - Fix issues
   - Add features
   - Optimize performance

---

## Support & Maintenance

### Regular Tasks
- Weekly: Check logs, monitor errors
- Monthly: Update dependencies
- Quarterly: Backup verification, security audit
- Yearly: Model retraining with new data

### Emergency Procedures
1. If API goes down → Check health endpoint
2. If slow response → Check resource usage
3. If errors spike → Check recent deployments
4. If data loss → Restore from backup

---

**Deployment complete! Your floor plan generator is now live! 🚀**

