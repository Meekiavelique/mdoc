document.addEventListener('DOMContentLoaded', function() {
    const desmosElements = document.querySelectorAll('.mdoc-desmos-graph');
    
    if (desmosElements.length === 0) {
        return;
    }
    
    const script = document.createElement('script');
    script.src = 'https://www.desmos.com/api/v1.7/calculator.js?apiKey=dcb31709b452b1cf9dc26972add0fda6';
    script.onload = initializeDesmosGraphs;
    document.head.appendChild(script);
});

function initializeDesmosGraphs() {
    const placeholders = document.querySelectorAll('.mdoc-desmos-graph');
    
    placeholders.forEach((placeholder, index) => {
        try {
            const encodedConfig = placeholder.getAttribute('data-graph-config');
            
            if (!encodedConfig) {
                console.error('No configuration found for Desmos graph');
                return;
            }
            
            const configString = atob(encodedConfig);
            const config = JSON.parse(configString);
            
            const header = document.createElement('div');
            header.className = 'component-header';
            header.textContent = 'Interactive Math Graph';
            placeholder.appendChild(header);
            
            const body = document.createElement('div');
            body.className = 'component-body';
            placeholder.appendChild(body);
            
            const controlsDiv = document.createElement('div');
            if (config.interactive && config.parameters) {
                controlsDiv.className = 'desmos-controls';
                body.appendChild(controlsDiv);
            }
            
            const calculatorDiv = document.createElement('div');
            calculatorDiv.className = 'desmos-calculator';
            calculatorDiv.style.width = config.width || '600px';
            calculatorDiv.style.height = config.height || '400px';
            body.appendChild(calculatorDiv);
            
            const calculator = Desmos.GraphingCalculator(calculatorDiv, {
                expressions: config.expressions || false,
                settingsMenu: config.settingsMenu || false,
                zoomButtons: config.zoomButtons || true,
                expressionsCollapsed: config.expressionsCollapsed || false,
                lockViewport: config.lockViewport || false,
                restrictedFunctions: config.restrictedFunctions || false,
            });
            
            if (config.bounds) {
                calculator.setMathBounds(config.bounds);
            }
            
            if (config.expressions && Array.isArray(config.expressionsList)) {
                config.expressionsList.forEach(expr => {
                    calculator.setExpression(expr);
                });
            }
            
            if (config.interactive && config.parameters) {
                createDesmosControls(controlsDiv, calculator, config.parameters);
            }
            
        } catch (error) {
            console.error('Error initializing Desmos graph:', error);
            
            const errorMsg = document.createElement('div');
            errorMsg.className = 'desmos-error';
            errorMsg.textContent = 'Error loading graph: ' + (error.message || 'Unknown error');
            placeholder.appendChild(errorMsg);
        }
    });
}

function createDesmosControls(container, calculator, parameters) {
    parameters.forEach(param => {
        const control = document.createElement('div');
        control.className = 'desmos-control';
        
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
        valueDisplay.className = 'desmos-value';
        
        input.addEventListener('input', function() {
            const value = parseFloat(input.value);
            valueDisplay.textContent = value;
            
            calculator.setExpression({ id: param.id, latex: param.id + '=' + value });
        });
        
        calculator.setExpression({ id: param.id, latex: param.id + '=' + param.default });
        
        control.appendChild(label);
        control.appendChild(input);
        control.appendChild(valueDisplay);
        container.appendChild(control);
    });
}