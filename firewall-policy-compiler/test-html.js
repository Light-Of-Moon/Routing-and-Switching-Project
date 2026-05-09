const fs = require('fs');
const html = fs.readFileSync('templates/index.html', 'utf-8');
const js = fs.readFileSync('static/js/main.js', 'utf-8');
if (!html.includes('btn-toggle-builder')) console.log("Missing html toggle");
if (!js.includes('btn-toggle-builder')) console.log("Missing js toggle");
// Let's run the JS through a mock DOM to see if it throws any errors simulating the clicks.
