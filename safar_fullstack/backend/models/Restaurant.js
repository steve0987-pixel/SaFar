// models/Restaurant.js
const mongoose = require('mongoose');

const restaurantSchema = new mongoose.Schema({
  name: { type: String, required: true },
  type: { type: String, required: true },
  rating: { type: Number, default: 0 },
  priceRange: { type: String, required: true },
  specialty: { type: String, required: true },
  emoji: { type: String },
  imageUrl: { type: String },
  location: {
    latitude: Number,
    longitude: Number,
  },
  createdAt: { type: Date, default: Date.now },
});

module.exports = mongoose.model('Restaurant', restaurantSchema);
