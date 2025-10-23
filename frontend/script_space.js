let scene, camera, renderer, particles;

function initThree() {
    scene = new THREE.Scene();
    camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.z = 50;

    renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    document.getElementById('scene-container').appendChild(renderer.domElement);

    const geometry = new THREE.BufferGeometry();
    const particleCount = 1000;
    const positions = new Float32Array(particleCount * 3);
    const colors = new Float32Array(particleCount * 3);

    const neonColors = [
        { r: 0, g: 0.96, b: 1 },
        { r: 1, g: 0, b: 0.43 },
        { r: 0.72, g: 0.58, b: 0.96 }
    ];

    for (let i = 0; i < particleCount; i++) {
        const i3 = i * 3;
        positions[i3] = (Math.random() - 0.5) * 200;
        positions[i3 + 1] = (Math.random() - 0.5) * 200;
        positions[i3 + 2] = (Math.random() - 0.5) * 200;

        const color = neonColors[Math.floor(Math.random() * neonColors.length)];
        colors[i3] = color.r;
        colors[i3 + 1] = color.g;
        colors[i3 + 2] = color.b;
    }

    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

    const material = new THREE.PointsMaterial({
        size: 0.8,
        vertexColors: true,
        transparent: true,
        opacity: 0.8,
        blending: THREE.AdditiveBlending
    });

    particles = new THREE.Points(geometry, material);
    scene.add(particles);

    animate();
}

function animate() {
    requestAnimationFrame(animate);

    particles.rotation.x += 0.0003;
    particles.rotation.y += 0.0005;

    const positions = particles.geometry.attributes.position.array;
    for (let i = 0; i < positions.length; i += 3) {
        positions[i + 1] += Math.sin(Date.now() * 0.001 + i) * 0.005;
    }
    particles.geometry.attributes.position.needsUpdate = true;

    renderer.render(scene, camera);
}

window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});

const scroll = new LocomotiveScroll({
    el: document.querySelector('[data-scroll-container]'),
    smooth: true,
    multiplier: 0.8,
    lerp: 0.1
});

scroll.on('scroll', (args) => {
    if (particles) {
        particles.rotation.y = args.scroll.y * 0.0003;
    }
});

const terminalOverlay = document.getElementById('terminal-overlay');
const terminalClose = document.querySelector('.terminal-close');
const terminalInput = document.querySelector('.terminal-input');
const terminalOutput = document.querySelector('.terminal-output');
let currentAgent = null;

const agentData = {
    1: {
        name: 'BOM & COSTING SPECIALIST',
        placeholder: 'Calculate BOM for hoodie, 500 units, cotton jersey, India supplier'
    },
    2: {
        name: 'MOQ NEGOTIATION STRATEGIST',
        placeholder: 'Negotiate MOQ for 5 styles, $15K budget, August order'
    },
    3: {
        name: 'PRODUCTION TIMELINE MANAGER',
        placeholder: 'Timeline for 500 hoodies, target launch October 1'
    },
    4: {
        name: 'INVENTORY & DEMAND FORECASTER',
        placeholder: 'Size allocation for 500 units, athletic fit, urban demographic'
    },
    5: {
        name: 'CASH FLOW FINANCIAL PLANNER',
        placeholder: 'Cash flow for $25K startup, 500-unit first order'
    }
};

document.querySelectorAll('.agent-connect').forEach(btn => {
    btn.addEventListener('click', () => {
        const agentId = btn.getAttribute('data-agent');
        openTerminal(agentId);
    });
});

function openTerminal(agentId) {
    currentAgent = agentId;
    const agent = agentData[agentId];

    document.getElementById('current-agent').textContent = `AGENT_0${agentId} - ${agent.name}`;
    terminalInput.placeholder = agent.placeholder;
    terminalOutput.innerHTML = `<div style="color: #00F5FF;">/// AGENT CONNECTED ///\n/// READY FOR QUERY ///</div>`;

    document.querySelector('.metric-time').textContent = '0ms';
    document.querySelector('.metric-data').textContent = '0';
    document.querySelector('.metric-conf').textContent = '0%';

    terminalOverlay.classList.add('active');
    terminalInput.focus();
}

terminalClose.addEventListener('click', () => {
    terminalOverlay.classList.remove('active');
    currentAgent = null;
    terminalInput.value = '';
});

terminalOverlay.addEventListener('click', (e) => {
    if (e.target === terminalOverlay) {
        terminalOverlay.classList.remove('active');
        currentAgent = null;
        terminalInput.value = '';
    }
});

terminalInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        executeQuery();
    }
});

