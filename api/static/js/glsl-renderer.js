document.addEventListener('DOMContentLoaded', function() {
    const glslElements = document.querySelectorAll('.mdoc-glsl-canvas');
    
    if (glslElements.length === 0) {
        return;
    }
    
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/glslCanvas@0.2.6/dist/GlslCanvas.min.js';
    script.onload = initializeGlslCanvases;
    document.head.appendChild(script);
});

function initializeGlslCanvases() {
    const placeholders = document.querySelectorAll('.mdoc-glsl-canvas');
    
    placeholders.forEach((placeholder, index) => {
        try {
            const encodedShader = placeholder.getAttribute('data-fragment-shader');
            const simpleDisplay = placeholder.getAttribute('data-simple-display') === 'true';
            const noUI = placeholder.getAttribute('data-no-ui') === 'true';
            const customWidth = parseInt(placeholder.getAttribute('data-width')) || 600;
            const customHeight = parseInt(placeholder.getAttribute('data-height')) || 400;

            // Debug logging
            console.log(`Canvas ${index}: simpleDisplay=${simpleDisplay}, noUI=${noUI}, dims=${customWidth}x${customHeight}`);

            if (!encodedShader) {
                console.error(`No shader code found for GLSL canvas ${index}`);
                placeholder.textContent = 'Error: Shader code missing.';
                return;
            }

            if (noUI) {
                placeholder.classList.add('no-ui');
            }

            const shaderCode = atob(encodedShader);
            placeholder.innerHTML = '';

            if (!simpleDisplay && !noUI) {
                console.log(`Canvas ${index}: Creating FULL UI`);
                
                // Create full UI structure
                const header = document.createElement('div');
                header.className = 'component-header';
                header.textContent = 'Interactive Shader';
                placeholder.appendChild(header);
                
                const body = document.createElement('div');
                body.className = 'component-body';
                placeholder.appendChild(body);
                
                // Controls
                const controls = document.createElement('div');
                controls.className = 'glsl-controls';
                body.appendChild(controls);
                
                const spacer = document.createElement('span');
                spacer.style.flex = '1';
                controls.appendChild(spacer);
                
                const pauseBtn = document.createElement('button');
                pauseBtn.className = 'glsl-control-btn';
                pauseBtn.textContent = 'Pause';
                controls.appendChild(pauseBtn);
                
                const resetBtn = document.createElement('button');
                resetBtn.className = 'glsl-control-btn';
                resetBtn.textContent = 'Reset';
                controls.appendChild(resetBtn);
                
                // Canvas
                const canvas = document.createElement('canvas');
                canvas.width = customWidth;
                canvas.height = customHeight;
                canvas.className = 'glsl-canvas';
                body.appendChild(canvas);
                
                // Info panel
                const infoDiv = document.createElement('div');
                infoDiv.className = 'glsl-info';
                const timeInfo = document.createElement('div');
                timeInfo.className = 'time';
                timeInfo.textContent = 'Time: 0.0s';
                const fpsCounter = document.createElement('div');
                fpsCounter.className = 'fps';
                fpsCounter.textContent = 'FPS: --';
                infoDiv.appendChild(timeInfo);
                infoDiv.appendChild(fpsCounter);
                body.appendChild(infoDiv);
                
                const glslCanvas = new GlslCanvas(canvas);
                if (glslCanvas) {
                    glslCanvas.load(shaderCode);
                    setupMouseInteraction(canvas, glslCanvas);
                    setupPerformanceMonitor(infoDiv, glslCanvas);
                    
                    let isPaused = false;
                    let customTime = 0;
                    
                    pauseBtn.addEventListener('click', () => {
                        isPaused = !isPaused;
                        pauseBtn.textContent = isPaused ? 'Play' : 'Pause';
                        if (isPaused) {
                            customTime = glslCanvas.uniforms.u_time?.value || 0;
                        }
                        console.log(`Canvas ${index}: ${isPaused ? 'Paused' : 'Resumed'} at ${customTime}s`);
                    });
                    
                    resetBtn.addEventListener('click', () => {
                        console.log(`Canvas ${index}: Reset triggered`);
                        glslCanvas.load(shaderCode);
                        customTime = 0;
                        isPaused = false;
                        pauseBtn.textContent = 'Pause';
                        glslCanvas.setUniform('u_mouseDown', 0.0);
                        glslCanvas.setUniform('u_mouse', 0.5, 0.5);
                    });
                    
                    // Modify render loop for pause support
                    const originalRender = glslCanvas.render;
                    glslCanvas.render = function() {
                        if (!isPaused) {
                            originalRender.call(glslCanvas);
                            customTime = glslCanvas.uniforms.u_time?.value || 0;
                        } else {
                            glslCanvas.uniforms.u_time = { type: 'f', value: customTime };
                            originalRender.call(glslCanvas);
                        }
                    };
                }
            } else {
                console.log(`Canvas ${index}: Creating minimal canvas (${noUI ? 'noUI' : 'simple'})`);
                
                if (noUI) {
                    placeholder.style.border = 'none';
                    placeholder.style.padding = '0';
                    placeholder.style.margin = '0';
                    placeholder.style.background = 'none';
                }
                
                const canvas = document.createElement('canvas');
                canvas.width = customWidth;
                canvas.height = customHeight;
                canvas.className = noUI ? 'glsl-canvas-noui' : 'glsl-canvas-simple';
                canvas.style.width = '100%';
                canvas.style.height = 'auto';
                canvas.style.display = 'block';
                if (noUI) {
                    canvas.style.border = 'none';
                }
                placeholder.appendChild(canvas);
                
                const glslCanvas = new GlslCanvas(canvas);
                if (glslCanvas) {
                    glslCanvas.load(shaderCode);
                    if (!noUI) {
                        setupMouseInteraction(canvas, glslCanvas);
                    }
                }
            }
        } catch (error) {
            console.error(`Error initializing GLSL canvas ${index}:`, error);
            placeholder.innerHTML = '';
            const errorMsg = document.createElement('div');
            errorMsg.className = 'glsl-error';
            errorMsg.textContent = 'Error loading shader: ' + (error.message || 'Unknown error');
            placeholder.appendChild(errorMsg);
        }
    });
}

