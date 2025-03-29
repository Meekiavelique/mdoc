document.addEventListener('DOMContentLoaded', function() {
    const p5jsElements = document.querySelectorAll('.mdoc-p5js-sketch');

    if (p5jsElements.length === 0) {
        return;
    }

    const p5Script = document.createElement('script');
    p5Script.src = 'https://cdn.jsdelivr.net/npm/p5@1.7.0/lib/p5.js';
    p5Script.onload = initializeP5jsElements;
    document.head.appendChild(p5Script);
});

function initializeP5jsElements() {
    const placeholders = document.querySelectorAll('.mdoc-p5js-sketch');

    placeholders.forEach((placeholder, index) => {
        try {
            const encodedCode = placeholder.getAttribute('data-sketch-code');
            if (!encodedCode) {
                placeholder.innerHTML = '<div class="p5js-error">Error: No sketch code found.</div>';
                console.error('No sketch code found for p5.js sketch');
                return;
            }

            let sketchCode = '';
            try {
                sketchCode = atob(encodedCode);
            } catch (e) {
                placeholder.innerHTML = '<div class="p5js-error">Error decoding sketch code.</div>';
                console.error('Error decoding sketch code:', e);
                return;
            }

            placeholder.innerHTML = '';

            const header = document.createElement('div');
            header.className = 'component-header';
            header.textContent = 'Interactive Sketch';
            placeholder.appendChild(header);

            const body = document.createElement('div');
            body.className = 'component-body';
            placeholder.appendChild(body);

            const controls = document.createElement('div');
            controls.className = 'p5js-controls';
            body.appendChild(controls);

            const restartBtn = document.createElement('button');
            restartBtn.className = 'p5js-restart-btn';
            restartBtn.textContent = 'Restart Sketch';
            controls.appendChild(restartBtn);

            const codeViewerBtn = document.createElement('button');
            codeViewerBtn.className = 'p5js-show-code-btn';
            codeViewerBtn.textContent = 'Show Code';
            controls.appendChild(codeViewerBtn);

            const sketchContainer = document.createElement('div');
            sketchContainer.className = 'p5js-sketch-container';
            sketchContainer.id = `p5js-sketch-${index}`;
            body.appendChild(sketchContainer);

            const codeViewer = document.createElement('div');
            codeViewer.className = 'p5js-code-viewer hidden';

            const codeBlock = document.createElement('pre');
            codeBlock.innerHTML = `<code class="language-javascript">${escapeHtml(sketchCode)}</code>`;
            codeViewer.appendChild(codeBlock);

            body.appendChild(codeViewer);

            let currentSketch = null;

            function displayError(container, message) {
                container.innerHTML = '';
                const errorMsg = document.createElement('div');
                errorMsg.className = 'p5js-error';
                errorMsg.style.padding = '10px';
                errorMsg.style.color = 'red';
                errorMsg.textContent = message;
                container.appendChild(errorMsg);
            }

            function initSketch() {
                try {
                    if (currentSketch) {
                        currentSketch.remove();
                        currentSketch = null;
                    }
                    sketchContainer.innerHTML = '';

                    const sketchFn = (p) => {
                        let userFunctions = {};

                        try {
                            const evalWrapper = new Function('p', `
                                let userDefinedSetup, userDefinedDraw, userDefinedPreload,
                                    userDefinedMousePressed, userDefinedMouseReleased, userDefinedMouseDragged,
                                    userDefinedKeyPressed, userDefinedKeyReleased, userDefinedKeyTyped,
                                    userDefinedWindowResized;

                                ${sketchCode}

                                return {
                                    setup: typeof setup === 'function' ? setup : null,
                                    draw: typeof draw === 'function' ? draw : null,
                                    preload: typeof preload === 'function' ? preload : null,
                                    mousePressed: typeof mousePressed === 'function' ? mousePressed : null,
                                    mouseReleased: typeof mouseReleased === 'function' ? mouseReleased : null,
                                    mouseDragged: typeof mouseDragged === 'function' ? mouseDragged : null,
                                    keyPressed: typeof keyPressed === 'function' ? keyPressed : null,
                                    keyReleased: typeof keyReleased === 'function' ? keyReleased : null,
                                    keyTyped: typeof keyTyped === 'function' ? keyTyped : null,
                                    windowResized: typeof windowResized === 'function' ? windowResized : null
                                };
                            `);

                            userFunctions = evalWrapper(p);
                        } catch (e) {
                            console.error('Error evaluating sketch code:', e);
                            displayError(sketchContainer, 'Error in sketch code: ' + e.message);
                            throw e;
                        }

                        p.preload = userFunctions.preload || function() {};
                        p.setup = function() {
                            try {
                                if (userFunctions.setup) {
                                    userFunctions.setup();
                                } else {
                                    p.createCanvas(400, 300);
                                    p.background(240);
                                    p.fill(100);
                                    p.textAlign(p.CENTER);
                                    p.text('p5.js sketch area\n(No setup() function found in code)', p.width / 2, p.height / 2);
                                }
                                if (!p.canvas) {
                                    p.createCanvas(400, 300).parent(sketchContainer);
                                    p.background(240);
                                    p.fill(255,0,0);
                                    p.text('Warning: setup() did not create a canvas.', 10, 20);
                                } else {
                                    p.canvas.elt.parentNode !== sketchContainer && p.canvas.parent(sketchContainer);
                                }
                            } catch(e) {
                                console.error('Error during p5 setup execution:', e);
                                displayError(sketchContainer, 'Error in setup(): ' + e.message);
                                p.noLoop();
                            }
                        };

                        p.draw = userFunctions.draw || function() {};
                        p.mousePressed = userFunctions.mousePressed || function() {};
                        p.mouseReleased = userFunctions.mouseReleased || function() {};
                        p.mouseDragged = userFunctions.mouseDragged || function() {};
                        p.keyPressed = userFunctions.keyPressed || function() {};
                        p.keyReleased = userFunctions.keyReleased || function() {};
                        p.keyTyped = userFunctions.keyTyped || function() {};
                        p.windowResized = userFunctions.windowResized || function() {};
                    };

                    currentSketch = new p5(sketchFn, sketchContainer);

                } catch (error) {
                    console.error('Fatal error initializing p5.js sketch:', error);
                    displayError(sketchContainer, 'Error initializing sketch: ' + (error.message || 'Unknown error'));
                }
            }

            initSketch();

            restartBtn.addEventListener('click', initSketch);

            codeViewerBtn.addEventListener('click', function() {
                const isHidden = codeViewer.classList.contains('hidden');

                if (isHidden) {
                    codeViewer.classList.remove('hidden');
                    codeViewerBtn.textContent = 'Hide Code';
                } else {
                    codeViewer.classList.add('hidden');
                    codeViewerBtn.textContent = 'Show Code';
                }
            });

        } catch (error) {
            console.error('Error setting up p5.js placeholder:', error);
            placeholder.innerHTML = `<div class="p5js-error">Error setting up sketch container: ${error.message}</div>`;
        }
    });
}

function escapeHtml(text) {
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}