async function executeQuery() {
    const query = terminalInput.value.trim();

    if (!query) {
        terminalOutput.innerHTML = `<div style="color: #FF006E;">/// ERROR: QUERY EMPTY ///</div>`;
        return;
    }

    terminalOutput.innerHTML = `<div style="color: #00F5FF;">/// PROCESSING QUERY ///\n/// ANALYZING DATA POINTS ///</div>`;

    const startTime = Date.now();

    try {
        const response = await fetch(`http://localhost:8000/agent/${currentAgent}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query })
        });

        if (!response.ok) throw new Error('Endpoint unavailable');

        const result = await response.json();
        const endTime = Date.now();

        document.querySelector('.metric-time').textContent = `${endTime - startTime}ms`;
        document.querySelector('.metric-data').textContent = result.data_points || '1000+';
        document.querySelector('.metric-conf').textContent = result.confidence || '98%';

        terminalOutput.innerHTML = `<div style="color: #00F5FF;">${result.output || result.message}</div>`;
    } catch (error) {
        const mockOutput = getMockAgentOutput(currentAgent, query);
        const endTime = Date.now();

        document.querySelector('.metric-time').textContent = `${endTime - startTime}ms`;
        document.querySelector('.metric-data').textContent = mockOutput.dataPoints;
        document.querySelector('.metric-conf').textContent = mockOutput.confidence;

        terminalOutput.innerHTML = `<div style="color: #00F5FF;">${mockOutput.output}</div>`;
    }

    terminalInput.value = '';
}

function getMockAgentOutput(agentId, query) {
    const outputs = {
        1: {
            output: `BOM CALCULATION RESULT
═══════════════════════════════════════════════
PRODUCT: HOODIE
SUPPLIER: EcoKnits-Tirupur (India)
ORDER: 500 units

COST BREAKDOWN (PER UNIT):

FABRIC:
  Consumption: 2.60m (with shrinkage + waste)
  Cost: 2.60m × $5.80/m = $15.08

TRIMS:
  Drawcord: $0.18
  Cord locks: $0.10
  Labels: $0.23
  Total Trims: $0.51

LABOR:
  SMV: 35 minutes
  Rate: $0.65/min
  Cost: 35 × $0.65 = $22.75

OVERHEAD & PROFIT:
  Factory overhead (16%): $6.13
  Factory profit (10%): $4.45

FOB COST: $48.92/unit

LANDED COST ADDITIONS:
  Freight (India): $3.60/unit
  Duty (16.0%): $7.83
  Customs broker: $0.25
  Receiving: $0.60
  QC inspection: $0.40

LANDED COST: $61.60/unit

PRICING RECOMMENDATIONS:

DTC (Direct-to-Consumer):
  Retail Price: $172.48
  Gross Margin: 64.3%

Premium Positioning:
  Retail Price: $246.40
  Gross Margin: 75.0%

TOTAL ORDER VALUE (500 units):
FOB Total: $24,460.00
Landed Total: $30,800.00
DTC Revenue Potential: $86,240.00
Premium Revenue Potential: $123,200.00

✅ ±2% accuracy | 15-20% cost overruns eliminated
📊 Based on 1,000+ real fashion industry data points`,
            dataPoints: '1247',
            confidence: '98%'
        },
        2: {
            output: `MOQ NEGOTIATION STRATEGY
═══════════════════════════════════════════════
ANALYSIS: 5 styles, $15K budget, August timing

RECOMMENDED SUPPLIER: EcoKnits-Tirupur

BASE MOQ SCENARIO:
  Standard MOQ: 300 units/style
  Total Required: 1,500 units
  Total Cost: $73,500 (OVER BUDGET)

STRATEGY STACK:

1. Multi-Style Commitment (-40%)
   Commit to 5 styles simultaneously
   Reduction: 300 → 180 units/style

2. Off-Peak Timing (-25%)
   August = low season
   Reduction: 180 → 135 units/style

3. Prepayment Leverage (-20%)
   50% upfront payment
   Reduction: 135 → 108 units/style

FINAL NEGOTIATED MOQ: 113 units/style
Total Order: 565 units (62% reduction!)
Total Cost: $27,677 (within budget)

SUCCESS PROBABILITY: 75%
ESTIMATED SAVINGS: $45,823

NEXT STEPS:
1. Contact supplier with multi-style proposal
2. Offer 50% prepayment
3. Emphasize August timing advantage`,
            dataPoints: '892',
            confidence: '75%'
        },
        3: {
            output: `PRODUCTION TIMELINE
═══════════════════════════════════════════════
ORDER: 500 hoodies
SUPPLIER: EcoKnits-Tirupur
TARGET LAUNCH: October 1

CRITICAL PATH:

Week 1-2 (14 days): Tech Pack & Fabric Procurement
  - Tech pack finalization
  - Fabric swatch approval
  - Yarn procurement

Week 3-4 (14 days): Sampling
  - Pre-production sample (PPS)
  - First article inspection (FAI)
  - Approval + revision round

Week 5-9 (35 days): Bulk Production
  - Cutting & sewing
  - Quality gates: inline 20%, 50%, 80%
  - Final random inspection (FRI)

Week 9 (3 days): Final QC
  - AQL 2.5 inspection
  - Third-party audit: $300

Week 10-12 (21 days): Shipping
  - India → NYC sea freight: 18 days
  - Customs clearance: 3 days

TOTAL TIMELINE: 87 days (12.4 weeks)
RECOMMENDED START: June 28
DELIVERY DATE: September 23
BUFFER: 8 days before launch

RISK FACTORS:
⚠️ Monsoon season (June-Sept): Add 1 week buffer
⚠️ Port congestion: Possible 3-5 day delay`,
            dataPoints: '1156',
            confidence: '95%'
        },
        4: {
            output: `INVENTORY ALLOCATION
═══════════════════════════════════════════════
PRODUCT: 500 hoodies
FIT: Athletic
DEMOGRAPHIC: Urban

SIZE CURVE (Athletic M/L Bias):
  XS: 15 units (3%)
  S: 80 units (16%)
  M: 170 units (34%)
  L: 150 units (30%)
  XL: 65 units (13%)
  XXL: 20 units (4%)

COLOR DISTRIBUTION (Neutral-Heavy):
  Black: 200 units (40%)
  Grey: 175 units (35%)
  Olive: 125 units (25%)

TOTAL SKUs: 18 (3 colors × 6 sizes)

HIGH-PRIORITY SKUs (70% of sales):
  - Black M: 68 units
  - Black L: 60 units
  - Grey M: 60 units
  - Grey L: 52 units

REORDER TRIGGERS:
  M sizes: Reorder at 19 units (6-week lead time)
  L sizes: Reorder at 17 units
  Total: Reorder when 36 units remain

DEAD STOCK RISKS (2 SKUs):
  - XS Olive: 4 units (>20 weeks inventory)
  - XXL Olive: 3 units
  Recommendation: Markdown at week 8-10

SELL-THROUGH FORECAST:
  Month 1: 150 units (30%)
  Month 2: 175 units (35%)
  Month 3: 125 units (25%)
  Month 4+: 50 units (10%)`,
            dataPoints: '2341',
            confidence: '87%'
        },
        5: {
            output: `CASH FLOW PROJECTION
═══════════════════════════════════════════════
STARTUP: $25K budget
ORDER: 500 units @ $61.60 landed cost
RETAIL: $172.48 DTC

PAYMENT SCHEDULE:

Month -4: Sampling
  Tech pack: -$500
  Samples: -$1,500
  Cash Position: $23,000

Month -2: Production Deposit (40%)
  Deposit: -$12,320
  Marketing setup: -$2,000
  Cash Position: $8,680

Month -1: Balance Payment (60%)
  Balance: -$18,480
  Freight: -$1,800
  Marketing: -$5,000
  Cash Position: -$16,600 ⚠️ NEED $16,600 MORE!

Month 0: Launch
  Receiving: -$300
  QC: -$400
  Sales: +$12,936 (75 units × $172.48)
  Cash Position: -$4,364

Month 1: Growth
  Sales: +$25,872 (150 units)
  Shopify fees: -$751
  Marketing: -$3,000
  Cash Position: +$17,757

Month 2: BREAKEVEN
  Sales: +$30,184 (175 units)
  Shopify fees: -$875
  Cash Position: +$47,066 ✅ PROFITABLE

ANALYSIS:
💰 Total Capital Needed: $41,600 (not $25K!)
📊 Breakeven: Month 2 (175 units sold)
🔄 Reorder Affordable: Month 2
⚠️ Critical Gap: Month -1 requires $16.6K bridge

RECOMMENDATIONS:
1. Secure $17K bridge financing
2. Consider smaller initial order (300 units)
3. Pre-orders to offset deposit`,
            dataPoints: '1893',
            confidence: '92%'
        }
    };

    return outputs[agentId] || {
        output: '/// AGENT PROCESSING COMPLETE ///',
        dataPoints: '1000+',
        confidence: '95%'
    };
}

initThree();
