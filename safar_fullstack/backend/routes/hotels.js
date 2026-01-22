// routes/hotels.js
const express = require('express');
const router = express.Router();
const Hotel = require('../models/Hotel');

// GET all hotels
router.get('/', async (req, res) => {
  try {
    const { minPrice, maxPrice, stars } = req.query;
    let query = {};

    if (minPrice || maxPrice) {
      query.price = {};
      if (minPrice) query.price.$gte = Number(minPrice);
      if (maxPrice) query.price.$lte = Number(maxPrice);
    }

    if (stars) {
      query.stars = Number(stars);
    }

    const hotels = await Hotel.find(query).sort({ rating: -1 });
    res.json(hotels);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// GET single hotel
router.get('/:id', async (req, res) => {
  try {
    const hotel = await Hotel.findById(req.params.id);
    if (!hotel) return res.status(404).json({ error: 'Hotel not found' });
    res.json(hotel);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// POST create hotel
router.post('/', async (req, res) => {
  try {
    const hotel = new Hotel(req.body);
    await hotel.save();
    res.status(201).json(hotel);
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

module.exports = router;
