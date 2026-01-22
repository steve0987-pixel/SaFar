// routes/places.js
const express = require('express');
const router = express.Router();
const Place = require('../models/Place');

// GET all places
router.get('/', async (req, res) => {
  try {
    const places = await Place.find().sort({ rating: -1 });
    res.json(places);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// GET single place by ID
router.get('/:id', async (req, res) => {
  try {
    const place = await Place.findById(req.params.id);
    if (!place) return res.status(404).json({ error: 'Place not found' });
    res.json(place);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// POST create new place (admin only - add auth middleware in production)
router.post('/', async (req, res) => {
  try {
    const place = new Place(req.body);
    await place.save();
    res.status(201).json(place);
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

// PUT update place
router.put('/:id', async (req, res) => {
  try {
    const place = await Place.findByIdAndUpdate(req.params.id, req.body, {
      new: true,
      runValidators: true,
    });
    if (!place) return res.status(404).json({ error: 'Place not found' });
    res.json(place);
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

// DELETE place
router.delete('/:id', async (req, res) => {
  try {
    const place = await Place.findByIdAndDelete(req.params.id);
    if (!place) return res.status(404).json({ error: 'Place not found' });
    res.json({ message: 'Place deleted successfully' });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

module.exports = router;
