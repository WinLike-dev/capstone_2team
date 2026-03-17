const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
require('dotenv').config();

const app = express();

// Middleware
app.use(helmet());
app.use(cors());
app.use(morgan('dev'));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// 기본 라우트
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', message: 'API Server is running' });
});

// API 라우트
app.use('/api/v1/auth', require('./routes/auth'));
app.use('/api/v1/users', require('./routes/users'));
app.use('/api/v1/chat', require('./routes/chat'));
app.use('/api/v1/admin', require('./routes/admin'));

module.exports = app;
