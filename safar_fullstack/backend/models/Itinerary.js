// models/Itinerary.js
const mongoose = require('mongoose');

const itinerarySchema = new mongoose.Schema({
  userId: { type: mongoose.Schema.Types.ObjectId, ref: 'User' },
  title: { type: String, required: true },
  days: { type: Number, required: true },
  budget: { type: Number, required: true },
  interests: [{ type: String }],
  travelStyle: { type: String },
  activityLevel: { type: String },
  dailyPlans: [
    {
      day: Number,
      title: String,
      activities: [String],
      estimatedCost: Number,
    },
  ],
  totalCost: { type: Number },
  createdAt: { type: Date, default: Date.now },
});

module.exports = mongoose.model('Itinerary', itinerarySchema);
