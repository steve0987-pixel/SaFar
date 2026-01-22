# Safar Samarkand - Full Stack Travel App 🌍

Complete travel guide application with Flutter frontend and Node.js backend.

## 📦 Project Structure

```
safar_fullstack/
├── backend/                    # Node.js + Express + MongoDB
│   ├── models/                # Database models
│   ├── routes/                # API endpoints
│   ├── seeders/               # Database seeder
│   ├── server.js              # Main server file
│   ├── package.json           # Backend dependencies
│   └── .env.example           # Environment variables template
│
└── flutter/                   # Flutter mobile app
    ├── lib/
    │   ├── models/           # Data models
    │   ├── screens/          # UI screens
    │   ├── services/         # API service
    │   ├── utils/            # Utilities
    │   └── widgets/          # Reusable widgets
    └── pubspec.yaml          # Flutter dependencies
```

## 🚀 Backend Setup

### Prerequisites
- Node.js (v16 or higher)
- MongoDB (v5 or higher)
- npm or yarn

### Installation Steps

1. **Navigate to backend directory:**
```bash
cd backend
```

2. **Install dependencies:**
```bash
npm install
```

3. **Setup environment variables:**
```bash
cp .env.example .env
```

Edit `.env` file:
```env
PORT=3000
MONGODB_URI=mongodb://localhost:27017/safar_samarkand
JWT_SECRET=your_secret_key_here
```

4. **Start MongoDB:**

**macOS (with Homebrew):**
```bash
brew services start mongodb-community
```

**Linux:**
```bash
sudo systemctl start mongod
```

**Windows:**
```bash
net start MongoDB
```

**Or use MongoDB Atlas (cloud):**
- Create account at https://www.mongodb.com/cloud/atlas
- Create cluster and get connection string
- Update MONGODB_URI in .env

5. **Seed the database:**
```bash
npm run seed
```

6. **Start the server:**
```bash
# Development mode (with auto-reload)
npm run dev

# Production mode
npm start
```

Server will run at: `http://localhost:3000`

### Test Backend API

```bash
# Health check
curl http://localhost:3000/api/health

# Get all places
curl http://localhost:3000/api/places

# Get all hotels
curl http://localhost:3000/api/hotels

# Get all restaurants
curl http://localhost:3000/api/restaurants
```

## 📱 Flutter Setup

### Prerequisites
- Flutter SDK (3.0 or higher)
- Dart SDK
- Android Studio / Xcode
- Android Emulator or iOS Simulator

### Installation Steps

1. **Navigate to flutter directory:**
```bash
cd flutter
```

2. **Install dependencies:**
```bash
flutter pub get
```

3. **Configure API endpoint:**

Open `lib/services/api_service.dart` and update the baseUrl:

**For Android Emulator:**
```dart
static const String baseUrl = 'http://10.0.2.2:3000/api';
```

**For iOS Simulator:**
```dart
static const String baseUrl = 'http://localhost:3000/api';
```

**For Physical Device (same network):**
```dart
static const String baseUrl = 'http://YOUR_COMPUTER_IP:3000/api';
// Example: 'http://192.168.1.100:3000/api'
```

**To find your computer's IP:**
- macOS/Linux: `ifconfig | grep inet`
- Windows: `ipconfig`

4. **Run the app:**

```bash
# Check connected devices
flutter devices

# Run on specific device
flutter run

# Run on Android
flutter run -d android

# Run on iOS
flutter run -d ios
```

## 🔧 Configuration

### Backend API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/places` | Get all historical places |
| GET | `/api/hotels` | Get all hotels (with filters) |
| GET | `/api/restaurants` | Get all restaurants |
| POST | `/api/itineraries` | Create trip itinerary |
| GET | `/api/itineraries?userId=X` | Get user itineraries |
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | Login user |
| GET | `/api/auth/me` | Get current user |

### Query Parameters

**Hotels:**
```
GET /api/hotels?minPrice=50&maxPrice=150&stars=4
```

