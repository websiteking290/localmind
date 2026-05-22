// server.js
const express = require('express');
const cookieParser = require('cookie-parser');
const path = require('path');
require('dotenv').config();

const app = express();

app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(cookieParser());
app.use(express.static(path.join(__dirname, 'public')));

app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

// Routes
app.use('/api/auth', require('./routes/auth'));
app.use('/api', require('./routes/api'));

// Pages
app.get('/', (req, res) => res.redirect('/buy'));
app.get('/buy', (req, res) => res.render('buy'));
app.get('/login', (req, res) => res.render('login'));
app.get('/dashboard', (req, res) => res.render('dashboard'));
app.get('/admin', (req, res) => res.render('admin'));

const PORT = process.env.PORT || 3001;
app.listen(PORT, () => console.log(`LocalMind Portal running on http://localhost:${PORT}`));
