// models/Place.js
const mongoose = require('mongoose');

const placeSchema = new mongoose.Schema({
  name: { type: String, required: true },
  description: { type: String, required: true },
  rating: { type: Number, default: 0 },
  cost: { type: String, required: true },
  time: { type: String, required: true },
  imageUrl: { type: String },
  location: {
    latitude: Number,
    longitude: Number,
  },
  category: { type: String, default: 'historical' },
  createdAt: { type: Date, default: Date.now },
});

module.exports = mongoose.model('Place', placeSchema);
