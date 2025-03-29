document.addEventListener('DOMContentLoaded', function() {
    const geogebraElements = document.querySelectorAll('.mdoc-geogebra');
    
    if (geogebraElements.length === 0) {
        return;
    }
    
    const script = document.createElement('script');
    script.src = 'https://www.geogebra.org/apps/deployggb.js';
    script.onload = initializeGeoGebraApplets;
    document.head.appendChild(script);
});

function initializeGeoGebraApplets() {
    const placeholders = document.querySelectorAll('.mdoc-geogebra');
    
    placeholders.forEach((placeholder, index) => {
        try {
            const encodedConfig = placeholder.getAttribute('data-geogebra-config');
            
            if (!encodedConfig) {
                console.error('No configuration found for GeoGebra applet');
                return;
            }
            
            const configString = atob(encodedConfig);
            const config = JSON.parse(configString);
            
            const width = config.width || 800;
            const height = config.height || 600;
            
            placeholder.style.width = width + 'px';
            placeholder.style.height = height + 'px';
            
            const header = document.createElement('div');
            header.className = 'component-header';
            header.textContent = 'Interactive Geometry';
            placeholder.appendChild(header);
            
            const body = document.createElement('div');
            body.className = 'component-body';
            placeholder.appendChild(body);
            
            const controlsDiv = document.createElement('div');
            controlsDiv.className = 'geogebra-controls';
            body.appendChild(controlsDiv);
            
            const parameters = config.parameters || [];
            
            const geogebraContainer = document.createElement('div');
            geogebraContainer.id = `geogebra-container-inner-${index}`;
            body.appendChild(geogebraContainer);
            
            const params = {
                id: "ggbApplet" + index,
                width: width,
                height: height,
                showMenuBar: config.showMenuBar || false,
                showAlgebraInput: config.showAlgebraInput || false,
                showToolBar: config.showToolBar || false,
                showResetIcon: config.showResetIcon || true,
                enableLabelDrags: config.enableLabelDrags || false,
                enableShiftDragZoom: config.enableShiftDragZoom || true,
                enableRightClick: config.enableRightClick || false,
                errorDialogsActive: false,
                useBrowserForJS: true,
                allowStyleBar: config.allowStyleBar || false,
                preventFocus: config.preventFocus || true,
                showZoomButtons: config.showZoomButtons || true,
                capturingThreshold: config.capturingThreshold || 3,
                showFullscreenButton: config.showFullscreenButton || true,
                scale: config.scale || 1,
                autoHeight: config.autoHeight || false,
                appletOnLoad: function(api) {
                    window["ggbApplet" + index] = api;
                    
                    if (config.appletCode) {
                        const commands = config.appletCode.split(';');
                        commands.forEach(cmd => {
                            if (cmd.trim().length > 0) {
                                try {
                                    api.evalCommand(cmd.trim());
                                } catch (e) {
                                    console.error('Error executing GeoGebra command:', e);
                                }
                            }
                        });
                    }
                    
                    createControls(parameters, api, controlsDiv);
                }
            };
            
            if (config.materialId) {
                params.material_id = config.materialId;
            }
            
            if (config.ggbBase64) {
                params.ggbBase64 = config.ggbBase64;
            }
            
            const applet = new GGBApplet(params, true);
            applet.inject(geogebraContainer.id);
            
        } catch (error) {
            console.error('Error initializing GeoGebra applet:', error);
            
            const errorMsg = document.createElement('div');
            errorMsg.className = 'geogebra-error';
            errorMsg.textContent = 'Error loading GeoGebra applet: ' + (error.message || 'Unknown error');
            placeholder.appendChild(errorMsg);
        }
    });
}

function createControls(parameters, ggbApplet, container) {
    if (!parameters || parameters.length === 0 || !ggbApplet) {
        container.style.display = 'none';
        return;
    }
    
    parameters.forEach(param => {
        try {
            try {
                ggbApplet.evalCommand(param.id + '=' + param.default);
            } catch (e) {
                console.error('Error initializing parameter ' + param.id + ':', e);
            }
            
            const control = document.createElement('div');
            control.className = 'geogebra-control';
            
            const label = document.createElement('label');
            label.textContent = param.name + ': ';
            
            const input = document.createElement('input');
            input.type = 'range';
            input.min = param.min;
            input.max = param.max;
            input.step = param.step || 0.1;
            input.value = param.default;
            
            const valueDisplay = document.createElement('span');
            valueDisplay.textContent = param.default;
            valueDisplay.className = 'geogebra-value';
            
            input.addEventListener('input', function() {
                const value = parseFloat(input.value);
                valueDisplay.textContent = value;
                
                try {
                    ggbApplet.evalCommand(param.id + '=' + value);
                } catch (e) {
                    console.error('Error setting GeoGebra value for ' + param.id + ':', e);
                }
            });
            
            control.appendChild(label);
            control.appendChild(input);
            control.appendChild(valueDisplay);
            container.appendChild(control);
        } catch (e) {
            console.error('Error creating control for parameter ' + param.id + ':', e);
        }
    });
}