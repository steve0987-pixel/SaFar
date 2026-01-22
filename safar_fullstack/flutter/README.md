# Safar Samarkand - Flutter Travel App

A beautiful travel guide app for Samarkand with AI advisor and manual trip planning features.

## Features

✨ **AI Travel Advisor** - Chat with an AI to create personalized itineraries
📝 **Manual Planning** - Step-by-step trip customization
🏛️ **Historical Places** - Browse UNESCO World Heritage sites
🍽️ **Restaurants** - Discover local Uzbek cuisine
🏨 **Hotels** - Find accommodation for every budget

## Project Structure

```
lib/
├── main.dart                           # App entry point
├── models/                             # Data models
│   ├── historical_place.dart
│   ├── hotel.dart
│   ├── restaurant.dart
│   └── chat_message.dart
├── data/
│   └── samarkand_data.dart            # Static data
├── screens/                            # App screens
│   ├── home_screen.dart
│   ├── places_screen.dart
│   ├── food_screen.dart
│   ├── hotels_screen.dart
│   ├── ai_advisor_screen.dart
│   ├── manual_preferences_screen.dart
│   └── results_screen.dart
├── widgets/                            # Reusable widgets
│   └── bottom_navigation.dart
└── utils/
    └── colors.dart                     # Color constants
```

## Getting Started

### Prerequisites
- Flutter SDK (3.0.0 or higher)
- Dart SDK
- Android Studio / VS Code with Flutter plugins

### Installation

1. Clone or download the project
2. Navigate to the project directory:
   ```bash
   cd safar_samarkand
   ```

3. Get dependencies:
   ```bash
   flutter pub get
   ```

4. Run the app:
   ```bash
   flutter run
   ```

## Screens

### Home Screen
- Hero section with Samarkand imagery
- Two main CTAs: AI Advisor and Manual Planning
- Quick facts about Samarkand
- Bottom navigation

### AI Advisor Screen
- Chat interface with typing indicators
- Conversational trip planning
- Real-time message updates

### Manual Planning Screen
- 5-step preference collection
- Progress indicator
- Interactive sliders and chips
- Smooth transitions

### Places/Food/Hotels Screens
- Browse attractions, restaurants, and hotels
- Filter and sort options
- Detailed information cards

### Results Screen
- AI-generated day-by-day itinerary
- Budget breakdown
- Pro tips for travelers
- Save and share options

## Customization

### Colors
Edit `lib/utils/colors.dart` to change the app's color scheme.

### Data
Add or modify places, hotels, and restaurants in `lib/data/samarkand_data.dart`.

## License

This project is open source and available for personal and commercial use.

## Author

Created with ❤️ for travelers exploring Samarkand
