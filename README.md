# 💪 LiftStash

**A powerful, self-hostable fitness companion for serious strength training enthusiasts**

>Note: This is heavily AI driven development, I just needed an application to suit my usecase. As such, your mileage may vary.

[![Docker](https://img.shields.io/badge/Docker-Ready-blue?logo=docker)](https://docker.com)
[![Mobile](https://img.shields.io/badge/Mobile-Optimized-green?logo=mobile)](https://github.com)
[![Dark Mode](https://img.shields.io/badge/Dark%20Mode-Supported-purple)](https://github.com)

---

## ✨ Why Choose LiftStash?

🏠 **Self-Hosted Privacy** - Your data stays on your server  
📱 **Mobile-First Design** - Perfect for gym use on any device  
🌙 **Dark Mode Ready** - Easy on the eyes during late workouts  
📊 **Smart Analytics** - Visual progress tracking with interactive charts  
🔄 **Split Tracking** - Advanced left/right limb tracking for unilateral exercises  

---

## 🚀 Key Features

### 💯 **Complete Workout Management**
- 🏋️ **Exercise Library** - Comprehensive database with custom exercises
- 📋 **Program Builder** - Create structured workout routines
- ⏱️ **Live Workout Tracking** - Real-time set/rep/weight logging
- 🏆 **Personal Records** - Automatic PR detection and tracking

### 📈 **Advanced Analytics**
- 📊 **Progress Charts** - Visual strength progression over time
- 🎯 **Multi-Exercise Comparison** - Compare performance across exercises
- 📅 **Historical Data** - Complete workout history with filtering

### 🔧 **Smart Features**
- ⚖️ **Assisted Exercise Support** - Track decreasing weight as improvement
- 🤲 **Split Limb Tracking** - Perfect for single-arm/leg exercises
- ✏️ **Full CRUD Operations** - Edit/delete any workout data
- 🌓 **Dark/Light Themes** - Comfortable viewing in any environment

### 📱 **Mobile Excellence**
- 📲 **Touch-Optimized UI** - Large buttons and inputs for gym use
- 🍔 **Hamburger Navigation** - Clean, accessible mobile interface
- 📐 **Responsive Design** - Seamless experience on all screen sizes

---

## 🏃‍♂️ Quick Start

### 🐳 Docker Compose (Recommended)

```bash
# Clone and launch in seconds
git clone <repo-url>
cd liftstash
docker-compose up -d
```

**🌐 Access at:** http://localhost

### 🔧 Manual Installation

```bash
# Install and run
pip install -r requirements.txt
python app.py
```

### 🐋 Docker Build

```bash
# Custom deployment
docker build -t liftstash .
docker run -p 80:80 -v $(pwd)/data:/app/data liftstash
```

---

## ⚙️ Production Configuration

### 🔐 Security Settings
```bash
# Essential environment variables
SECRET_KEY=your-super-secure-secret-key-here
DATABASE=/app/data/workout_tracker.db
```

### 🏗️ Architecture
- **🌐 Nginx** - Production web server with static file caching
- **🦄 Gunicorn** - High-performance WSGI server
- **📊 Supervisor** - Process management and auto-restart
- **🗄️ SQLite** - Lightweight, portable database

---

## 📖 Getting Started Guide

1. **👤 Create Account** - Secure user registration
2. **🏋️ Build Exercise Library** - Add your favorite exercises
3. **📋 Design Programs** - Structure your training routines
4. **💪 Track Workouts** - Log sets, reps, and weights in real-time
5. **📈 Monitor Progress** - Watch your strength gains over time

---

## 🛠️ Tech Stack

- **Backend:** Python Flask + Gunicorn
- **Frontend:** Vanilla JS + Responsive CSS
- **Database:** SQLite (portable & reliable)
- **Deployment:** Docker + Nginx + Supervisor
- **Charts:** Chart.js for beautiful visualizations

---

## 📄 License

**Open Source** - MIT License  
Feel free to modify, distribute, and make it your own!

---

*Built with ❤️ for the fitness community*