**Restaurants:**
```
GET /api/restaurants?type=Traditional
```

## 🧪 Testing

### Test Backend Endpoints

```bash
# Register user
curl -X POST http://localhost:3000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Test User","email":"test@example.com","password":"password123"}'

# Login
curl -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'

# Create itinerary
curl -X POST http://localhost:3000/api/itineraries \
  -H "Content-Type: application/json" \
  -d '{"days":5,"budget":100,"interests":["History","Food"]}'
```

## 📊 Database Schema

### Places Collection
```javascript
{
  name: String,
  description: String,
  rating: Number,
  cost: String,
  time: String,
  imageUrl: String,
  category: String,
  location: { latitude: Number, longitude: Number }
}
```

### Hotels Collection
```javascript
{
  name: String,
  stars: Number (1-5),
  price: Number,
  description: String,
  rating: Number,
  amenities: [String],
  imageUrl: String,
  location: { latitude: Number, longitude: Number }
}
```

### Restaurants Collection
```javascript
{
  name: String,
  type: String,
  rating: Number,
  priceRange: String,
  specialty: String,
  emoji: String,
  location: { latitude: Number, longitude: Number }
}
```

### Itineraries Collection
```javascript
{
  userId: ObjectId,
  title: String,
  days: Number,
  budget: Number,
  interests: [String],
  travelStyle: String,
  activityLevel: String,
  dailyPlans: [{
    day: Number,
    title: String,
    activities: [String],
    estimatedCost: Number
  }],
  totalCost: Number
}
```

## 🐛 Troubleshooting

### Backend Issues

**MongoDB connection failed:**
```bash
# Check if MongoDB is running
mongosh

# Start MongoDB
brew services start mongodb-community  # macOS
sudo systemctl start mongod            # Linux
```

**Port already in use:**
```bash
# Find process using port 3000
lsof -i :3000  # macOS/Linux
netstat -ano | findstr :3000  # Windows

# Kill the process
kill -9 <PID>
```

### Flutter Issues

**Cannot connect to backend:**
1. Ensure backend is running (`npm run dev`)
2. Check API URL in `api_service.dart`
3. For Android emulator, use `10.0.2.2` instead of `localhost`
4. Disable firewall temporarily to test
5. Make sure phone and computer are on same WiFi

**Packages not found:**
```bash
flutter pub get
flutter clean
flutter pub get
```

**Build errors:**
```bash
flutter clean
rm -rf pubspec.lock
flutter pub get
```

## 🔒 Security Notes

**For Production:**

1. Change JWT_SECRET in .env
2. Enable authentication middleware on protected routes
3. Add rate limiting
4. Use HTTPS
5. Validate all inputs
6. Use environment variables for sensitive data
7. Enable CORS only for your frontend domain
8. Use MongoDB Atlas with IP whitelist

## 📱 Features

✅ Browse historical places, hotels, and restaurants
✅ AI-powered trip advisor (chat interface)
✅ Manual trip planning (step-by-step)
✅ Generate personalized itineraries
✅ Save and view trip plans
✅ User authentication (register/login)
✅ Responsive design (mobile, tablet, desktop)
✅ Real-time data from backend API

## 🚀 Deployment

### Backend Deployment (Heroku/Railway/Render)

1. Create account on platform
2. Create new app/service
3. Connect GitHub repository
4. Set environment variables
5. Deploy

### Frontend Deployment

**Android:**
```bash
flutter build apk --release
# APK located at: build/app/outputs/flutter-apk/app-release.apk
```

**iOS:**
```bash
flutter build ios --release
# Then open Xcode and archive
```

## 📄 License

MIT License - Feel free to use for personal and commercial projects!

## 🤝 Support

For issues or questions:
1. Check troubleshooting section
2. Review error logs
3. Check API endpoint connectivity

---

Made with ❤️ for travelers exploring Samarkand 🇺🇿
