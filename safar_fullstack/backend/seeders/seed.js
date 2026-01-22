// seeders/seed.js
require('dotenv').config();
const mongoose = require('mongoose');
const Place = require('../models/Place');
const Hotel = require('../models/Hotel');
const Restaurant = require('../models/Restaurant');

const places = [
  {
    name: 'Registan Square',
    description: 'Three magnificent madrasas',
    rating: 4.9,
    cost: '10-15',
    time: '2-3 hours',
    imageUrl: 'https://images.unsplash.com/photo-1496442226666-8d4d0e62e6e9?w=400',
    category: 'historical',
  },
  {
    name: 'Gur-Emir Mausoleum',
    description: 'Tomb of Timur',
    rating: 4.8,
    cost: '5-8',
    time: '1 hour',
    imageUrl: 'https://images.unsplash.com/photo-1518156677180-95a2893f3e9f?w=400',
    category: 'historical',
  },
  {
    name: 'Shah-i-Zinda Necropolis',
    description: 'Avenue of the tombs',
    rating: 4.9,
    cost: '8-10',
    time: '1.5-2 hours',
    imageUrl: 'https://images.unsplash.com/photo-1570129477492-45af003fc337?w=400',
    category: 'historical',
  },
  {
    name: 'Bibi-Khanym Mosque',
    description: 'Grand Friday mosque',
    rating: 4.7,
    cost: '5-8',
    time: '1 hour',
    imageUrl: 'https://images.unsplash.com/photo-1486182143521-c89f41dc025d?w=400',
    category: 'historical',
  },
  {
    name: 'Ulugbek Observatory',
    description: 'Ancient astronomical observatory',
    rating: 4.6,
    cost: '3-5',
    time: '45 min',
    imageUrl: 'https://images.unsplash.com/photo-1576169239e0-07cd6bfbe272?w=400',
    category: 'historical',
  },
];

const hotels = [
  {
    name: 'Registan Palace Hotel',
    stars: 5,
    price: 150,
    description: 'Luxury 5-star with Registan view',
    rating: 4.9,
    amenities: ['Wi-Fi', 'Restaurant', 'Spa', 'Gym', 'Parking'],
  },
  {
    name: 'Dilshod Hotel',
    stars: 4,
    price: 80,
    description: 'Boutique hotel in old city',
    rating: 4.7,
    amenities: ['Wi-Fi', 'Restaurant', 'Courtyard', 'Parking'],
  },
  {
    name: 'Afrosiab Hotel',
    stars: 4,
    price: 75,
    description: 'Modern hotel near attractions',
    rating: 4.6,
    amenities: ['Wi-Fi', 'Restaurant', 'Pool', 'Gym'],
  },
  {
    name: 'Jahongir Hotel',
    stars: 3,
    price: 45,
    description: 'Budget-friendly guesthouse',
    rating: 4.4,
    amenities: ['Wi-Fi', 'Breakfast', 'Courtyard'],
  },
  {
    name: 'Samarkand Boutique Hotel',
    stars: 4,
    price: 95,
    description: 'Traditional Uzbek design',
    rating: 4.8,
    amenities: ['Wi-Fi', 'Restaurant', 'Terrace', 'Parking'],
  },
];

const restaurants = [
  {
    name: 'Plov Center',
    type: 'Traditional Uzbek',
    rating: 4.9,
    priceRange: '5-10',
    specialty: 'Famous plov',
    emoji: '🍲',
  },
  {
    name: 'Mirza Restaurant',
    type: 'Fine Dining',
    rating: 4.8,
    priceRange: '15-25',
    specialty: 'Kebabs & steaks',
    emoji: '🥩',
  },
  {
    name: 'Samarkand Sarai',
    type: 'Uzbek Cuisine',
    rating: 4.7,
    priceRange: '8-15',
    specialty: 'Lagman & manti',
    emoji: '🍜',
  },
  {
    name: 'Chorsu Bazaar Food',
    type: 'Street Food',
    rating: 4.6,
    priceRange: '2-5',
    specialty: 'Samosas & bread',
    emoji: '🥐',
  },
  {
    name: 'Shashlyk House',
    type: 'BBQ',
    rating: 4.7,
    priceRange: '10-20',
    specialty: 'Grilled meats',
    emoji: '🍗',
  },
  {
    name: 'Tea House Samarkand',
    type: 'Cafe',
    rating: 4.5,
    priceRange: '3-8',
    specialty: 'Green tea & snacks',
    emoji: '🫖',
  },
];

async function seedDatabase() {
  try {
    // Connect to MongoDB
    await mongoose.connect(
      process.env.MONGODB_URI || 'mongodb://localhost:27017/safar_samarkand',
      {
        useNewUrlParser: true,
        useUnifiedTopology: true,
      }
    );

    console.log('✅ Connected to MongoDB');

    // Clear existing data
    await Place.deleteMany({});
    await Hotel.deleteMany({});
    await Restaurant.deleteMany({});
    console.log('🗑️  Cleared existing data');

    // Insert new data
    await Place.insertMany(places);
    console.log(`✅ Inserted ${places.length} places`);

    await Hotel.insertMany(hotels);
    console.log(`✅ Inserted ${hotels.length} hotels`);

    await Restaurant.insertMany(restaurants);
    console.log(`✅ Inserted ${restaurants.length} restaurants`);

    console.log('🎉 Database seeded successfully!');
    process.exit(0);
  } catch (error) {
    console.error('❌ Error seeding database:', error);
    process.exit(1);
  }
}

seedDatabase();
