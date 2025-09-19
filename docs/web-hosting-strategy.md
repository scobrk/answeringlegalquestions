# Web Hosting Strategy - Zero Cost Deployment

## **ORCHESTRATION AGENT: Deployment Architecture Update**

### **Web Accessibility Requirement**
- **Stakeholder Access**: Revenue NSW staff need web-based access
- **Demo Capability**: Public URL for presentations and testing
- **User Testing**: Real-world validation with actual users
- **Zero-Cost Constraint**: Must maintain free tier compliance

## **Free Hosting Platform Analysis**

### **Option 1: Railway (Recommended)**
- **Frontend**: Streamlit app deployment
- **Backend**: FastAPI service hosting
- **Database**: Supabase (already planned)
- **Cost**: $0 for 500 hours/month
- **Domain**: railway.app subdomain included
- **Pros**: Docker support, automatic deployments, environment variables
- **Cons**: 500-hour monthly limit

### **Option 2: Render**
- **Frontend**: Static site + Streamlit service
- **Backend**: FastAPI web service
- **Database**: Supabase (external)
- **Cost**: $0 for 750 hours/month
- **Domain**: render.com subdomain included
- **Pros**: More generous free tier, good Docker support
- **Cons**: Slower cold starts

### **Option 3: Streamlit Community Cloud**
- **Frontend**: Native Streamlit hosting
- **Backend**: Separate service (Railway/Render)
- **Database**: Supabase (external)
- **Cost**: $0 unlimited for public repos
- **Domain**: streamlit.app subdomain
- **Pros**: Purpose-built for Streamlit, unlimited usage
- **Cons**: Requires public GitHub repo

### **Option 4: Hybrid Approach (Best)**
- **Frontend**: Streamlit Community Cloud
- **Backend**: Railway or Render
- **RAGflow**: Railway container service
- **Database**: Supabase
- **Total Cost**: $0

## **Recommended Deployment Architecture**

### **Web-Accessible Stack**
```
User Browser → Streamlit Cloud → Railway Backend → Supabase Database
              (streamlit.app)   (railway.app)      (supabase.co)
                     ↓
               Railway RAGflow
               (ragflow.railway.app)
```

### **Service Distribution**
1. **Streamlit Frontend**: `revenue-nsw-assistant.streamlit.app`
2. **FastAPI Backend**: `revenue-nsw-api.up.railway.app`
3. **RAGflow Service**: `revenue-nsw-ragflow.up.railway.app`
4. **Supabase Database**: `your-project.supabase.co`

## **Implementation Updates Required**

### **1. GitHub Repository Setup**
- **Public Repository**: Required for Streamlit Community Cloud
- **Environment Management**: Secrets via platform settings
- **Deployment Branches**: main for production, dev for testing

### **2. Docker Configuration Updates**
- **Railway Dockerfile**: Optimized for cloud deployment
- **Environment Variables**: Platform-specific configuration
- **Health Checks**: Service monitoring endpoints

### **3. Domain & SSL**
- **Free Subdomains**: Provided by hosting platforms
- **Custom Domain**: Future upgrade option
- **SSL**: Automatic HTTPS on all platforms

### **4. CI/CD Pipeline**
- **Auto-Deployment**: Git push triggers deployment
- **Environment Promotion**: dev → staging → production
- **Rollback Capability**: Previous version restoration

## **Zero-Cost Compliance Strategy**

### **Resource Limits Management**
- **Railway**: 500 hours/month = ~16 hours/day (sufficient)
- **Streamlit Cloud**: Unlimited public usage
- **Supabase**: 1GB database, 500MB storage limit
- **Monitoring**: Track usage to prevent overages

### **Optimization Tactics**
- **Efficient Container**: Minimal Docker images
- **Sleep Mode**: Automatic scaling to zero during low usage
- **Connection Pooling**: Reduce database connections
- **Caching**: Reduce API calls and processing

## **Updated Timeline Impact**

### **Additional Tasks (0.5-1 day)**
- **Repository Setup**: Public GitHub with proper structure
- **Platform Configuration**: Railway + Streamlit Cloud setup
- **Environment Variables**: Secure secrets management
- **Domain Configuration**: Custom subdomain setup
- **Testing**: End-to-end web accessibility validation

### **Deployment Phases**
- **Phase 1**: Local development (current)
- **Phase 2**: Cloud staging deployment
- **Phase 3**: Production web access
- **Phase 4**: User acceptance testing

## **Security Considerations**

### **Public Access Controls**
- **No Authentication**: As designed for MVP
- **Rate Limiting**: Platform-level DDoS protection
- **Input Validation**: Prevent malicious queries
- **Data Privacy**: No PII storage in logs

### **Environment Security**
- **Secret Management**: Platform environment variables
- **API Key Protection**: Never exposed in frontend
- **Database Security**: Supabase RLS (Row Level Security)
- **HTTPS Only**: All communications encrypted

## **Monitoring & Maintenance**

### **Health Monitoring**
- **Uptime**: Platform-provided monitoring
- **Performance**: Response time tracking
- **Usage**: Resource consumption alerts
- **Error Tracking**: Application error logging

### **Maintenance Windows**
- **Deployments**: Zero-downtime rolling updates
- **Database**: Supabase managed maintenance
- **Platform Updates**: Automatic platform patching
- **Backup Strategy**: Supabase automatic backups

## **Success Metrics for Web Deployment**

### **Accessibility**
- **URL Access**: Public URL functional 24/7
- **Response Time**: <10 seconds for queries
- **Uptime**: >99% availability
- **Concurrent Users**: Support 10+ simultaneous users

### **Cost Compliance**
- **Monthly Cost**: $0 infrastructure
- **Usage Tracking**: Within all free tier limits
- **Scalability**: Ready to upgrade when needed
- **ROI**: Demonstrate value before infrastructure investment

## **Next Actions**
1. **Update KAN-2 Docker setup** for cloud deployment
2. **Create public GitHub repository** structure
3. **Configure Railway and Streamlit Cloud** accounts
4. **Update all Jira tasks** with web hosting requirements
5. **Test deployment pipeline** before KAN-4 implementation