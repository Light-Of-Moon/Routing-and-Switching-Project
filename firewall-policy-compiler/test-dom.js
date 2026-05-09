const jsdom = require("jsdom");
const { JSDOM } = jsdom;
const fs = require('fs');

const html = fs.readFileSync('templates/index.html', 'utf-8');
const scriptCode = fs.readFileSync('static/js/main.js', 'utf-8');

const dom = new JSDOM(html, { runScripts: "dangerously" });
const document = dom.window.document;

function test() {
    try {
        const scriptEl = document.createElement("script");
        scriptEl.textContent = scriptCode;
        document.body.appendChild(scriptEl);
        
        // Run DOMContentLoaded
        const event = document.createEvent("Event");
        event.initEvent("DOMContentLoaded", true, true);
        document.dispatchEvent(event);

        cons = document.getElementById("btn-toggle-builder");
        cons.click();
        
        console.log("Visual Builder display:", document.getElementById("visual-builder").style.display);
        
        document.getElementById("btn-add-rule").click();
        console.log("Editor value:", document.getElementById("policy-editor").value.substring(0, 100));
        
    } catch(e) {
        console.error("ERROR:", e);
    }
}
test();
