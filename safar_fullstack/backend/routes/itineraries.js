// routes/itineraries.js
const express = require('express');
const router = express.Router();
const Itinerary = require('../models/Itinerary');

// GET all itineraries for a user
router.get('/', async (req, res) => {
  try {
    const { userId } = req.query;
    const query = userId ? { userId } : {};
    const itineraries = await Itinerary.find(query).sort({ createdAt: -1 });
    res.json(itineraries);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// GET single itinerary
router.get('/:id', async (req, res) => {
  try {
    const itinerary = await Itinerary.findById(req.params.id);
    if (!itinerary) return res.status(404).json({ error: 'Itinerary not found' });
    res.json(itinerary);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// POST create itinerary (AI-generated or manual)
router.post('/', async (req, res) => {
  try {
    const { days, budget, interests, travelStyle, activityLevel } = req.body;

    // Generate daily plans based on inputs
    const dailyPlans = [];
    const titles = [
      'Arrival & Orientation',
      'Historic Samarkand',
      'Silk Road Heritage',
      'Culture & Cuisine',
      'Leisure & Departure',
    ];

    for (let i = 0; i < days; i++) {
      dailyPlans.push({
        day: i + 1,
        title: titles[i % titles.length],
        activities: [
          'Morning activity',
          'Lunch break',
          'Afternoon exploration',
          'Evening experience',
        ],
        estimatedCost: budget,
      });
    }

    const itinerary = new Itinerary({
      ...req.body,
      title: `${days}-Day Samarkand Adventure`,
      dailyPlans,
      totalCost: days * budget,
    });

    await itinerary.save();
    res.status(201).json(itinerary);
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

// PUT update itinerary
router.put('/:id', async (req, res) => {
  try {
    const itinerary = await Itinerary.findByIdAndUpdate(req.params.id, req.body, {
      new: true,
      runValidators: true,
    });
    if (!itinerary) return res.status(404).json({ error: 'Itinerary not found' });
    res.json(itinerary);
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

// DELETE itinerary
router.delete('/:id', async (req, res) => {
  try {
    const itinerary = await Itinerary.findByIdAndDelete(req.params.id);
    if (!itinerary) return res.status(404).json({ error: 'Itinerary not found' });
    res.json({ message: 'Itinerary deleted successfully' });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

module.exports = router;
