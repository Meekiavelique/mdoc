function escapeHtml(unsafeText) {
    const element = document.createElement('div');
    element.textContent = unsafeText;
    return element.innerHTML;
}

function displayP5Error(containerElement, message) {
    containerElement.innerHTML = '';
    const errorDiv = document.createElement('div');
    errorDiv.className = 'p5js-error';
    errorDiv.style.padding = '10px';
    errorDiv.style.color = 'red';
    errorDiv.style.border = '1px solid red';
    errorDiv.style.backgroundColor = '#fee';
    errorDiv.textContent = `Error: ${message}`;
    containerElement.appendChild(errorDiv);
    console.error(`P5.js Sketch Error: ${message}`);
}

function initializeSingleP5Sketch(placeholderElement, index) {
    let currentP5Instance = null;
    const sketchContainerId = `p5js-sketch-container-${index}`;

    function removeExistingSketch() {
        if (currentP5Instance) {
            try {
                currentP5Instance.remove();
            } catch (e) {
                console.warn(`Non-critical error removing previous p5 instance ${index}:`, e);
            }
            currentP5Instance = null;
        }
        const container = document.getElementById(sketchContainerId);
        if (container) {
            container.innerHTML = '';
        } else {
             console.warn(`Container ${sketchContainerId} not found during removal.`);
        }
    }

    try {
        const encodedCode = placeholderElement.getAttribute('data-sketch-code');
        if (!encodedCode) {
            throw new Error('No sketch code found in data-sketch-code attribute.');
        }

        let sketchCode = '';
        try {
            sketchCode = atob(encodedCode);
        } catch (e) {
            throw new Error(`Failed to decode base64 sketch code: ${e.message}`);
        }

        placeholderElement.innerHTML = '';

        const header = document.createElement('div');
        header.className = 'component-header';
        header.textContent = 'Interactive Sketch';
        placeholderElement.appendChild(header);

        const body = document.createElement('div');
        body.className = 'component-body';
        placeholderElement.appendChild(body);

        const controls = document.createElement('div');
        controls.className = 'p5js-controls';
        body.appendChild(controls);

        const restartButton = document.createElement('button');
        restartButton.className = 'p5js-restart-btn';
        restartButton.textContent = 'Restart Sketch';
        controls.appendChild(restartButton);

        const codeViewerButton = document.createElement('button');
        codeViewerButton.className = 'p5js-show-code-btn';
        codeViewerButton.textContent = 'Show Code';
        controls.appendChild(codeViewerButton);

        const sketchContainer = document.createElement('div');
        sketchContainer.className = 'p5js-sketch-container';
        sketchContainer.id = sketchContainerId;
        body.appendChild(sketchContainer);

        const codeViewer = document.createElement('div');
        codeViewer.className = 'p5js-code-viewer hidden';
        const codeBlock = document.createElement('pre');
        const codeElement = document.createElement('code');
        codeElement.className = 'language-javascript';
        codeElement.textContent = sketchCode;
        codeBlock.appendChild(codeElement);
        codeViewer.appendChild(codeBlock);
        body.appendChild(codeViewer);

        function createSketch() {
            removeExistingSketch();
            try {
                const sketchFunction = new Function('p', sketchCode);
                currentP5Instance = new p5(sketchFunction, sketchContainer);

                if (!currentP5Instance || !currentP5Instance.canvas) {
                     setTimeout(() => {
                         if (!currentP5Instance || !currentP5Instance.canvas) {
                             console.warn(`P5 instance ${index} or its canvas might not have initialized correctly after delay.`);
                             if (!document.getElementById(sketchContainerId)?.querySelector('canvas')) {
                                displayP5Error(sketchContainer, 'Sketch failed to create a canvas element.');
                             }
                         }
                     }, 300);
                }

            } catch (error) {
                const errorMessage = error instanceof SyntaxError
                    ? `Syntax error in sketch code: ${error.message}`
                    : `Runtime error initializing sketch: ${error.message}`;
                displayP5Error(sketchContainer, errorMessage);
                if (error.stack) {
                     console.error(error.stack);
                }
                currentP5Instance = null;
            }
        }

        restartButton.addEventListener('click', createSketch);

        codeViewerButton.addEventListener('click', function() {
            const isHidden = codeViewer.classList.toggle('hidden');
            codeViewerButton.textContent = isHidden ? 'Show Code' : 'Hide Code';
            if (!isHidden && typeof Prism !== 'undefined') {
                 Prism.highlightElement(codeElement);
            }
        });

        createSketch();

    } catch (error) {
        displayP5Error(placeholderElement, `Setup error: ${error.message}`);
    }
}

function initializeAllP5Sketches() {
    console.log("P5.js library loaded successfully. Initializing sketches.");
    const p5jsPlaceholders = document.querySelectorAll('.mdoc-p5js-sketch');
    p5jsPlaceholders.forEach(initializeSingleP5Sketch);
}

function loadP5LibraryAndInitialize() {
    const p5jsPlaceholders = document.querySelectorAll('.mdoc-p5js-sketch');
    if (p5jsPlaceholders.length === 0) {
        return;
    }

    if (typeof p5 !== 'undefined') {
        console.log("P5.js already loaded. Initializing sketches directly.");
        initializeAllP5Sketches();
        return;
    }

    const p5Script = document.createElement('script');
    p5Script.src = 'https://cdn.jsdelivr.net/npm/p5@1.7.0/lib/p5.js';
    p5Script.async = true;

    p5Script.onload = initializeAllP5Sketches;

    p5Script.onerror = function() {
        console.error("Failed to load P5.js library from CDN.");
        p5jsPlaceholders.forEach(el => {
            displayP5Error(el, 'Failed to load P5.js library. Cannot run sketch.');
        });
    };

    document.head.appendChild(p5Script);
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', loadP5LibraryAndInitialize);
} else {
    loadP5LibraryAndInitialize();
}