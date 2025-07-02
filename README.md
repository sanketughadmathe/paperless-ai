# Paperless AI

An intelligent document management system powered by AI for seamless document processing and organization.

## 🚀 Project Overview

Paperless AI is designed to revolutionize document management by leveraging artificial intelligence to automatically organize, categorize, and make documents searchable. The system provides intelligent document processing capabilities with a modern web interface.

## 🏗️ Project Structure

```
paperless-ai/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── core/           # Core configurations
│   │   └── main.py         # Application entry point
│   ├── requirements.txt    # Python dependencies
│   └── .gitignore
├── frontend/               # React frontend (to be added)
├── docs/                   # Documentation
└── README.md
```

## 🛠️ Technology Stack

### Backend
- **FastAPI** - Modern Python web framework
- **Supabase** - Backend as a Service (Database & Auth)
- **Python 3.9+** - Programming language

### Frontend (Planned)
- **React** - UI framework
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first CSS framework

## 🔧 Installation & Setup

### Prerequisites
- Python 3.9+
- Node.js 16+ (for frontend)
- Git

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Environment Variables
Create a `.env` file in the backend directory:
```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
SECRET_KEY=your_secret_key
```

### Running the Application
```bash
cd backend
uvicorn app.main:app --reload
```

## 🌟 Features

- [ ] Document upload and storage
- [ ] AI-powered document categorization
- [ ] Intelligent search functionality
- [ ] User authentication and authorization
- [ ] Document preview and management
- [ ] API for document operations

## 🔄 Development Workflow

### Branch Strategy
- **main** - Production-ready code
- **dev** - Development integration branch
- **prod** - Production deployment branch
- **feature/** - Feature development branches
- **bugfix/** - Bug fix branches
- **hotfix/** - Critical production fixes

### Contributing
1. Create feature branch from `dev`
2. Make your changes
3. Submit pull request to `dev`
4. After review, changes are merged

## 🔐 Branch Protection

Both `main` and `dev` branches are protected with:
- Required pull request reviews (1 reviewer)
- No direct pushes allowed
- No force pushes or deletions

## 📝 API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🚀 Deployment

- **Development**: Deploy from `dev` branch
- **Production**: Deploy from `main` branch via `prod` branch

## 📄 License

This project is licensed under the MIT License.

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines and submit pull requests to the `dev` branch.

## 📞 Contact

For questions or support, please create an issue in this repository.