function setupMouseInteraction(canvas, glslCanvas) {
    let isMouseDown = false;
    let lastX = 0, lastY = 0;
    
    function updateMouse(e) {
        const rect = canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = rect.height - (e.clientY - rect.top);
        
        const normX = Math.max(0, Math.min(1, x / rect.width));
        const normY = Math.max(0, Math.min(1, y / rect.height));
        
        glslCanvas.setUniform('u_mouse', normX, normY);
        
        if (isMouseDown) {
            const deltaX = (x - lastX) / rect.width;
            const deltaY = (y - lastY) / rect.height;
            
            glslCanvas.setUniform('u_mouseDelta', deltaX, deltaY);
        }
        
        lastX = x;
        lastY = y;
    }
    
    canvas.addEventListener('mousedown', function(e) {
        isMouseDown = true;
        updateMouse(e);
        glslCanvas.setUniform('u_mouseDown', 1.0);
    });
    
    canvas.addEventListener('mouseup', function() {
        isMouseDown = false;
        glslCanvas.setUniform('u_mouseDown', 0.0);
    });
    
    canvas.addEventListener('mousemove', updateMouse);
    
    canvas.addEventListener('mouseleave', function() {
        glslCanvas.setUniform('u_mouseDown', 0.0);
        isMouseDown = false;
    });
    
    glslCanvas.setUniform('u_mouse', 0.5, 0.5);
    glslCanvas.setUniform('u_mouseDown', 0.0);
    glslCanvas.setUniform('u_mouseDelta', 0.0, 0.0);
}

function setupPerformanceMonitor(infoDiv, glslCanvas) {
    const fpsCounter = infoDiv.querySelector('.fps');
    const timeInfo = infoDiv.querySelector('.time');
    
    let lastTime = performance.now();
    let frames = 0;
    
    function updateInfo() {
        const now = performance.now();
        frames++;
        
        if (now - lastTime >= 1000) {
            fpsCounter.textContent = `FPS: ${frames}`;
            frames = 0;
            lastTime = now;
        }
        
        if (glslCanvas.uniforms && glslCanvas.uniforms.u_time) {
            const shaderTime = glslCanvas.uniforms.u_time.value;
            if (typeof shaderTime === 'number') {
                timeInfo.textContent = `Time: ${shaderTime.toFixed(1)}s`;
            }
        }
        
        requestAnimationFrame(updateInfo);
    }
    
    requestAnimationFrame(updateInfo);
}