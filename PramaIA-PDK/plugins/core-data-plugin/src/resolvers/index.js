// index.js - Esporta tutti i resolver del plugin core-data-plugin

const file_cleanup_resolver = require('./file_cleanup_resolver.py');
// ...eventuali altri resolver

module.exports = {
  file_cleanup: file_cleanup_resolver,
  // ...altri resolver
};
