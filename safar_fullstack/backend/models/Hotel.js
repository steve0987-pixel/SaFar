// models/Hotel.js
const mongoose = require('mongoose');

const hotelSchema = new mongoose.Schema({
  name: { type: String, required: true },
  stars: { type: Number, min: 1, max: 5 },
  price: { type: Number, required: true },
  description: { type: String, required: true },
  rating: { type: Number, default: 0 },
  amenities: [{ type: String }],
  imageUrl: { type: String },
  location: {
    latitude: Number,
    longitude: Number,
  },
  createdAt: { type: Date, default: Date.now },
});

module.exports = mongoose.model('Hotel', hotelSchema);
